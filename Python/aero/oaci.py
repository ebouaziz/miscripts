#!/usr/bin/env python2.7
# -*- coding: utf8 -*-
"""Filter out OACI areas depending on geographic position"""

from math import isnan
from optparse import OptionParser
from xml.etree import ElementTree as ET
from pprint import pprint
import sys
import time

parser = ET.XMLTreeBuilder()
prefix = 'http://earth.google.com/kml/2.2'

def PF(s):
    return '{%s}%s' % (prefix, s)

def m2f(m):
    return float(m)/0.3048

def f2m(m):
    return float(m)*0.3048

def parse(filename):
    print >> sys.stderr, "Parsing..."
    with filename and open(filename, 'rt') or sys.stdin as f:
        et = ET.parse(f)
    return et

def generate(filename, et):
    print >> sys.stderr, "Generating..."
    try:
        ET.register_namespace('', prefix)
    except AttributeError:
        print >> sys.stderr, "Invalid namespace in output"
    with filename and open(filename, 'wt') or sys.stdout as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(ET.tostring(et.getroot(), encoding='utf-8'))
        f.write('\n')

def iterator(e, tag):
    # Python < 2.7 wrapper
    try:
        return e.iter(tag)
    except AttributeError:
        return e.getiterator(tag)

def first(e, tag):
    # Python < 2.7 wrapper
    try:
        return next(e.iter(tag))
    except AttributeError:
        return e.getiterator(tag)[0]

def filtertree(et, kwargs):
    verbose = kwargs['verbose']
    folders = ('classes', 'zones')
    print >> sys.stderr, "Filtering %s..." % ' & '.join(folders)
    filters = {}
    for f in folders:
        filters[f] = kwargs[f].lower().split(',')
    for e in iterator(et, PF('Folder')):
        name = first(e, PF('name')).text
        cats = name.lower().split(' ',1)
        if len(cats) < 2:
            continue
        type_, value = cats
        if value in filters[type_]:
            if verbose:
                print >> sys.stderr, "Discarding %s %s" % \
                    (type_.title(), value.upper())
            e.clear()
            e.tag = None
    print >> sys.stderr, "Filtering regions..."
    tvalues = 'nmin nmax lmin lmax emin emax'.split()
    tnmin, tnmax, tlmin, tlmax, temin, temax = \
        [not isnan(kwargs[x]) for x in tvalues]
    nmin, nmax, lmin, lmax, emin, emax = [kwargs[x] for x in tvalues]
    # 1% safety factor
    emin /= 1.01
    emax *= 1.01
    if not kwargs['meter']:
        emin = f2m(emin)
        emax = f2m(emax)
    for e in iterator(et, PF('Placemark')):
        mg = first(e, PF('MultiGeometry'))
        name = first(e, PF('name')).text
        name = name.encode('ascii', 'replace')
        xl,yl,zl = [],[],[]
        for polygon in iterator(mg, PF('Polygon')):
            coord = first(polygon, PF('coordinates')).text
            for point in coord.strip().split(' '):
                try:
                    (x,y,z) = [float(f) for f in point.split(',')]
                    [l.append(v) for l,v in zip((xl,yl,zl),(x,y,z))]
                except ValueError, e:
                    print >> sys.stderr, "Invalid point '%s'" % point
                    raise
        discard = False
        if tnmin and max(xl) < nmin:
            discard = True
            if verbose > 1:
                print >> sys.stderr, "Discard longitude min", max(xl), name
        if tnmax and min(xl) > nmax:
            discard = True
            if verbose > 1:
                print >> sys.stderr, "Discard longitude max", min(xl), name
        if tlmin and max(yl) < lmin:
            discard = True
            if verbose > 1:
                print >> sys.stderr, "Discard latitude min", max(yl), name
        if tlmax and min(yl) > lmax:
            discard = True
            if verbose > 1:
                print >> sys.stderr, "Discard latitude max", min(yl), name
        if temin and max(zl) < emin:
            discard = True
            if verbose > 1:
                print >> sys.stderr, "Discard elevation min", max(zl), name
        if temax and min(zl) > emax:
            discard = True
            if verbose > 1:
                print >> sys.stderr, "Discard elevation max", min(zl), name
        if discard:
            if verbose == 1:
                print >> sys.stderr, "Discard", name
            e.clear()
            e.tag = None
    for e in iterator(et, PF('Document')):
        desc = first(e, PF('description'))
        addendum = u'filtrées le %s' % time.strftime("%d/%m/%Y")
        udesc = desc.text
        newdesc = u', '.join((udesc, addendum))
        desc.text = newdesc

if __name__ == '__main__':
    usage = 'Usage: %prog [options]\n'\
            '  Filter an OACI KML file'
    optparser = OptionParser(usage=usage)
    optparser.add_option('-l', '--lmin', dest='lmin', type='float',
                         help='Minimum latitude', default='Nan')
    optparser.add_option('-L', '--lmax', dest='lmax', type='float',
                         help='Maximum latitude', default='Nan')
    optparser.add_option('-n', '--nmin', dest='nmin', type='float',
                         help='Minimum longitude', default='Nan')
    optparser.add_option('-N', '--nmax', dest='nmax', type='float',
                         help='Maximum longitude', default='Nan')
    optparser.add_option('-e', '--emin', dest='emin', type='float',
                         help='Minimum elevation', default='0.0')
    optparser.add_option('-E', '--emax', dest='emax', type='float',
                         help='Maximum elevation', default='19500.0')
    optparser.add_option('-m', '--meter', dest='meter', action='store_true',
                         help='Elevation in meters (default: feet)')
    optparser.add_option('-c', '--class', dest='classes', default='',
                         help='Discard comma-separated class spaces')
    optparser.add_option('-z', '--zone', dest='zones', default='',
                         help='Discard comma-separated zones')
    optparser.add_option('-v', '--verbose', dest='verbose', action='count',
                         help='Increase verbosity, may be repeated')
    optparser.add_option('-i', '--input', dest='input',
                         help='Input file')
    optparser.add_option('-o', '--output', dest='output',
                         help='Output file (default: stdout)')
    #optparser.add_option('-x', '--kmz', dest='zip', action='store_true',
    #                     help='Output file in KMZ format')

    try:
        (options, args) = optparser.parse_args(sys.argv[1:])
        et = parse(options.input)
        filtertree(et, dict(options.__dict__))
        generate(options.output, et)
    except AssertionError, e:
        print >> sys.stderr, str(e)
        sys.exit(1)
