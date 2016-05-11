#!/usr/bin/env python2.7

# Show page files from a *25 data flash device

GEN25_PAGE_DIV = 8
GEN25_PAGE_SIZE = (1 << GEN25_PAGE_DIV)

def write(address, length):
    print 'start 0x%04x 0x%x' % (address, length)
    rem = length
    pos = 0
    while pos<length:
        start = address+pos
        count = min(rem, GEN25_PAGE_SIZE)
        if start & (GEN25_PAGE_SIZE-1):
            up = (start+(GEN25_PAGE_SIZE-1))&~(GEN25_PAGE_SIZE-1)
            count = min(count, up-start)
        end = start+count
        print "0x%x..0x%x %d" % (start, end, count)
        pos += count
        rem -= count

length = 0
count = 516
address = 0
while length < 0x10000:
    write(address, count)
    address += count
    length += count
