#!/usr/bin/env python2.7

# Get error kinds from postfix log messages

import os
import re
import sys


class Extractor(object):

    # 2.X.X   Success
    # 4.X.X   Persistent Transient Failure
    # 5.X.X   Permanent Failure

    EXTCODES = {
        0: {
            None: 'Undefined',
            0: 'Other undefined Status',
        },
        1: {
            None: 'Addressing Status',
            0:  'Other address status',
            1:  'Bad destination mailbox address',
            2:  'Bad destination system address',
            3:  'Bad destination mailbox address syntax',
            4:  'Destination mailbox address ambiguous',
            5:  'Destination address valid',
            6:  'Destination mailbox has moved, No forwarding address',
            7:  'Bad sender\'s mailbox address syntax',
            8:  'Bad sender\'s system address',
        },
        2: {
            None: 'Mailbox Status',
            0: 'Other or undefined mailbox status',
            1: 'Mailbox disabled, not accepting messages',
            2: 'Mailbox full',
            3: 'Message length exceeds administrative limit',
            4: 'Mailing list expansion problem',
        },
        3: {
            None: 'Mail System Status',
            0: 'Other or undefined mail system status',
            1: 'Mail system full',
            2: 'System not accepting network messages',
            3: 'System not capable of selected features',
            4: 'Message too big for system',
            5: 'System incorrectly configured',
        },
        4: {
            None: 'Network and Routing Status',
            0: 'Other or undefined network or routing status',
            1: 'No answer from host',
            2: 'Bad connection',
            3: 'Directory server failure',
            4: 'Unable to route',
            5: 'Mail system congestion',
            6: 'Routing loop detected',
            7: 'Delivery time expired',
        },
        5: {
            None: 'Mail Delivery Protocol Status',
            0: 'Other or undefined protocol status',
            1: 'Invalid command',
            2: 'Syntax error',
            3: 'Too many recipients',
            4: 'Invalid command arguments',
            5: 'Wrong protocol version',
        },
        6: {
            None: 'Message Content or Media Status',
            0: 'Other or undefined media error',
            1: 'Media not supported',
            2: 'Conversion required and prohibited',
            3: 'Conversion required but not supported',
            4: 'Conversion with loss performed',
            5: 'Conversion Failed',
    
        },
        7: {
            None: 'Security or Policy Status',
            0: 'Other or undefined security status',
            1: 'Delivery not authorized, message refused',
            2: 'Mailing list expansion prohibited',
            3: 'Security conversion required but not possible',
            4: 'Security features not supported',
            5: 'Cryptographic failure',
            6: 'Cryptographic algorithm not supported',
            7: 'Message integrity failure',
        }
    }

    EXTCODE_CRE = re.compile(r'(?:^|[^\.0-9])([245]\.\d{1,3}\.\d{1,3})(?:$|[^\.])')
    NOSYNC, ADDRESS, MESSAGE = range(3)

    def __init__(self):
        self._base = {}
        self._errors = {}
        self._current_address = None
        self._current_msgs = []

    def parse(self, fp):
        self._current_address = None
        self._current_msgs = []
        state = self.NOSYNC
        for n, l in enumerate(fp, start=1):
            l = l.strip('\r\n')
            if state in (self.NOSYNC, self.ADDRESS):
                try:
                    s, r = l.split(':', 1)
                except ValueError:
                    s = '-'
                    r = l
                s = s.strip().lower()
                # print '[%s]' % s
                # new email address (new block)
                if s == 'email':
                    self._create_entry(r.strip())
                    state = self.ADDRESS
                    continue
                # error count: don't care
                if s == 'errors':
                    continue
                # new message start line
                if s == 'message':
                    state = self.MESSAGE
                    l = r.lstrip()
            if state == self.NOSYNC:
                continue
            if state in (self.MESSAGE, ):
                if l.endswith('=20'):
                    l = l[:-3]
                    end = True
                elif r.endswith('='):
                    l = l[:-1]
                    end = False
                else:
                    # single-line messages do not have a end-of-line terminator
                    end = True
                # ignore empty lines
                if not l.strip():
                    end = True
                else:
                    self._push_message(l)
                if end:
                    self._close_entry()
                    state = self.NOSYNC
                continue
            print "Unknown content in state %d @ line %d: %s" % (state, n ,l)

    def _create_entry(self, address):
        if self._current_address:
            print "Error: entry %s still on-going" % self._current_address
        self._current_address = address
        self._current_msgs = []

    def _close_entry(self):
        msg = ''.join(self._current_msgs)
        code = self._find_extended_code(msg)
        # do not count duplicate entry
        if not self._current_address in self._base:
            self._base[self._current_address] = code
        # print self._base[self._current_address]
        self._current_address = None

    def _push_message(self, msg):
        self._current_msgs.append(msg)

    @classmethod
    def _find_extended_code(cls, msg):
        mo = cls.EXTCODE_CRE.search(msg)
        if mo:
            return mo.group(1)
        else:
            return None

    def sort(self):
        self._errors = {}
        for addr in self._base:
            error = self._base[addr]
            if error:
                te = tuple([int(x) for x in error.split('.')])
            else:
                te = (5,0,0)
            self._errors.setdefault(te, [])
            self._errors[te].append(addr)

    @classmethod
    def _get_strerror(cls, code):
        try:
            subject = cls.EXTCODES[code[1]]
        except KeyError:
            subject = cls.EXTCODES[0]
        try:
            detail = subject[code[2]]
        except KeyError:
            detail = cls.EXTCODES[0][0]
        error = ': '.join([subject[None], detail])
        return error

    def show(self):
        # from pprint import pprint
        # pprint(self._errors)
        print >> sys.stderr, 'Total: %d entries' % len(self._base)
        for error in reversed(sorted(self._errors,
                                     key=lambda x: len(self._errors[x]))):
            strerror = self._get_strerror(error)
            print >> sys.stderr, \
                '%10s: %d (%s)' % (error, len(self._errors[error]), strerror)

    def build_sql_update(self):
        addresses = set()
        for e in self._errors:
            type_, major, minor = e
            if type_ ==4:
                continue
            addresses.update(self._errors[e])
        sql="update plum_acymailing_subscriber set enabled=0 where " \
            "email='%s';"
        for addr in sorted(addresses):
            print sql % addr

    def list_host_errors(self):
        HOST_ERRORS = ('5.1.2', '4.4.3', '4.1.2')
        for email in self._base:
            code = self._base[email]
            if not code:
                continue
            if code in HOST_ERRORS:
                print email


if __name__ == '__main__':
    ex = Extractor()
    for f in os.listdir(os.getcwd()):
        if not f.endswith('.log'):
            continue
        if not os.path.isfile(f):
            continue
        print "PARSE", f
        with open(f, 'rt') as fp:
            ex.parse(fp)
    ex.sort()
    # ex.show()
    # ex.build_sql_update()
    ex.list_host_errors()

