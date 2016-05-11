#!/usr/bin/env python2.7

import os
import sys
from collections import defaultdict
from hashlib import sha1
from optparse import OptionParser


class TreeMatcher(object):
    """Locate and report identical files from two directory trees.

       A tree can be a sub-tree of the other.
    """

    def __init__(self, exts=[], stop_on_error=False, verbose=False):
        self._exts = [x.lstrip('.') for x in exts]
        self._stop_on_error = stop_on_error
        self._verbose = verbose
        self._digests = ({}, {})
        self._paths = (None, None)

    def scan(self, root, nolink, discard):
        if self._verbose:
            print "Scan %s" % root
        digests = defaultdict(list)
        rules = [lambda p, d: not d.startswith('.'),
                 lambda p, d: discard != os.path.join(p, d),
                 lambda p, d: not nolink or
                              not os.path.islink(os.path.join(p, d))]
        for (dirpath, dirnames, filenames) in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if all([r(dirpath, d) for r in rules])]
            for fn in filenames:
                if self._exts:
                    name, ext = os.path.splitext(fn)
                    if ext[1:] not in self._exts:
                        continue
                pn = os.path.join(dirpath, fn)
                try:
                    with open(pn, 'rb') as fp:
                        hmd = sha1(fp.read()).hexdigest()
                except IOError:
                    if self._stop_on_error:
                        if self._verbose:
                            print ""
                        raise
                    continue
                rn = pn[len(root)+1:]
                digests[hmd].append(rn)
                if self._verbose:
                    print "\r%s %d files" % (root, len(digests)),
        if self._verbose:
            print ""
        return digests

    def scanall(self, dir1, dir2, nolink):
        ad1 = os.path.abspath(dir1)
        ad2 = os.path.abspath(dir2)
        discard1 = self._discard_nested(ad1, ad2)
        discard2 = self._discard_nested(ad2, ad1)
        d1 = self.scan(ad1, nolink, discard1)
        d2 = self.scan(ad2, nolink, discard2)
        self._digests = (d1, d2)
        self._paths = (ad1, ad2)

    @classmethod
    def _discard_nested(cls, p1, p2):
        relpath = os.path.relpath(p2, p1)
        if not relpath.startswith(''.join((os.pardir, os.sep))):
            return p2
        return None

    def show_match(self, script_mode=False, relative_mode=False):
        d1, d2 = self._digests
        if not d1:
            print "No file found"
            return
        m = set(d1) & set(d2)
        if not script_mode:
            l1 = max([len(d1[x][0]) for x in m])
            l2 = max([max([len(s) for s in d2[x]]) for x in m])
            fmttpl = "%%(dst)-%(ldst)ds <-- %%(src)-%(ldst)ds"
            fmt = fmttpl % {'lsrc': l1, 'ldst': l2}
            for h in sorted(m, key=lambda x: sorted(d2[x])[0]):
                if len(d1[h]) == 1:
                    s1 = d1[h][0]
                else:
                    s1 = "%s (%d)" % (d1[h][0], len(d1[h]))
                print fmt % {'src': s1, 'dst': d2[h][0]}
                for s2 in d2[h][1:]:
                    print s2
        else:
            fmt = "%(src)s %(dst)s"
            for h in sorted(m, key=lambda x: sorted(d2[x])[0]):
                for dst in d2[h]:
                    src = d1[h][0]
                    if relative_mode:
                        p1, p2 = self._paths
                        src = os.path.abspath(os.path.join(p1, src))
                        tmp = os.path.abspath(os.path.join(p2, dst))
                        src = os.path.relpath(src, os.path.dirname(tmp))
                    print fmt % {'src': src, 'dst': dst}

    def show_unmatch(self, prefix, pos):
        if pos:
            d1, d2 = self._digests
        else:
            d2, d1 = self._digests
        m = set(d2) - set(d1)
        for h in sorted(m, key=lambda x: d2[x]):
            print "%s" % os.path.relpath(os.path.join(prefix, d2[h][0]))


def main():
    # Use example to replace duplicate header files with symlinks:
    # matchtrees.py -l -x "h" -s -r . sysroot/usr/include | \
    #    while read a b; do rm sysroot/usr/include/$b &&
    #      ln -s $a sysroot/usr/include/$b; done

    try:
        debug = False
        usage = 'Usage: %prog [options] <src> <dst>\n'\
                '  Track and match files between two directory structures'
        optparser = OptionParser(usage=usage)
        optparser.add_option('-x', '--extension', dest='exts',
                             action='append', default=[],
                             help='Extension filter, may be repeated')
        optparser.add_option('-u', '--unmatch', dest='unmatch',
                             action='count',
                             help='Show unmatch')
        optparser.add_option('-l', '--nolink', dest='nolink',
                             action='store_true',
                             help='Do not descent in symlinked dirs')
        optparser.add_option('-a', '--abort', dest='abort',
                             action='store_true',
                             help='Abort on error')
        optparser.add_option('-s', '--script', dest='script',
                             action='store_true',
                             help='Make the output script-friendly')
        optparser.add_option('-r', '--relative', dest='relative',
                             action='store_true',
                             help='Use relative paths for output')
        optparser.add_option('-v', '--verbose', dest='verbose',
                             action='store_true',
                             help='Show progress')
        optparser.add_option('-d', '--debug', dest='debug',
                             action='store_true',
                             help='Show debug information')
        (options, args) = optparser.parse_args(sys.argv[1:])
        debug = options.debug
        if len(args) < 2:
            optparser.error('Missing tree directory')
        tm = TreeMatcher(exts=options.exts, stop_on_error=options.abort,
                         verbose=options.verbose)
        tm.scanall(args[0], args[1], options.nolink)
        if options.unmatch:
            tm.show_unmatch(args[0], 0)
            if options.unmatch > 1:
                tm.show_unmatch(args[1], 1)
        else:
            tm.show_match(options.script, options.relative)
    except (IOError, ), e:
        if debug:
            import traceback
            traceback.print_exc()
        else:
            print >> sys.stderr, 'Error:', str(e) or 'Internal error, use -d'
        sys.exit(1)


if __name__ == '__main__':
    main()
