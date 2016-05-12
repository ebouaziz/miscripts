#!/usr/bin/env python2.7

# Inject b64 encoded JPEG file into LDAP

import os

for d in os.listdir('.'):
    if not d.endswith('.b64'):
        continue
    (name,jpg,ext) = d.split('.')
    f = open(d)
    b = f.readlines()
    f.close()
    print "dn: uid=%s,ou=people,dc=domain,dc=com" % name
    print "changetype: modify"
    print "replace: jpegPhoto"
    print "jpegPhoto::",
    for l in b:
        print " %s" % l[:-1]
    print ""
