#!/usr/bin/env python2.7

# Online SMTP address validator (expect a lot of false positive and negative)

import dns.resolver
import os
import smtplib
import socket
import sys
from Queue import Queue
from optparse import OptionParser
from threading import Thread
from time import sleep


def check_emails(mx, out, q):
    count = 0
    while True:
        from_, to = q.get(block=True)
        if None in (from_, to):
            break

        count += 1
        from_domain = from_.split('@', 1)[1]
        try:
            server = smtplib.SMTP(mx, timeout=10)
            server.set_debuglevel(0)
            server.ehlo(from_domain)
            server.mail(from_)
            code, msg = server.rcpt(to)
            code = int(code)
            if code == 250:
                out[to] = 1
    #            print "Ok"
            else:
                out[to] = -1
    #            return (-1, to)
    #            invalid_emails.add(to)
    #            print "Fail", code, msg.replace('\n', ' ')
            server.quit()
        except (smtplib.SMTPException, socket.error), e:
            print >> sys.stderr, "%s: %s" % (mx, e)
            out[to] = 0
        except Exception, e:
            print >> sys.stderr, "%s: %s" % (mx, e)
    #        return (0, to)
    #        unknown_emails.add(to)
    #        print "Unknown", str(e).replace('\n', ' ')
    print "Exiting %s domain after %d requests" % (mx, count)

def validate(from_, filename, column, first=None):
    valid_emails = set()
    valid_domains = {}
    invalid_emails = set()
    invalid_domains = set()
    unknown_emails = set()
    run = False
    results = dict()
    queues = dict()
    with open(filename, 'rt') as inf:
        for n, l in enumerate(inf):
            if '@' not in l:
                continue
            email = l.strip().lower()
            if column:
                for sep in ',;':
                    if sep in email:
                        parts = email.split(sep)
                        email = parts[column]
                        break
                else:
                    raise AssertionError('No separator in input file')
            if not first or email == first:
                run = True
            if not run:
                continue
            # print "%s:" % email,
            sys.stdout.flush()
            domain = email.split('@', 1)[1]
            if domain in valid_domains:
                pass
            elif domain in invalid_domains:
                invalid_emails.add(email)
                continue
            else:
                try:
                    mxs = [x.to_text().split(' ', 1)[1] 
                           for x in dns.resolver.query(domain, 'MX')]
                except KeyboardInterrupt:
                    break
                except dns.exception.DNSException, e:
                    invalid_domains.add(domain)
                    invalid_emails.add(email)
                    continue
                else:
                    valid_domains[domain] = mxs
            # mx = valid_domains[domain][0]
            use_mx = None
            for mx in valid_domains[domain]:
                if mx not in queues:
                    q = Queue()
                    thread_args = (mx, results, q)
                    t = Thread(target=check_emails,
                               name=mx,
                               args=thread_args)
                    queues[mx] = (t, q)
                    t.start()
                    use_mx = mx
                    break
            if not use_mx:
                use_mx = valid_domains[domain][0]
            request_args = from_, email
            queues[use_mx][1].put(request_args)
    for q in queues:
        queues[q][1].put((None, None))
    while queues:
        completed = [q for q in queues if not queues[q][0].is_alive()]
        for q in completed:
            del queues[q]
        print "Waiting for %d queues" % len(queues)
        for q in queues:
            print '  %s: %d remaining' % (q, queues[q][1].qsize())
        sleep(1)
    for x in results:
        r = results[x]
        if r == -1:
            invalid_emails.add(x)
        elif r == 0:
            unknown_emails.add(x)
        elif r == 1:
            valid_emails.add(x)
        else:
            print "Unknown status", x, r

    for email in sorted(valid_emails):
        print "- Ok: %s" % email
    for email in sorted(invalid_emails):
        print "- Discarded: %s" % email
    for email in sorted(unknown_emails):
        print "- Unknown: %s" % email
    for domain in sorted(invalid_domains):
        print "- Discarded: %s" % domain


def main():
    try:
        debug = False
        from_ = 'postmaster@example.com'
        usage = 'Usage: %prog [options] <email_file>\n'\
                '  Validate a list of emails'
        optparser = OptionParser(usage=usage)
        optparser.add_option('-f', '--from', dest='addr', default=from_,
                             help='sender address, default: %s' % from_)
        optparser.add_option('-c', '--count', dest='column', type='int',
                             help='input file being a CSV, specify which column '
                                  'contains an email address')
        optparser.add_option('-r', '--restart', dest='restart',
                             help='when specified, all addresses specified before '
                                  'this one are ignored')
        optparser.add_option('-d', '--debug', dest='debug', action='store_true',
                             help='show debug messages')
        (options, args) = optparser.parse_args(sys.argv[1:])

        debug = options.debug
        if not len(args):
            optparser.error('Missing email file')
        validate(options.addr, args[0], options.column, options.restart)

    except KeyboardInterrupt:
        raise
    except Exception, e:
        if debug:
            import traceback
            traceback.print_exc()
        else:
            print >> sys.stderr, 'Error:', str(e) or 'Internal error, use -d'
        sys.exit(1)

if __name__ == '__main__':
    main()
