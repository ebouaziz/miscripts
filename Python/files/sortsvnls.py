#!/usr/bin/env python2.7

# Deal with various SVN date output to sort SVN ls by date

import re
import sys
from datetime import timedelta
from time import localtime, mktime, strptime, time

svncre = re.compile(r'\s*(?P<rev>\d+)\s+(?P<author>\w+)\s+'
                    r'(?:(?P<mdate>\w{3}\s\d{2}\s\d{2}:\d{2})|'
                    r'(?P<ydate>\w{3}\s\d{2}\s\d{4}))\s+'
                    r'(?P<path>.*)$')

entries = [svncre.match(l) for l in sys.stdin]
items = [mo.groupdict() for mo in entries if mo]


def totime(x):
    if x['mdate']:
        t = strptime("%d %s" % (localtime().tm_year, x['mdate']),
                     "%Y %b %d %H:%M")
    elif x['ydate']:
        t = strptime(x['ydate'], "%b %d %Y")
    else:
        raise ValueError('Invalid date')
    return t


now = time()
author = ''
authors = set()
for item in sorted(items, key=lambda x: (x['author'], mktime(totime(x)))):
    delta = timedelta(seconds=now-mktime(totime(item)))
    if delta.days > 30:
        if author != item['author']:
            print ''
            author = item['author']
            authors.add(author)
            print '%s:' % author
        print '  {: <8} {: >12} days'.format(item['path'], delta.days)
print ''

print ', '.join(["%s@domain.com" % a for a in sorted(authors)])
