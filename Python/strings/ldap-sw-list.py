#!/usr/bin/env python

# Play with a LDAP/LDIF file

people = {}

with open('software.txt') as txt:
    info = {}
    for l in txt:
        l = l.strip()
        if not l:
            cn = info['cn']
            del info['cn']
            people[cn] = info
            info = {}
            continue
        k, v = [x.strip() for x in l.split(':')]
        info[k] = unicode(v, 'utf8')

for k in sorted(people):
    info = people[k]
    v = ','.join(info.values())
    s = u'%s,%s' % (k, v)
    print s.encode('utf8')