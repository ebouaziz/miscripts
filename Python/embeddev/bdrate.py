#!/usr/bin/env python

# Compute UART baudrate tolerance

TOLERANCE = 1  # %

def calc_baudrates(freq, tolerance, hostclock=0):
    basefreq = [115200*(x+1) for x in xrange(7)]
    tm = 100+tolerance
    last = 0
    for bd_ in xrange(10, 121):
        bd = 100000*bd_
        divisor = freq//bd
        actual = freq//divisor
        #delta = (100.0*abs(bd-actual))/bd
        #print bd_, bd, delta
        if actual * 2 < bd:
            # overflow
            continue
        if (actual < bd) and (actual * tm < bd * 100) \
                         or (bd * tm < actual * 100):
            # not in tolerance range
            continue
        if hostclock:
            hostdiv = hostclock//bd
            hostactual = hostclock//hostdiv
            if hostactual * 2 < bd:
                # overflow
                continue
            if (hostactual < bd) and (hostactual * tm < bd * 100) \
                             or (bd * tm < hostactual * 100):
                # not in tolerance range
                # print bd, (100.0*abs(bd-hostactual))/bd
                continue
        if (bd_%10) and abs(bd-last) < 300000:
            # to close of the previous computation, and not a 1000000 multiple
            continue
        last = bd
        #delta = (100.0*abs(bd-actual))/bd
        #print bd_, bd, delta
        basefreq += [bd]
        # WARNING ARRAY SIZE !
    return basefreq

for freq in xrange(96, 208, 12):
    freqs = calc_baudrates(freq*1000*1000, TOLERANCE, 8*3*1000*1000*4)
    print "%d: (%d) %s" % (freq, len(freqs), freqs)
