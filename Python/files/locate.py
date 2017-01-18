#!/usr/bin/env python3

"""Locate files by name in a directory tree
"""

from argparse import ArgumentParser, FileType
from collections import defaultdict
from os import walk
from os.path import basename, join as joinpath, normpath
from sys import exit, modules, stderr, stdin, stdout
from traceback import format_exc


def build_file_list(infp):
    files = set()
    for line in infp:
        line = line.strip()
        files.add(basename(line))
    return files


def scan_dirs(dirs):
    files = defaultdict(set)
    for dir_ in sorted(set([normpath(dir_) for dir_ in dirs])):
        for dirpath, dirnames, filenames in walk(dir_):
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            for f in filenames:
                if f.endswith('.c'):
                    files[f].add(normpath(dirpath))
    return files


def reduce(filesdb, files, maxcount, verbose):
    error_count = 0
    match_files = set()
    for f in files:
        if verbose:
            print('%s:' % f)
        if f in filesdb:
            candidates = filesdb[f]
            if len(candidates) > maxcount:
                error_count += 1
                if verbose:
                    print('  TOO MANY CANDIDATES')
            else:
                for candidate in candidates:
                    filepath = joinpath(candidate, f)
                    match_files.add(filepath)
                    if verbose:
                        print('  %s' % filepath)
            continue
        error_count += 1
        if verbose:
            print('  MISSING FILE')
    if not verbose:
        for f in sorted(match_files):
            print(f)
    if error_count:
        print('%d missing files' % error_count, file=stderr)


def main():
    """Main routine"""
    debug = False
    try:
        argparser = ArgumentParser(description=modules[__name__].__doc__)
        argparser.add_argument('-i', '--input', type=FileType('rt'),
                               default=stdin,
                               help='use input file instead of stdin')
        argparser.add_argument('-m', '--max', type=int, default=4,
                               help='discard report with that many candidates')
        argparser.add_argument('-l', '--list', action='store_true',
                               help='only report matching files')
        argparser.add_argument('dir', nargs='+',
                               help='directory tree to search')
        argparser.add_argument('-v', '--verbose', action='count',
                               help='increase verbosity')
        argparser.add_argument('-d', '--debug', action='store_true',
                               help='enable debug mode')
        args = argparser.parse_args()
        debug = args.debug
        from pprint import pprint
        filesdb = scan_dirs(args.dir)
        # pprint(filesdb)
        seekfiles = build_file_list(args.input)
        reduce(filesdb, seekfiles, args.max, not args.list)
    except Exception as e:
        print('\nError: %s' % e, file=stderr)
        if debug:
            print(format_exc(chain=False), file=stderr)
        exit(1)
    except KeyboardInterrupt:
        exit(2)


if __name__ == '__main__':
    main()
