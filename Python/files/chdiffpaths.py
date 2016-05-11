#!/usr/bin/env python

import re
import sys

changes = {}
lchanges = []
for line in sys.stdin.xreadlines():
    in_, out_ = line.strip('\r\n').split(' ')
    lchanges.append(in_)
    changes[in_] = out_

src = open(sys.argv[1], "rt")
dst = open(sys.argv[2], "wt")

srcre = r'|'.join(['(%s)' % x for x in lchanges]).replace('.', '\\.')
print srcre
srccre = re.compile(srcre)
for line in src.xreadlines():
    line = line.strip('\r\n')
    mo = srccre.search(line)
    #print line, " -> ",
    if mo:
        match = mo.group(0)
        line = line.replace(match, changes[match])
    print >>dst, line
