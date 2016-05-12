#!/usr/bin/env python

# Filter out and extract custom info from a CSV file

import csv
import re

filename = '/Users/eblot/Desktop/RebutFuseLot1045.csv'

fields = ('serial', 'task', 'error', 'result')
unmanaged_errors = []
errors = {}
errcre = re.compile(r'^.*\((.*)\).*$')
with open(filename, 'rb') as csvfile:
    dreader = csv.DictReader(csvfile, fields)
    for d in dreader:
        if not dreader.line_num:
            # skip header
            continue
        try:
            name, msg = d['result'].split(',', 1)
            mo = errcre.match(msg)
            if not mo:
                unmanaged_errors.append(msg)
            error = mo.group(1).strip('",')
            if error.startswith('Error in task'):
                error = error.split(',',1)[1]
            count = errors.get(error, 0)
            errors[error] = count + 1
        except ValueError:
            unmanaged_errors.append(d['result'])

total = 0
for error in reversed(sorted(errors, key=lambda k: errors[k])):
    total += errors[error]
    print "%3d: %s" % (errors[error], error)
print total