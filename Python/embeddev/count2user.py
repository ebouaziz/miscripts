#!/usr/bin/env python2.7

# Helper to count errors by author. Input stream would either be from
# Trac or SVN?

import sys
import pprint


lines = [l.rstrip('\n').split(',') for l in sys.stdin.readlines()]

# find all authors
authdict = {}
for line in lines:
    (rev, afiles, acode, acmt, ablk, atotal, author, dt) = line
    authdict[author] = 0
authors = authdict.keys()
authors.sort()

print ','.join(authors)
lcode = 0
lcmt = 0
count = 0
for line in lines:
    (rev, afiles, acode, acmt, ablk, atotal, author, dt) = line
    rev = int(rev)
    acode = int(acode)
    dcode = acode-lcode
    lcode = acode
    acmt = int(acmt)
    dcmt = acmt-lcmt
    lcmt = acmt
    authdict[author] += dcode
    count += 1
    if count == 10:
        count = 0
    print ','.join([str(authdict[auth]) for auth in authors])
