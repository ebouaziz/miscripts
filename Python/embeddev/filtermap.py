#!/usr/bin/env python

# Perform some kind of filtering from a MAP (ELF) file

from __future__ import with_statement
import re
import sys

items = []
for l in sys.stdin.readlines():
    l = l.strip('\n').strip('\r')
    mo = re.match(r'(?i)^\s*.bss\s+(0x[a-f0-9]+)\s+(0x[a-f0-9]+)\s'
                  r'.*\((.*)\)\s*$', l)
    if not mo:
        continue
    items.append((int(mo.group(1),16), int(mo.group(2),16), mo.group(3)))

items = filter(lambda x: x[1] > 0, items)
items.sort(key=lambda x: x[1])
items.reverse()
for it in items:
    print "%8d: %s" % (it[1], it[2])