#!/usr/bin/env python

import re
import sys

# Cnv definition
convlist = ('UpperCnv', 'LowerCnv')

# Create the cnv map
convmap = dict()
for (i, v) in enumerate(convlist):
    convmap[v] = str(i)

# RE stuff
timere = r'\d{2}:\d{2}:\d{2}:\d{3}'
cnvre = r'(?P<cnv>%s)' % r'|'.join(convlist)
hexare = r'(?P<hex>0x[0-9a-f]+)'
valre = r'(?P<val>\d)'
linere = r'\s'.join((timere, cnvre, r'-', r'\w+', hexare, r'\w+', valre))
cre = re.compile(linere)

# UT: read from stdin
lines = sys.stdin.readlines()

# execute the RE engine on the input text
output = cre.sub(lambda mo: ', '.join((convmap[mo.group('cnv')], \
                                    mo.group('hex'), mo.group('val'))), 
        ''.join(lines))

# UT: print the result
print output