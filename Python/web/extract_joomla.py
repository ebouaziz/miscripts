#!/usr/bin/env python3

# Helper script to generate a list of changes from Joomla backup

import difflib
import os
import re
from sqlparse import sql, parse as sqlparse, tokens as sqltokens
from bs4 import BeautifulSoup

'''
GIT

for sha in `git log ffplumsite.sql | grep commit | cut -d' ' -f2 | cut -c-8`; do 
  n=`(git show -s --format=%B $sha | head -1 | tr -d [:space:])`; 
  echo $n; 
  git show $sha:joomla/site.sql | sift plum_content | \
     sift "VALUES \(71" > ~/Desktop/ffplum/$n.sql; 
done
'''

def sql2html(sqlstr):
    p = sqlparse(sqlstr)
    s = p[0]
    par = s.token_next_by_instance(0, sql.Parenthesis)
    il = par.token_next_by_instance(0, sql.IdentifierList)
    htmls = []
    for n, i in enumerate(il.get_identifiers()):
        if n < 4:
            continue
        if n > 5:
            break
        if i.ttype == sqltokens.String.Single:
            val = i.value.strip("'")
            if val:
                htmls.append(val)
    html = ''.join(htmls).replace(r'\r\n', '\r\n')
    soup = BeautifulSoup(html, 'html.parser')
    return ''.join(['<html><body>', soup.prettify(), '</body></html>'])

path = 'tmp/'
date_cre = re.compile(r'(\d{4}\-\d{2}\-\d{2})')
last_h = ''
last_d = ''
filenames = [f for f in os.listdir(path) if f.endswith('.sql')]
for fname in sorted(filenames):
    date_mo = date_cre.search(fname)
    date = date_mo.group(1)
    with open(os.path.join(path, fname), 'rt') as fp:
        d = fp.read()
    h = sql2html(d)
    if last_h != h:
        print("New version on %s" % date)
        hf = difflib.HtmlDiff()
        hs = hf.make_file(last_h.splitlines(keepends=True), h.splitlines(keepends=True),
                          last_d, date, context=True, numlines=3)
        hs = hs.replace('<style type="text/css">\n',
                   '<style type="text/css">\nbody { font-size: 7pt; }')
        hs = hs.replace('font-family:Courier;','font-family:Input;')
        with open(os.path.join(path, '%s.html' % date), 'wt') as diff:
            diff.write(hs)
        # print(list(unified_diff(last_h.splitlines(keepends=True), h.splitlines(keepends=True))))
        # break
    last_h = h
    last_d = date
