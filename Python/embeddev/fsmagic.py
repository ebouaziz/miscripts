#!/usr/bin/env python

# Create a FS magic word

import struct
import binascii

values = [ord(c) for c in 'UFFS']
print '0x%s' % binascii.hexlify(struct.pack('<BBBB', *values))
