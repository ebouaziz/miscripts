#!/usr/bin/env python

# Some kind of very project-specific way to remove unwanted components

from __future__ import with_statement
import os
import re
import sys
from optparse import OptionParser
from subprocess import Popen, PIPE, STDOUT

TRUE_VALUES = ['yes','ok','true']
FALSE_VALUES = ['no','none','false']


def parse(filename):
    if not filename or not os.path.isfile(filename):
        raise AssertionError("Invalid filename: %s" % filename)
    states = '|'.join(TRUE_VALUES + FALSE_VALUES)
    compcre = re.compile(r'^\s*\*\s+(n[adsl]_\w+)\s+(' + states + ')\s*$',
                         re.IGNORECASE)
    add_comp = []
    del_comp = []
    with open(filename, 'rt') as f:
        for line in f.readlines():
            mo = compcre.match(line)
            if mo:
                comp = mo.group(1)
                status = mo.group(2)
                if status in TRUE_VALUES:
                    add_comp.append(comp)
                elif status in FALSE_VALUES:
                    del_comp.append(comp)
    return (add_comp, del_comp)

def proceed(add, rem, stop_on_error=False):
    MAP = { 'na' : 'neoasl',
            'nd' : 'neodrv',
            'nl' : 'neolib',
            'ns' : 'neosys' }
    for order, info in enumerate([('sdk', ''), ('sdktests', '_test')]):
        for fn in add:
            libdir = MAP[fn.split('_')[0]]
            reldir = os.path.join(info[0], libdir, fn + info[1])
            if order == 0 and not os.path.isdir(reldir):
                err = "Missing required component '%s'" % reldir
                if stop_on_error:
                    raise AssertionError(err)
                else:
                    print >> sys.stderr, "Warning: %s" % err
        del_list = []
        for fn in rem:
            libdir = MAP[fn.split('_')[0]]
            reldir = os.path.join(info[0], libdir, fn + info[1])
            if os.path.isdir(reldir):
                del_list.append(reldir)
        if del_list:
            args = ['svn', 'rm']
            args.extend(del_list)
            child = Popen(args)
            ret = child.wait()
            if ret and stop_on_error:
                raise AssertionError('Error: SVN cannot remove files')

if __name__ == '__main__':
    try:
        usage = 'Usage: %prog [options]\n'\
                '  prepare a project branch'
        optparser = OptionParser(usage=usage)
        optparser.add_option('-i', '--input', dest='input',
                             help='input file')
        optparser.add_option('-k', '--keep-going', dest='keepgo',
                             action='store_true',
                             help='Keep going on error')
        (options, args) = optparser.parse_args(sys.argv[1:])
        
        (add, rem) = parse(options.input)
        proceed(add, rem, stop_on_error=not options.keepgo)

    except AssertionError, e:
        print >> sys.stderr, "Error: %s" % e.args[0]
        exit(-1)
