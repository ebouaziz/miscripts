#!/usr/bin/env python3


def show_bits(bits):
    for c in bits:
        print('  %s' % ''.join([str(b) for b in c]))
    print('')


def show_dots(bits):
    # dot = chr(0x2589)
    dot = '*'
    for c in bits:
        print('  %s .' % ''.join([b and dot or ' ' for b in c]))
    print('')


pts = [0x00,0x0E,0x02,0x0E,0x02,0x02,0x00,0x00]
bpts = [[int(b) for b in '{0:08b}'.format(c)] for c in pts]
rbpts = list(reversed(zip(*bpts[::-1])))

show_dots(bpts)
show_dots(rbpts)

# print(rbpts)
print(pts)
bytes_ = [int(''.join([str(b) for b in t]), 2) for t in rbpts]
print(bytes_)
