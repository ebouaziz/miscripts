#!/usr/bin/env python2.6

# Geolocalize netstat entries

import re
import os
import sys
import GeoIP

gi = GeoIP.open("/usr/local/share/GeoIP/GeoIPCity.dat",GeoIP.GEOIP_STANDARD)

def utf8(string):
    return string and unicode(string, 'iso-8859-1').encode('utf-8')

nscre = re.compile(r'^tcp4+\s+\d+\s+\d+\s+'
                   r'(?P<asrc>(?:\d+\.){4})(?P<psrc>\d+)\s+'
                   r'(?P<adst>(?:\d+\.){4})(?P<pdst>\d+)\s+'
                   r'(?P<state>[\w\d_]+)')

peers = []
with open("/Users/eblot/Desktop/netstat.txt") as ns:
    for line in ns.readlines():
        line = line.strip('\n').strip('\r')
        mo = nscre.match(line)
        if not mo or mo.group('state') not in ['ESTABLISHED']:
            continue
        remote = mo.group('adst')[:-1]
        gir = gi.record_by_addr(remote)
        peers.append(', '.join(filter(None, map(utf8,
                                                 [gir['country_name'],
                                                  gir['region_name'],
                                                  gir['city']]))))
peers.sort()
for peer in peers:
    print peer