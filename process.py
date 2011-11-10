#!/usr/bin/env python

import csv
import re
import sys

from calendar import monthrange
from datetime import datetime, timedelta
from urllib import urlencode
from urllib2 import urlopen
from urlparse import urljoin

DATEFMT = "%Y-%m-%d %H:%M:%S"
CLIMATEURL = "http://www.nws.noaa.gov/climate/getclimate.php?{params}"
CLIMATEQUERY = dict(
    pil="CF6",
    recent="yes",
)

CACHE = {}

def main():
    wfo, sid = sys.argv[1:3]

    out = csv.writer(sys.stdout)

    for date in sys.stdin:
        date = date.strip()
        day = getclimate(wfo, sid, date)
        row = (date, "MISSING", "MISSING")
        if day:
            row = (date, day["max"], day["avg"])
        out.writerow(row)

def getclimate(wfo, sid, date):
    year, month, day = date = parsedate(date)
    data = CACHE.get(date)
    if not data:
        data = query(wfo, sid, year, month).read()

        CACHE.update(
            ((year, month, int(day["day"])), day) for day in parse(data.splitlines())
        )
        data = CACHE.get(date)

    return data

def parsedate(date):
    month, day, year = (int(x) for x in date.split("/", 2))
    return (year, month, day)

def query(wfo, sid, year, month):
    specdate = datetime(
        year=year,
        month=month,
        day=monthrange(year, month)[1],
        hour=11, minute=11, second=11
    )

    params = urlencode(dict(
        wfo=wfo,
        sid=sid,
        specdate=specdate.strftime(DATEFMT),
        **CLIMATEQUERY
    ))
    result = urlopen(CLIMATEURL.format(params=params))
    return result

# http://www.nws.noaa.gov/climate/f6.php?wfo=gld
daypattern = re.compile(r"""
    ^\s*
    (?P<day>\d+)\s+           # day of the month
    (?P<max>[0-9-]+)\s+           # max temperature (F)
    (?P<min>[0-9-]+)\s+           # min temperature (F)
    (?P<avg>[0-9-]+)\s+           # average temperature (F)
    (?P<departure>[0-9-]+)\s+     # departure from 30-year average (F)
    (?P<heatdegree>\d+)\s+    # heating degree (abs(day's average - 65)) (F)
    (?P<cooldegree>\d+)\s+    # cooling degree (abs(day's average - 65)) (F)
    (?P<precipitation>[T.0-9]+)\s+ # all precipitation, T=trace (1/100 inch)
    (?P<snow>[.0-9]+)\s+       # total snowfall (1/10 inch)
    (?P<depth>\d+)\s+         # snow depth at 1200 UTC (inch)
    (?P<windavg>[.0-9]+)\s+   # average wind speed (mph)
    (?P<windmax>[.0-9]+)\s+   # max wind speed (two minute averages) (mph)
    (?P<winddir>\d+)\s+       # direction of max wind (compass degrees/10)
    (?P<sunshine>[0-9M]+)\s+  # sunshine (minutes)
    (?P<sunshinepct>[0-9M]+)\s+ # possible sunshine (minutes/possible minutes)
    (?P<cover>\d+)\s+         # average cloud coverage (tenths of sky)
    (?P<weather>[0-9X]+|\ )\s+   # types of observed weather (coded)
    (?P<windpeak>\d+)\s+      # peak wind speed (mph)
    (?P<windpeakdir>\d+)      # direction of peak wind (compass degrees/10)
    $
    """, re.VERBOSE)

def parse(result):
    inreport = False
    for line in result:
        if line == "000":
            inreport = True
        if not inreport:
            continue

        match = daypattern.match(line)
        if not match:
            continue
        match = match.groupdict()
        yield match

if __name__ == "__main__":
    try:
        ret = main()
    except KeyboardInterrupt:
        ret = None
    sys.exit(ret)
