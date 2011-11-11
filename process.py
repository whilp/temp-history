#!/usr/bin/env python

import csv
import sys

from functools import partial
from tempfile import NamedTemporaryFile

import lxml.html

tempfile = partial(NamedTemporaryFile, dir=".", prefix="result-", delete=False)
CLIMATEURL = "http://www.wunderground.com/history/airport/{airport}/{year}/{month}/{day}/DailyHistory.html"

def main():
    airport = sys.argv[1]
    dates = sys.argv[2:]

    with tempfile() as outfile:
        out = csv.writer(outfile)

        for date in dates:
            id, date = date.split(",", 1)
            year, month, day = parsedate(date.strip())
            result = getclimate(airport, year, month, day)
            row = (id, date, "MISSING", "MISSING")
            if result:
                row = (id, date,
                    result["temperature.max.actual"],
                    result["temperature.mean.actual"]
                )
            out.writerow(row)
    sys.stdout.write("{0}\n".format(outfile.name))

def parsedate(date):
    month, day, year = (int(x) for x in date.split("/", 2))
    return (year, month, day)

def getclimate(airport, year, month, day):
    url = CLIMATEURL.format(
        airport=airport,
        year=year,
        month=month,
        day=day)
    return dict(parse(url))

keys = {
    "Mean Temperature": "temperature.mean",
    "Max Temperature": "temperature.max",
    "Min Temperature": "temperature.min",
}

def parse(url):
    data = lxml.html.parse(url)
    for cell in data.xpath('//table[@id="historyTable"]//td'):
        text = cell.findtext("span")
        key = keys.get(text)
        if key is None:
            continue
        fields = [float(x) for x in cell.getparent().xpath("td/span/span/text()")]
        fields.append("MISSING")
        for k, v in zip(("actual", "average", "record"), fields):
            yield "{key}.{heading}".format(key=key, heading=k), v

if __name__ == "__main__":
    try:
        ret = main()
    except KeyboardInterrupt:
        ret = None
    sys.exit(ret)
