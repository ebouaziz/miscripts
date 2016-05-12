#!/usr/bin/env python3

# Sort email addresses by their FQDN

import sys

def email_key(e):
    rcpt, fqdn = e.lower().split('@', 1)
    return (fqdn, rcpt)

addrs = set([a.strip() for a in sys.stdin])
for a in sorted(addrs, key=email_key):
    print (a)
