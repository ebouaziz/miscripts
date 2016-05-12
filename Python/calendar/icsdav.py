#!/usr/bin/env python

# Prototype to manage ICS with a SOGo calendar.

import httplib
import os
import urlparse

from icalendar import Calendar, Event, FreeBusy
from icalendar.tools import UIDGenerator
from caldav import Principal
from caldav.elements import base, dav, cdav
from caldav.lib import error

from datetime import datetime
from lxml import etree
from socket import gethostname

user = os.getenv('USER')
with open(os.path.join(os.getenv('HOME'), '.ldap')) as resource:
    passwd = resource.readline().strip('\r\n')
    if passwd.startswith('export'):
        _, passwd = passwd.split('=')


class DAVResponse(object):
    """
    This class is a response from a DAV request.
    Since we often get XML responses, it tries to parse it into `self.tree`
    """
    raw = ""
    reason = ""
    tree = None
    headers = {}
    status = 0

    def __init__(self, response):
        self.raw = response.read()
        self.headers = response.getheaders()
        self.status = response.status
        self.reason = response.reason

        try:
            self.tree = etree.XML(self.raw)
        except Exception, e:
            print e
            self.tree = None


class DAVClient(object):
    """
    Basic client for webdav, heavily based on httplib
    """
    proxy = None
    url = None

    def __init__(self, url, proxy=None):
        """
        Connects to the server, as defined in the url.
        Parameters:
         * url: A fully qualified url: `scheme://user:pass@hostname:port`
         * proxy: A string defining a proxy server: `hostname:port`
        """

        self.url = urlparse.urlparse(url)

        # Prepare proxy info
        if proxy is not None:
            self.proxy = proxy.split(":")
            if len(self.proxy) == 1:
                self.proxy.append(8080)
            else:
                self.proxy[1] = int(self.proxy[1])

        # Build global headers
        self.headers = {"User-Agent": "Mozilla/5.0"}
        if self.url.username is not None:
            hash_ = (("%s:%s" % (self.url.username.replace('%40', '@'),
                                self.url.password))\
                    .encode('base64')[:-1])
            self.headers['Authorization'] = "Basic %s" % hash_

        # Connection proxy
        if self.proxy is not None:
            self.handle = httplib.HTTPConnection(*self.proxy)
        # direct, https
        elif self.url.port == 443 or self.url.scheme == 'https':
            self.handle = httplib.HTTPSConnection(self.url.hostname,
                                                  self.url.port)
        # direct, http
        else:
            self.handle = httplib.HTTPConnection(self.url.hostname,
                                                 self.url.port)

    def propfind(self, url, props="", depth=0):
        """
        Send a propfind request.

        Parameters:
         * url: url for the root of the propfind.
         * props = [dav.DisplayName(), ...], properties we want
         * depth: maximum recursion depth

        Returns
         * DAVResponse
        """
        return self.xml_request(url, "PROPFIND", props, {'depth': str(depth)})

    def proppatch(self, url, body):
        """
        Send a proppatch request.

        Parameters:
         * url: url for the root of the propfind.
         * body: XML propertyupdate request

        Returns
         * DAVResponse
        """
        return self.xml_request(url, "PROPPATCH", body)

    def report(self, url, query="", depth=0):
        """
        Send a report request.

        Parameters:
         * url: url for the root of the propfind.
         * query: XML request
         * depth: maximum recursion depth

        Returns
         * DAVResponse
        """
        return self.xml_request(url, "REPORT", query,
                            {'depth': str(depth), "Content-Type":
                             "application/xml; charset=\"utf-8\""})

    def mkcol(self, url, body):
        """
        Send a mkcol request.

        Parameters:
         * url: url for the root of the propfind.
         * body: XML request

        Returns
         * DAVResponse
        """
        return self.xml_request(url, "MKCOL", body)

    def put(self, url, body, headers={}):
        """
        Send a put request.
        """
        return self.xml_request(url, "PUT", body, headers)

    def delete(self, url):
        """
        Send a delete request.
        """
        return self.xml_request(url, "DELETE")

    def xml_request(self, url, method="GET", body="", headers=None):
        """
        """

        req_headers = dict(headers)
        req_headers.update({"Content-Type": "text/xml",
                        "Accept": "text/xml"})
        return self.request(url, method, body, req_headers)

    def request(self, url, method="GET", body="", headers=None):
        """
        Actually sends the request
        """
        if self.proxy is not None:
            url = "%s://%s:%s%s" % (self.url.scheme, self.url.hostname,
                                    self.url.port, url)

        req_headers = dict(self.headers)
        req_headers.update(headers)
        if body is None or body == "" and "Content-Type" in req_headers:
            del req_headers["Content-Type"]
        print "--- request ---"
        print url
        for k, v in req_headers.items():
            print ': '.join((k, v))
        print
        print body
        print "---------------"
        self.handle.request(method, url, body, req_headers)

        print "--- response ---"
        r = self.handle.getresponse()
        response = DAVResponse(r)
        print response.status, response.raw
        print "----------------"

        # this is an error condition the application wants to know
        if response.status == httplib.FORBIDDEN or \
                response.status == httplib.UNAUTHORIZED:
            ex = error.AuthorizationError()
            ex.url = url
            ex.reason = response.reason
            raise ex

        return response

