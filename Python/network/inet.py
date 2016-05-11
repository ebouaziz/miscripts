#!/usr/bin/env python2.7

# Experiment with netifaces module

from netifaces import interfaces, ifaddresses, AF_INET

for ifaceName in interfaces():
    try:
        addresses = [i['addr'] for i in ifaddresses(ifaceName)[AF_INET]]
        print '%s: %s' % (ifaceName, ', '.join(addresses))
    except KeyError, e:
        print "%s: no defined address" % ifaceName