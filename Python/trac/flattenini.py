#!/usr/bin/env python3

"""Flatten a trac.ini hierarchy into a single file
"""

import os
from sys import modules, stderr
from argparse import ArgumentParser
from collections import OrderedDict, defaultdict
from configparser import ConfigParser


def run(infile, outfile, debug=False):
    dicts = []
    inifile = infile
    while True:
        sections = ini2dict(inifile, debug)
        dicts.append(sections)
        inherit = sections.get('inherit', {}).get('file', '').strip()
        if not inherit:
            break
        if os.path.isabs(inherit):
            inifile = inherit
        else:
            inifile = os.path.normpath(os.path.join(os.path.dirname(inifile),
                                                    inherit))
        if debug:
            print(inherit, '->', inifile)
    merge = defaultdict(dict)
    while dicts:
        sections = dicts.pop()
        for sectname in sections:
            section = sections[sectname]
            if sectname == 'inherit':
                if 'file' in section:
                    del section['file']
            merge[sectname].update(section)
    omerge = OrderedDict()
    for sectname in sorted(merge):
        osection = omerge[sectname] = OrderedDict()
        section = merge[sectname]
        for kname in sorted(section):
            osection[kname] = section[kname]
    dict2ini(outfile, omerge)


def ini2dict(inifile, debug):
    cp = ConfigParser(strict=False)
    sections = dict()
    if debug:
        print('Parsing %s' % inifile)
    with open(inifile, 'rt') as inifp:
        cp.read_file(inifp)
    for sectname in cp:
        if sectname == 'DEFAULT':
            continue
        sect = cp[sectname]
        section = sections[sectname] = dict()
        # print('[%s]' % sectname)
        for k in sect:
            value = sect[k]
            section[k] = value
            # print('%s = %s' % (k, value))
        # print('')
    return sections


def dict2ini(inifile, sections):
    cp = ConfigParser(strict=True)
    cp.read_dict(sections)
    with open(inifile, 'wt') as inifp:
        cp.write(inifp)


def main():
    try:
        debug = False
        argp = ArgumentParser(description=modules[__name__].__doc__)
        argp.add_argument('input', nargs=1,
                          help='Trac ini file to parse')
        argp.add_argument('output', nargs=1,
                          help='Trac ini file to generate')
        argp.add_argument('-d', '--debug', action='store_true',
                          help='Show debug information')
        args = argp.parse_args()
        debug = bool(args.debug)

        infile = args.input[0]
        outfile = args.output[0]
        run(infile, outfile, debug)

    except Exception as e:
        if debug:
            import traceback
            traceback.print_exc()
        else:
            print('Error:', str(e) or 'Internal error, use -d',
                  file=stderr)
        exit(1)

if __name__ == '__main__':
    main()
