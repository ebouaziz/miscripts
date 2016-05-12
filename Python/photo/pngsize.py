#!/usr/bin/env python2.7

# Extract image dimension from a PNG file - w/o a third party lib

# http://www.libpng.org/pub/png/spec/1.2/png-1.2-pdg.html

import binascii

def parse(filename):
    with open(filename, 'rb') as png:
        data = png.read(8)
        print ''.join([0x20 < ord(x) < 0x7f and x or '.' for x in data])
        print data.decode('latin1')
        print binascii.hexlify(data)
        while True:
            # Length 32 bits
            # Type   32 bits
            # Data   ..
            # CRC    32 bits
            length_bytes = png.read(4)
            if not length_bytes:
                break
            length = (ord(length_bytes[0])<<24) + \
                     (ord(length_bytes[1])<<16) + \
                     (ord(length_bytes[2])<<8) + \
                     (ord(length_bytes[3]))
            type_bytes = png.read(4)
            chunk_bytes = png.read(length)
            crc_bytes = png.read(4)
            print type_bytes
            if type_bytes == 'IHDR':
                import struct
                width, heigth = struct.unpack('>II', chunk_bytes[:8])
                print width, heigth

            # Width:              4 bytes
            # Height:             4 bytes
            # Bit depth:          1 byte
            # Color type:         1 byte
            # Compression method: 1 byte
            # Filter method:      1 byte
            # Interlace method:   1 byte

if __name__ == '__main__':
    parse('~/png.png')