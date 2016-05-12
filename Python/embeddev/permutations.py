#!/usr/bin/env python2.7

# Permutations of bits to figure out the proper bit order from a fully
# undocumented SoC implementation whose name if being kept secret :-)

from array import array
from binascii import unhexlify
from neo.bits import BitSequence
from neo.util import crc16

def l2a(l):
    return array('B', l)
def flatten(l):
    return [item for sublist in l for item in sublist]
def wordendian(l):
    # 32-bit little-endian permutation
    words = [l[n:n+4:1] for n in range(0,16, 4)]
    return flatten([reversed(w) for w in words])
def reverse(l):
    return list(reversed(l))
def niot(l):
    return l + [0, 0]
def niotcrc(l):
    POLYNOMIAL = 0x1021
    crc = 0xffff
    for x in l + [0, 0]:
        j = 0x80
        while j:
            f = crc & 0x8000
            crc <<= 1
            if x & j:
                crc |= 1
            if f:
                crc ^= POLYNOMIAL
            j >>= 1
        crc &= 0xffff
    return crc
def show(m,l):
    print "%-24s:" % m, ' '.join(["%02x" % x for x in l]), "= %04x" % niotcrc(l)


seq = range(16)
wseq = wordendian(seq)
rseq = reverse(seq)
rwseq = reverse(wseq)
bseq = [BitSequence(i, msb=True, length=8).tobyte() for i in seq]
bwseq = wordendian(bseq)
brseq = reverse(bseq)
bwrseq = reverse(bwseq)
show('natural', seq)
show('endian', wseq)
show('reverse', rseq)
show('reverse+endian', rwseq)
show('bitrev', bseq)
show('bitrev+endian', bwseq)
show('bitrev+reverse', brseq)
show('bitrev+endian+reverse', bwrseq)