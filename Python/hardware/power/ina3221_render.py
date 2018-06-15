#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from sys import argv

def render(csv):
    with open(csv, 'rt') as dfp:
        times = []
        currents = []
        volts = []
        for line in dfp:
            values = line.strip().split(',')
            times.append(float(values[0]))
            currents.append(float(values[1]))
            volts.append(float(values[2])/1000)
    min_current = min(currents)
    max_current = max(currents)
    max_volt = max(volts)
    max_time = max(times)

    fig = plt.figure()
    pnode = fig.add_subplot(111)
    pnode.set_yscale('log')

    par1 = pnode.twinx()

    pnode.set_xlim(0, max_time)
    pnode.set_ylim(0.9*min_current, 1.2*max_current)
    par1.set_ylim(0, 1.2*max_volt)

    pnode.set_xlabel("Time (s)")
    pnode.set_ylabel("Current (mA)")
    par1.set_ylabel("Volt (V)")

    color1 = plt.cm.viridis(0.2)
    color2 = plt.cm.viridis(0.7)

    p1, = pnode.plot(times, currents, color=color1,label="Current (mA)")
    p2, = par1.plot(times, volts, color=color2, label="Volt (V)")

    lns = [p1, p2]
    pnode.legend(handles=lns, loc='best')

    # right, left, top, bottom
    # par2.spines['right'].set_position(('outward', 60))
    # no x-ticks
    # par2.xaxis.set_ticks([])
    # Sometimes handy, same for xaxis
    #par2.yaxis.set_ticks_position('right')

    pnode.yaxis.label.set_color(p1.get_color())
    par1.yaxis.label.set_color(p2.get_color())

    # plt.savefig("pyplot_multiple_y-axis.png", bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    render(argv[1])
