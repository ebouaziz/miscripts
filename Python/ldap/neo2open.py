#!/usr/bin/env python

# Create/update LDAP entries from custom directory to opendirectory schema

import binascii
import os
import re
import sys

cmtcre = re.compile(r'#.*$')

try:
    filename = sys.argv[1]
except IndexError:
    filename = os.path.join(os.path.expanduser('~'), 'Desktop', 'openldap.ldif')

def get_users(filename):
    attributes = []
    with open(filename, 'rt') as in_:
        for (n,l) in enumerate(in_):
            l = l.strip('\r\n')
            l = cmtcre.sub('', l).rstrip('\t ')
            if not l:
                if attributes:
                    dattr = {}
                    for k,t,v in attributes:
                        dattr.setdefault(k, []).append((t,v))
                    try:
                        dn = dattr['dn'][0][1]
                    except KeyError:
                        print >> sys.stderr, "No DN: ", attributes
                        raise StopIteration
                    if 'ou=people' in [x.lower() for x in dn.split(',')]:
                        yield dattr
                        #raise StopIteration
                    else:
                        print >> sys.stderr, "Not a people DN"
                    attributes = []
                continue
            #print n,l
            if l[0] in ' \t':
                # continuation
                attributes[-1] = (attributes[-1][0],
                                  attributes[-1][1],
                                  attributes[-1][2]+l[1:])
                continue
            items = l.split(':')
            k,v = items[0], items[-1].lstrip(' \t')
            b64 = len(items) > 2
            attributes.append((k, b64, v))

OBJECTCLASSES = ['inetOrgPerson','posixAccount','shadowAccount',
                 #'apple-user',
                 'extensibleObject','organizationalPerson','top','person']

def update_user(attributes, uid, gid):
    # add objectclass
    delattrs = []
    for attr in attributes:
        if attr.lower().startswith('trac'):
            delattrs.append(attr)
        if attr.lower() in ['objectclass']:
            delattrs.append(attr)
    for attr in set(delattrs):
        del attributes[attr]
    attributes['objectclass'] = zip([False]*len(OBJECTCLASSES), OBJECTCLASSES)
    attributes['structuralObjectClass'] = [(False, 'inetOrgPerson')]
    attributes['uidNumber'] = [(False, str(uid))]
    attributes['gidNumber'] = [(False, str(gid))]
    attributes['homeDirectory'] = [(False, '/dev/null')]
    attributes['loginShell'] = [(False, '/bin/bash')]

def export_user(dn, attrs):
    lmax = 77
    ndn = []
    for it in dn.split(','):
        k,v = it.split('=')
        if k == 'ou':
            k = 'cn'
            v = 'users'
        ndn.append('='.join([k,v]))
    dn = ','.join(ndn)
    print 'dn:', dn
    for k in attrs:
        for t,v in attrs[k]:
            l = '%s:%s %s' % (k, t and ':' or '', v)
            print '\n '.join([l[lmax*x:lmax*(x+1)] \
                              for x in xrange((len(v)+lmax-1)/lmax)])
    print ''

uid = 1100
gid = 20

for attributes in get_users(filename):
    uid += 1
    (dn, ) = attributes['dn']
    del attributes['dn']
    update_user(attributes, uid, gid)
    export_user(dn[1], attributes)
    #import pprint
    #pprint.pprint(attributes)