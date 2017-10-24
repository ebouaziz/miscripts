#!/usr/bin/env python3

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, datetime as dt
from os import getenv
from os.path import join as joinpath


def main():
    tsa = list()
    cla = list()
    with open(joinpath(getenv('HOME'), 'Downloads', 'ip.txt'), 'rt') as fp:
        for line in fp:
            ts_str, cl_str = line.strip().split(',')
            ts = float(ts_str)
            cl = int(cl_str)
            tsa.append(dt.fromtimestamp(ts))
            cla.append(cl)
    fig, ax = plt.subplots(figsize=(20, 4))
    datefmt = mdates.DateFormatter('%a %Hh')
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_minor_locator(mdates.HourLocator())
    ax.xaxis.set_major_formatter(datefmt)
    datemin = tsa[0]
    datemax = tsa[-1]
    ax.set_xlim(datemin, datemax)
    ax.yaxis.grid(True)
    ax.plot(tsa, cla)
    fig.autofmt_xdate()
    fig.savefig("clients.png")


if __name__ == '__main__':
    main()