# Principal url
auth_url = "http://%s:%s@webmail.network.com/SOGo/dav/%s/Calendar" % \
             (user, passwd, user, )

client = DAVClient(auth_url)
url = ''.join((auth_url[:auth_url.find(':')+3],
               auth_url[auth_url.find('@')+1:]))
print client
principal = Principal(client, url)
calendars = principal.calendars()
if not calendars:
    raise AssertionError('No calendar')
calendar = calendars[0]

calendar_path = calendar.url.path
if not calendar_path.endswith('/'):
    calendar_path = '%s/' % calendar_path

#calendars = principal.calendars()
#print url, calendars
#if len(calendars) > 0:
#    calendar = calendars[0]
#    print "Using calendar", calendar
#
#    print "Looking for events"
#    results = calendar.date_search(datetime(2013, 12, 1))
#    for event in results:
#        print "Found", event

cal = Calendar()
cal.add('calscale', 'GREGORIAN')
cal.add('version', '2.0')
cal.add('method', 'REQUEST')
cal.add('prodid', '-//MeetingGroom//iroazh.eu//')

freebusy = FreeBusy()
freebusy.add('uid', UIDGenerator().uid(gethostname()))
freebusy.add('dtstart', datetime(2013,12,12))
freebusy.add('dtend', datetime(2013,12,13))

cal.add_component(freebusy)

request = cal.to_ical()

request = \
"""BEGIN:VCALENDAR
CALSCALE:GREGORIAN
VERSION:2.0
METHOD:REQUEST
PRODID:-//Apple Inc.//Mac OS X 10.9//EN
BEGIN:VFREEBUSY
UID:4790384D-220D-4B73-86E4-CF639975EC2B
DTEND:20131213T230000Z
X-CALENDARSERVER-EXTENDED-FREEBUSY:T
ATTENDEE:mailto:eblot@network.com
ATTENDEE:mailto:inewton@network.com
DTSTART:20131212T230000Z
X-CALENDARSERVER-MASK-UID:6780CEEF-552B-4B45-8D69-73B724E0EBCF
DTSTAMP:20131212T151449Z
ORGANIZER:mailto:eblot@network.com
END:VFREEBUSY
END:VCALENDAR
"""

request = request.replace('\n', '\r\n')

headers = {
    "Content-Type": "text/calendar",
    "Accept": "*/*",
    "Recipient": "mailto:eblot@network.com, mailto:inewton@network.com",
}



#root = cdav.CalendarQuery() + base.BaseElement(value=request)

#query = etree.tostring(root.xmlelement(), encoding="utf-8",
#                       xml_declaration=True)

#print calendar_path
#print headers
#print request

response = client.request(calendar_path, 'POST', request, headers)

#print response.status

