#!/usr/bin/env python2.7

# Poor man diffstat :-)

import sys
import re

lcre = re.compile(r'^(.*)\s+\|\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)')
insertions = deletions = modifications = files = 0
for line in sys.stdin.readlines():
    line = line.strip('\n').strip('\r')
    mo = lcre.match(line)
    if mo:
        (file_, insertion, deletion, modification, _) = mo.groups()
        insertions += int(insertion)
        deletions += int(deletion)
        modifications += int(modification)
        files += 1
print "%u files, %u added lines, %u removed lines, %u modified lines" % \
    (files, insertions, deletions, modifications)