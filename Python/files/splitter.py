#!/usr/bin/env python

# Split a file on pattern criteria

from __future__ import with_statement
from optparse import OptionParser
import re
import sys


#--- Main -------------------------------------------------------------------

if __name__ == "__main__":
    usage = 'Usage: %prog [options]\n' \
            '   Split a file on pattern criteria'
    optparser = OptionParser(usage=usage)
    optparser.add_option('-p', '--pattern', dest='pattern',
                         help='Split pattern')
    optparser.add_option('-i', '--input', dest='input',
                         help='File to split')
    optparser.add_option('-o', '--output', dest='output',
                         help='File output pattern',
                         default='output-@.txt')
    optparser.add_option('-v', '--verbose', dest='verbose',
                         action='store_true', help='Verbose mode')
    (options, args) = optparser.parse_args(sys.argv[1:])

    try:
        if not options.pattern:
            raise AssertionError("No split pattern defined")
        try:
            pcre = re.compile(options.pattern)
        except Exception, e:
            raise AssertionError("Invalid RE pattern: %s" % str(e))
        count = 0
        if not '@' in options.output:
            raise AssertionError("Outfile pattern prefix should contain a "
                                 "'@' marker")
        try:
            name = options.output.replace('@', '%03d' % count)
            out_ = open(name, 'wt')
            if options.verbose:
                print >> sys.stderr, "Creating outfile %s" % name
        except IOError, e:
            raise AssertionError("Cannot create output file %s" % name)
        with options.input and open(options.input, 'rt') or sys.stdin as in_:
            lcount = 0
            for line in in_:
                lcount += 1
                if pcre.match(line):
                    if options.verbose:
                        print >> sys.stderr, "Found a %d-line segment" % lcount
                    lcount = 0
                    out_.close()
                    try:
                        count += 1
                        name = options.output.replace('@', '%03d' % count)
                        out_ = open(name, 'wt')
                        print >> sys.stderr, "Creating outfile %s" % name
                    except IOError, e:
                        raise AssertionError("Cannot create output file %s" \
                            % name)
                out_.write(line)
        try:
            out_.close()
        except Exception:
            pass
    except AssertionError, e:
        print >> sys.stderr, "Error: %s" % e
        sys.exit(1)
