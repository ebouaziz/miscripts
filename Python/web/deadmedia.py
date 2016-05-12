#!/usr/bin/env python2.7

# Find media files that are no longer referenced within a Joomla DB

import os
import re
import sys
import sqlite3
from optparse import OptionParser
from urllib import unquote
from urlparse import urlparse


def find_media_files(rootdir, subpath, exts):
    media_files = set()
    topdir = os.path.join(rootdir, subpath.lstrip(os.sep))
    if not os.path.isdir(topdir):
        raise AssertionError('Invalid top directory \'%s\'' % topdir)
    for (dirpath, dirnames, filenames) in os.walk(topdir):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for fn in [f for f in filenames if os.path.splitext(f)[1].lower() in exts]:
            abspath = os.path.join(dirpath, fn)
            common = os.path.commonprefix((abspath, rootdir))
            relpath = abspath[len(common):]
            media_files.add(relpath)
    return media_files

def find_media_urls(sqlfile, exts, www, path):
    con = sqlite3.connect(sqlfile)
    c = con.cursor()
    c.execute('SELECT url, is_page FROM links WHERE is_internal=1')
    media_paths = set()
    prefix = '/'.join((www.rstrip('/'), path.lstrip('/')))
    while True:
        row = c.fetchone()
        if not row:
            break
        url = row[0].encode('utf-8')
        up = urlparse(url)
        urlpath = unquote(up.path)
        radix_url = '%s://%s%s' % (up.scheme, up.netloc, urlpath)
        if not radix_url.startswith(prefix):
            continue
        ext = os.path.splitext(up.path)[1].lower()
        if ext in exts:
            media_paths.add(urlpath)
    return media_paths

def main():
    default_www = 'http://www.host.com'
    default_root = '/www'
    default_path = '/images/stories'
    exts = ['.jpg', '.gif', '.png', '.pdf', '.doc', '.xls', '.swf']
    try:
        debug = False
        usage = 'Usage: %prog [options] <sqldb> <wwwpath>\n'\
                '  Find media files that are no longer referenced'
        optparser = OptionParser(usage=usage)
        optparser.add_option('-i', '--input', dest='elf',
                             help='input file')
        optparser.add_option('-w', '--www', dest='www',
                             default=default_www,
                             help='Web site (default: %s)' % default_www)
        optparser.add_option('-r', '--root', dest='root',
                             default=default_root,
                             help='Root dir (default: %s)' % default_root)
        optparser.add_option('-p', '--path', dest='path',
                             default=default_path,
                             help='Root path (default: %s)' % default_path)
        optparser.add_option('-d', '--debug', dest='debug',
                             action='store_true',
                             help='Show debug information')
        (options, args) = optparser.parse_args(sys.argv[1:])

        debug = options.debug
        if len(sys.argv) != 3:
            optparser.error('Missing arguments')
        sql, path = sys.argv[1:3]
        if not os.path.isfile(sql):
            raise AssertionError('SQLite DB does not exist')
        if not os.path.isdir(path):
            raise AssertionError('Invalid top directory')
        topdir = os.path.join(path, options.root.lstrip(os.sep))
        if not os.path.isdir(topdir):
            raise AssertionError('Invalid root path \'%s\'' % topdir)
        files = find_media_files(topdir, options.path, exts)
        urlpaths = find_media_urls(sql, exts, options.www, options.path)
        from pprint import pprint
        #pprint(sorted(files))
        print '=' * 78
        #pprint(sorted(urlpaths))
        #print extract_orpheanous(files, urlpaths)
        orpheanous = sorted(files - urlpaths)
        #pprint(orpheanous)
        print '%d media files, %d orpheanous' % (len(files), len(orpheanous))

    except (AssertionError, IOError), e:
        if debug:
            import traceback
            traceback.print_exc()
        else:
            print >> sys.stderr, 'Error:', str(e) or 'Internal error, use -d'
        sys.exit(1)

if __name__ == '__main__':
    main()
