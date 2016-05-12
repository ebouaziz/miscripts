#!/usr/bin/env python3

import re
import sys

# Parameter positions (start from 0)
ADDRESS, MSG = 2, 3

errors = dict()
cre = re.compile('(?i)host .* said:')
for l in sys.stdin:
    l = l.strip()
    items = [item.strip() for item in l.split('|')]
    # Preserve the last error message for each address
    msg = cre.sub('', items[MSG])
    errors[items[ADDRESS]] = msg.strip()

print ('Adresse;Derniere Erreur')
for addr in sorted(errors):
    print(';'.join((addr, errors[addr])))
