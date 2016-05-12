#!/usr/bin/env python

# Show position of non-ASCII chars in input stream

import sys

for (pos, line) in enumerate(sys.stdin.readlines()):
    if [c for c in line if ord(c) > 0x7f]:
        print "%d: %s" % (pos, line)
