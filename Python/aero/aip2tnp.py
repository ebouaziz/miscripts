#!/usr/bin/env python3

# Some kind of AIP data analyser?

import re
import sys

COORD_RE = r"(\d+)°(\d+)'(\d+)(?:\.\d+)?''\s?([NS])[,\-]" \
           r"(\d+)°(\d+)'(\d+)(?:\.\d+)?''\s?([WE])\s*"
COORD_CRE = re.compile(COORD_RE)


def build(mo, *args):
    return ''.join([mo.group(x) for x in args])


def altitude(s):
    alts = [x.strip() for x in s.split('/')]
    def replace(x):
        x = x.replace('SFC', '0 ft')
        x = x.replace('FT AMSL', ' ft')
        return x
    alts = [replace(a) for a in alts]
    return alts


def emit(title, type_, base, tops, points):
    lines = []
    lines.append("INCLUDE=YES")
    lines.append("TITLE=%s" % title)
    lines.append("TYPE=%s" % type_.upper())
    lines.append("BASE=%s" % base)
    lines.append("TOPS=%s" % tops)
    lines.extend(points)
    lines.append("")
    print ('\n'.join([l.strip() for l in lines]))


def main(fp, prefix=None):
    name = ''
    points = []
    state = ''
    for l in fp:
        l = l.strip()
        if not l:
            name = ''
            points = []
            state = ''
            continue
        if state == '':
            name = prefix and "%s %s" % (prefix, l) or l
            state = 'N'
            continue
        if state == 'N':
            state = 'P'        
            for ptmo in COORD_CRE.finditer(l):
                lat = build(ptmo, 4, 1, 2, 3)
                lon = build(ptmo, 8, 5, 6, 7)
                points.append("POINT=%s %s" % (lat, lon))
            else:
                state = 'A'
                continue
        if state == 'A':
            if not points:
                raise ValueError('Unable to find points')
            base, tops = altitude(l)
            emit(name, 'RESTRICTED', base, tops, points)
            state = ''
    print("END\n")


if __name__ == '__main__':
    prefix = len(sys.argv) > 1 and sys.argv[1]
    main(sys.stdin, prefix)
