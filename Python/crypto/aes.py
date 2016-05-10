#!/usr/bin/env python2.7

# Combine words to find the proper sequence order for a very specific and
# klunky undocumented piece of ... HW

from binascii import hexlify, unhexlify
from Crypto.Cipher import AES

aesKey = [0, 0, 0, 0]
aesKey[3] = ''
aesKey[2] = ''
aesKey[1] = ''
aesKey[0] = ''


def rev(s):
    return hexlify(''.join(reversed(unhexlify(s))))

passwd = 'ABCDEFGHIJKLMNO\0'


# hexkey = aesKey[3] + aesKey[2] + aesKey[1] + aesKey[0]
# hexkey = aesKey[0] + aesKey[1] + aesKey[2] + aesKey[3]
# hexkey = rev(aesKey[3]) + rev(aesKey[2]) + rev(aesKey[1]) + rev(aesKey[0])
# hexkey = rev(aesKey[0]) + rev(aesKey[1]) + rev(aesKey[2]) + rev(aesKey[3])
hexkey = aesKey[3] + aesKey[2] + aesKey[1] + aesKey[0]
hexkey = rev(hexkey)

key = unhexlify(hexkey)
aes = AES.new(key, AES.MODE_ECB)
cpasswd = aes.encrypt(passwd)
print 'key:    %s' % hexlify(key)
print 'get:    %s' % hexlify(cpasswd)
print 'expect: eb7ad95d1015c9a5826c78adf9ba995b'
