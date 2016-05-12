#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import phone list into LDAP

import sys
from base64 import b64encode

inp = sys.stdin

for l in inp.readlines()[1:]:
    l.strip('\n').strip('\r')
    comp = l.split(',', 4)
    if len(comp) < 4:
        continue
    (firstname, lastname, short, number, dummy) = comp
    firstname = firstname.decode('utf-8').lower()
    lastname = lastname.decode('utf-8').lower()
    uid = ''.join([f[0] for f in firstname.split('-')])
    uid += lastname.replace(u' ', u'').replace(u"'",u'')
    if short.replace(' ', ''):
        short = int(short)
    else:
        short = None
    number = number.replace(' ', '')
    if number:
        number = int(float(number))
    else:
        number = None
    
    dataset = {}
    dataset['uid'] = (uid, False)
    #try:
    #    cn.encode('ascii')
    #    dataset['cn'] = (cn, False)
    #    dataset['displayName'] = (cn, False)
    #except UnicodeEncodeError:
    #    name = b64encode(cn.encode('utf-8'))
    #    dataset['cn'] = (name, True)
    #    dataset['displayName'] = (name, True)
    #try:
    #    lastname.encode('ascii')
    #    dataset['sn'] = (lastname, False)
    #except UnicodeEncodeError:
    #    dataset['sn'] = (b64encode(lastname.encode('utf-8')), True)
    #try:
    #    firstname.encode('ascii')
    #    dataset['givenName'] = (firstname, False)
    #except UnicodeEncodeError:
    #    dataset['givenName'] = (b64encode(firstname.encode('utf-8')), True)
    #dataset['mail'] = ("%s@domain.com" % uid, False)
    if number:
        dataset['telephoneNumber'] = ('%010d' % number, False)
    if short:
        dataset['pager'] = dataset['telephoneNumber']
        dataset['telephoneNumber'] = (short, False)        
    # dataset['l'] = (city, False)

    for (k,(v,b)) in dataset.items():
        if k == 'uid':
            continue
        print "dn: uid=%s,ou=people,dc=domain,dc=com" % uid
        print "changetype: modify"
        #print "delete: telephoneNumber"
        #print "delete: facsimileTelephoneNumber"
        print "add: %s" % k
        print "%s:%s %s" % (k, b and ':' or '', v)
        print ""
    print ""
