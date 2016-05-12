#!/usr/bin/env python2.6

# Play with RSA asym keys

import binascii
import os
from Crypto.PublicKey import RSA


rsa = RSA.generate(256, os.urandom)
rsapub = rsa.publickey()
print '%x' % rsa.n
print '%x' % rsa.e
print '%x' % rsa.d

cipher = rsapub.encrypt('Emmanuel Blot', None)
hcipher = binascii.hexlify(cipher[0])
print 'msg: %s' % hcipher
print ' '.join(hcipher[::2])

print '-' * 40

rsa2 = RSA.construct((0x899d0c1494243b9c592da272a2753cbdf1d2ee19f3c33645eee8d69d948a9145,
                      0x10001,
                      0x4d68096389f0d7971a9290cdea940795fb5b1f0b77952494d87d4a85a4b2001))

print rsa2.decrypt(binascii.unhexlify('780fa425f2820c5230e9bee753643a496b84021fd6e19e597c2dbf700c518bb3'))