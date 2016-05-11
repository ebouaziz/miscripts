#!/usr/bin/env python2.7

# Compute clock value using binary shifts and multiply call instead of a
# constant divisor

CLOCKS = range(6, 250, 6)

for clock in CLOCKS:
    pll_ref = (clock*4)//12
    pll_opt = (clock*0xAAAAAB)>>25
    print "%uMHz: %u / %u" % (clock, pll_ref, pll_opt)
    if pll_ref != pll_opt:
        print "Invalid opt for clock %u: %u / %u" % (clock, pll_ref, pll_opt)
        break
