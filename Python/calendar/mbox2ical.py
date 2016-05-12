#!/usr/bin/env python

from icalendar import Calendar, Event
from email.parser import Parser
from binascii import a2b_qp, a2b_base64

# Very early prototype to extract ics from emails

class CalendarEvent(object):
    """
    """


class CalendarManager(object):
    """
    """

    RFC822_CODECS = {
        None: lambda x: x,
        'quoted-printable': a2b_qp,
        'base64': a2b_base64,
        '8bit': lambda x: x,
    }

    def __init__(self):
        self._events = {}

    def _parse_vevent(self, component):
        #print component
        uid = component['uid']
        start = component['dtstart'].dt
        end = component['dtend'].dt
        summary = component.get('summary', '')
        location = component.get('location', '?')
        sequence = int(component.get('sequence', 1))
        recurrent = component.get('rrule', {}) 
        print '%s (%d): from %s to %s in %s: %s - %s' % \
            (uid, sequence, start, end, location, summary, recurrent)

    def _parse_ics(self, ics):
        cal = Calendar.from_ical(ics)
        for component in cal.walk():
            #print component.name
            try:
                parser = getattr(self, '_parse_%s' % component.name.lower())
            except AttributeError:
                #print "No parser for %s" % component.name
                continue
            parser(component)

    def _parse_email(self, message):
        messages = message.is_multipart() and message.get_payload() or [message]
        for msg in messages:
            mimetype = msg.get_content_type()
            if mimetype == 'text/calendar':
                ics = msg.get_payload()
                encoding = msg.get('Content-Transfer-Encoding', None)
                ics = self.RFC822_CODECS[encoding](ics)
                self._parse_ics(ics)

    def parse(self, filename):
        parser = Parser()
        with open(filename, 'rt') as eml:
            message = parser.parse(eml)
            self._parse_email(message)

if __name__ == '__main__':
    cal = CalendarManager()
    for x in range(1, 5):
        cal.parse('/Users/eblot/Desktop/calendar/%d.eml' % x)