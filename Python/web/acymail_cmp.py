#!/usr/bin/env python

# Compare AcyMailing CSV files

import sys

clubs = set()
existing = set()

with open('clubs.csv', 'rt') as inf:
	for l in inf:
		if '@' not in l:
			continue
		email, _ = l.split(',', 1)
		email = email.lower()
		clubs.add(email)

with open('all.csv', 'rt') as inf:
	for l in inf:
		if '@' not in l:
			continue
		if ',' in l:
			email, _ = l.split(',', 1)
			email = email.lower()
		else:
			email = l.strip('\r\n').lower()
		existing.add(email)

missing = clubs - existing
print >> sys.stderr, "Total: %d" % len(existing)
print >> sys.stderr,  "Clubs: %d" % len(clubs)
print >> sys.stderr,  "Common: %d" % len (existing & clubs)
print >> sys.stderr,  "Missing: %d" % len(missing)

print 'email;name;confirmed;enabled;accept;html'

for email in sorted(clubs):
	name, domain = email.split('@', 1)
	name = name.replace('.', ' ').title()
	print ';'.join((email, name, '1','1','1','1'))

