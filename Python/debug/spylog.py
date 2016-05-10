#!/usr/bin/env python2.7

# Decode custom format from a log file

import sys
from struct import unpack as sunpack, calcsize as scalc

with open(sys.argv[1], "rb") as log:
    fmt = '<II'
    fmt_size = scalc(fmt)
    total_irq = 0
    total_read = 0
    ticks = 0
    period_ms = 3000
    tick_ms = 2
    start = 3000
    end = (period_ms/tick_ms)+start
    inperiod_irq = 0
    inperiod_read = 0
    with open('/Users/eblot/Desktop/output1.txt', 'wt') as out1, \
         open('/Users/eblot/Desktop/output2.txt', 'wt') as out2:
        while True:
            words = log.read(fmt_size)
            if not words:
                break
            irq_count, read_count = sunpack(fmt, words)
            total_irq += irq_count
            total_read += read_count
            ticks += 1
            if start <= ticks < end:
                inperiod_irq += irq_count
                inperiod_read += read_count
            print >> out1, '%d,%d' % (ticks, irq_count)
            print >> out2, '%d,%d' % (ticks, read_count)
    print '-' * 16
    print total_irq, ticks, 1.0/float(inperiod_irq)
    print inperiod_irq, inperiod_read, float(inperiod_read)/float(inperiod_irq)

