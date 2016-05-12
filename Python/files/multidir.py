#!/usr/bin/env python

# Some kind of early prototype to os.walk from several dir trees

import os

def mergewalk(dirs):
    topdirnames = []
    topfilenames = []
    for td in dirs:
        for (path, dnames, fnames) in os.walk(td):
            dirnames = [(path, d) for d in dnames if not d.startswith('.')]
            filenames = [(path, d) for d in fnames if not d.startswith('.')]
            topdirnames.extend(dirnames)
            topfilenames.extend(filenames)
            dnames[:] = []
    topdirnames.sort(key=lambda x: x[1])
    topfilenames.sort(key=lambda x: x[1])
    yield(topdirnames, topfilenames)
    for td in topdirnames:
        for (path, dnames, fnames) in os.walk(os.path.join(td[0], td[1])):
            dnames[:] = [d for d in dnames if not d.startswith('.')]
            yield([(path, d) for d in sorted(dnames)],
                  [(path, f) for f in sorted(fnames)])

def run(dirs):
    for d in dirs:
        if not os.path.isdir(d):
            raise IOError('No such directory: %s' % d)
    for (dirnames, filenames) in mergewalk(dirs):
        #print "dirnames", dirnames
        for e in [(d[0],d[1]+os.sep) for d in dirnames] + filenames:
            print e

if __name__ == '__main__':
    prefix = '/Users/eblot/Sources/sdk/trunk'
    dirs = [os.path.join(prefix, 'config'),
            os.path.join(prefix, 'build/config')]
    run(dirs)