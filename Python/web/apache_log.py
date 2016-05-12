#!/usr/bin/env python

# Some kind of data extractor from Apache logs

import re

# 82.239.190.92 www.host.com - [14/May/2013:05:36:43 +0200] "GET /plugins/system/jcemediabox/themes/standard/css/style.css?version=111 HTTP/1.1" 200 7487 "http://www.ffplum.com/component/phocagallery/category/14-couhe-verac.html" "Mozilla/5.0 (Windows NT 5.1; rv:20.0) Gecko/20100101 Firefox/20.0"

class EasyDict(dict):
    """Dictionary whose members can be accessed as instance members
    """

    def __init__(self, dictionary=None, **kwargs):
        if dictionary is not None:
            self.update(dictionary)
        self.update(kwargs)

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError:
            print self
            raise

    def __setattr__(self, name, value):
        self.__setitem__(name, value)


def parse(fp):
    cre = re.compile(r'^(?P<ip>[\d\.]+)\s'
                     r'(?P<host>[^\s+]+)\s-\s'
                     r'\[(?P<date>[^\]]+)\]\s'
                     r'"(?P<req>[^"]+)"\s'
                     r'(?P<code>\d{3})\s'
                     r'(?:(?P<size>\d+)|\-)\s'
                     r'"(?P<referer>[^"]+)"\s'
                     r'"(?P<useragent>[^"]+)"\s*$'
                     )
    requests = {}
    urls = {}
    for l, r in enumerate(fp):
        mo = cre.match(r)
        if not mo:
            print "Invalid line: %s" % r.strip()
            break
        request = EasyDict(mo.groupdict())
        method, url, protocol = request.req.split(' ')
        #if method in ('GET', 'HEAD', 'OPTIONS', 'PROPFIND'):
        #    continue
        #if method != 'POST':
        #    print "Invalid request: %s" % request.req
        #    break
        params = url.split('?')
        radix = params[0]
        if request.ip not in requests:
            requests[request.ip] = {}
        if radix not in requests[request.ip]:
            requests[request.ip][radix] = 0
        requests[request.ip][radix] += 1
        if radix not in urls:
            urls[radix] = 0
        urls[radix] += 1
    print "Parsed %d entries" % l
    print "By IP"
    for ip in sorted(requests, key=lambda x: 
                     -sum([requests[x][r] for r in requests[x]])):
        iprequests = requests[ip]
        print ip
        for r in sorted(iprequests, key=lambda x: -iprequests[x]):
            print '  %4d %s' % (iprequests[r], r)
        print ''
    print "By URL"
    for url in sorted(urls, key=lambda x: -urls[x]):
        print '%4d: %s' % (urls[url], url)

if __name__ == '__main__':
    with open('web-13-05-2013.log.gz.txt', 'rt') as fp:
        parse(fp)
