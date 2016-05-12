#!/usr/bin/env python2.7

# Compare two list of emails

import sys

with open(sys.argv[1], 'rt') as f:
	src1 = set([l.strip().lower() for l in f if '@' in l])
with open(sys.argv[2], 'rt') as f:
	src2 = set([l.strip().lower() for l in f if '@' in l])
dst = src1-src2
print "S1: %d, S2: %d, D: %d" % (len(src1),len(src2),len(dst))
with len(sys.argv) > 3 and open(sys.argv[3], 'wt') or sys.stdout as f:
	print >> f, 'email'
	for l in sorted(dst):
		print >> f, l
