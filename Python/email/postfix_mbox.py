#!/usr/bin/env python2.7

# Combine mbox bounced message and postfix log to explain delivery issues

import re
import sys
from mailbox import mbox, mboxMessage
from email.utils import parsedate
from flufl.bounce import all_failures
from calendar import timegm
from collections import defaultdict
from time import strftime, strptime, time, gmtime


def parse_bounces(filename, mintime=None, maxtime=None):
    mb = mbox(filename)
    errors = set()
    count = 0
    for key, msg in mb.iteritems():
        message = mboxMessage(msg)
        msgtime = parsedate(message['Date'])
        count += 1
        print >> sys.stderr, '\r', "%6d" % count, \
            strftime("%Y/%m/%d %H:%M:%S", msgtime),
        sys.stdout.flush()
        t = timegm(msgtime)
        if mintime and t < mintime:
            continue
        if maxtime and t > maxtime:
            continue
        temporary, permanent = all_failures(msg)
        errors.update([p for p in permanent if '@' in p])
    print >> sys.stderr, ""
    print >> sys.stderr, "%s issues" % len(errors)
    return errors


def parse_log(filename, mintime=None, maxtime=None):
    year = gmtime(time()).tm_year
    email_cre = re.compile('<([^<]*@[^>]*)>')
    error_cre = re.compile('(\d\d\d)\s(.*)$')
    emails = defaultdict(list)
    last_errors = dict()
    with open(filename, 'rt') as log:
        for n, l in enumerate(log, start=1):
            try:
                tt = strptime('%d %s' % (year, l[:16]), "%Y %b %d %H:%M:%S ")
            except ValueError:
                print >> sys.stderr, "Unable to parse log @ line %d" % n
                continue
            t = timegm(tt)
            if mintime and t < mintime:
                continue
            if maxtime and t > maxtime:
                continue
            mo1 = email_cre.search(l[16:])
            mo2 = error_cre.search(l[16:])
            if mo1 and mo2:
                email = mo1.group(1)
                code = int(mo2.group(1))
                error = mo2.group(2)
                if code >= 400:
                    # print t, email, code, error
                    emails[email].append((t, code, error))
                elif code == 250:
                    if email in emails:
                        del emails[email]
    for email in emails:
        entries = emails[email]
        #print "email:", email
        for t, code, error in sorted(entries, key=lambda x: -x[0]):
            #print "   ", code, error
            error = error.replace('(in reply to RCPT TO command)','')
            last_errors[email] = (code, error)
            break
    return last_errors


def report_wiki(addresses):
    print "||=**Adresse**=||=**Code**=||=**Erreur**=||"
    for addr in sorted(addresses, key=lambda x: x.lower()):
        if addr in errors:
            code, msg = errors[addr]
            if len(msg) > maxlen:
                msg = '%s...' % msg[:maxlen-3]
            #print " * %s: `%d` ''%s''" % (addr, code, msg)
            #print "%-36s: %d %s" % (addr, code, msg)
            msg = cre.sub('!\\1', msg)
            print "||`%s`||%d||''%s''||" % (addr.lower(), code, msg)
        else:
            #print " * %s: ???" % addr
            #print "%-36s: ???" % addr
            print "||`%s`||||?||" % addr.lower()


def report_csv(addresses):
    print "Adresse,Code,Erreur"
    for addr in sorted(addresses, key=lambda x: x.lower()):
        if addr in errors:
            code, msg = errors[addr]
            if len(msg) > maxlen:
                msg = '%s...' % msg[:maxlen-3]
            msg = cre.sub('!\\1', msg)
            laddr = addr.lower()
            raddr = re.escape(laddr)
            msg = re.sub("(?i)(<)?%s(?(1)>)" % raddr, '', msg)
            print '%s,%d,"%s"' % (laddr, code, msg)
        else:
            print "%s,," % addr.lower()


mboxname, logname, mintime = sys.argv[1:4]

mintime = [int(x) for x in mintime.split('-')][:3]
mintime.extend([0] * 3)
mintime = timegm(tuple(mintime))

addresses = parse_bounces(mboxname, mintime)
errors = parse_log(logname, mintime)
maxlen = 100
cre = re.compile(r'(\[\d+\]|[A-Z][a-z]+[A-Z][a-z]+)')

report_csv(addresses)
