#!/usr/bin/env python

# Show HTTP request time

import timeit

setup = '''
import urllib2

url = 'http://localhost:8080/gencert/cramfs?product=SpeedTest'

p = urllib2.HTTPPasswordMgrWithDefaultRealm()
p.add_password(None, 'http://localhost:8080/', 'user', 'passwd')

h = urllib2.HTTPBasicAuthHandler(p)
o = urllib2.build_opener(h)
urllib2.install_opener(o)
'''

code = '''
try:
    u = urllib2.urlopen(url)
    d = u.read()
    u.close()
    assert(len(d) == 8192)
except urllib2.HTTPError, e:
    print e
'''

t = timeit.Timer(code, setup)

for count in range(0,1000):
    r = t.timeit(number=1)
    print '%d, %f' % (count, r*1000)
