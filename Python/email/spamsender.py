#!/usr/bin/env python

# Seems to extract email addresses from junk (Python email module would be
# a better idea than raw parsing...)

import os
import sys

def main(topdir):
    for dirpath, dirnames, filenames in os.walk(topdir):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        filenames[:] = [f for f in filenames if f.endswith('.emlx')]
        for f in filenames:
            filename = os.path.join(dirpath, f)
            with open(filename, 'rt') as mail:
                for line in mail:
                    if line.startswith('From:'):
                        line = line.strip('\r\n')
                        if '<' in line:
                            s = line.index('<')+1
                            e = line[s:].index('>')
                            sender = line[s:s+e]
                        else:
                            sender = line
                        print sender
                        break

if __name__ == '__main__':
    junk = '~/Junk.mbox/'
    main(os.path.join(os.environ.get('HOME'), junk))

