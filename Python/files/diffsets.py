#!/usr/bin/env python3

# Show only different lines between two files

import sys


with open(sys.argv[1], 'rt') as fp:
    a = set([l.strip() for l in fp])

with open(sys.argv[2], 'rt') as fp:
    b = set([l.strip() for l in fp])

with open(sys.argv[3], 'wt') as fp:
    for d in sorted(a-b):
        print(d, file=fp)
