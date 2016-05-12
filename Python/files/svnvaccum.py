#!/usr/bin/env python

# Angry man's script to vaccum SVN repository from leftover sandboxes

import os
import re
import sys
import time
from neo.util import EasyOptionParser
from neo.svn import SvnCommand

slscre = re.compile(r'^\s*(?P<rev>\d+)\s+(?P<author>\w+)\s+(?P<date>.*)\s+'
                    r'(?P<sandbox>t\d+[a-z]?)/\s*$')
tktcre = re.compile(r'(?i)^(?:(Refs|Creates)|(Closes|Fixes)) .*#(\d+)')

def main():
    usage = 'Usage: %prog [options]\n'\
            '  Clean up SVN repository from obsoleted sandboxes'
    optparser = EasyOptionParser(usage=usage)
    optparser.add_option('-r', '--repository', dest='repository',
                         help='SVN repository (default: current)',
                         default='^')
    optparser.add_option('-c', '--closed', dest='closed',
                         type='int', default=15,
                         help='Days of obsolescence for closed tickets')
    optparser.add_option('-i', '--inactive', dest='inactive',
                         type='int', default=60,
                         help='Days of obsolescence for inactive sandboxes')
    optparser.add_option('-n', '--dry-run', dest='dryrun',
                         default=False, action='store_true',
                         help='Dry run (show actions but do not execute)')
    optparser.add_option('-o', '--output', dest='output',
                         default=os.getcwd(),
                         help='destination directory')
    (options, args) = optparser.parse_args(sys.argv[1:])

    today = time.localtime()
    year = today.tm_year
    today_sec = time.mktime(today)
    day = 60*60*24
    sandboxes = {}
    prefix = '%s/sandboxes' % options.repository
    with SvnCommand('ls', '--verbose', prefix) as svn:
        for item in svn:
            mo = slscre.match(item)
            if not mo:
                continue
            #print item,
            info = mo.groupdict()
            try:
                age = time.strptime(info['date'], '%b %d  %Y')
            except ValueError:
                try:
                    age = time.strptime(info['date'], '%b %d %H:%M')
                    if age.tm_mon > today.tm_mon:
                        y = year-1
                    else:
                        y = year
                    date = info['date'] + ' %d' % y
                    age = time.strptime(date, '%b %d %H:%M %Y')
                except ValueError:
                    print "Unsupported date format: %s" % age
                    continue
            age_sec = time.mktime(age)
            delta_day = int((today_sec-age_sec)/day)
            sandboxes[info['sandbox']] = delta_day
    for sandbox in sorted(sandboxes):
        svncmd = 'log -l 1 %s/%s' % (prefix, sandbox)
        with SvnCommand(*svncmd.split()) as svn:
            _1 = next(svn)
            meta = next(svn)
            empty = next(svn)
            log = next(svn)
        mo = tktcre.match(log)
        if not mo:
            continue
        delay = sandboxes[sandbox]
        msg = None
        reason = None
        if mo.group(2):
            if delay > options.closed:
                reason = 'forgotten'
                msg = "Terminates! forgotten sandbox. "
                msg += "Ticket #%s is %sd for %d days and all admin requests " \
                       "to delete this sandbox have been ignored till now." % \
                    (mo.group(3), mo.group(2)[:-1].lower(), delay)
        elif mo.group(1):
            if delay > options.inactive:
                reason = 'inactive'
                msg = "Terminates! inactive sandbox. "
                msg += "Sandbox %s is inactive for %d days" % \
                    (sandbox, delay)
        if msg is not None:
            print "Deleting %s sandbox %s (%d days)" % \
                (reason, sandbox, delay),
            if options.dryrun:
                print ' [dry run]'
            else:
                cmd = ['del', '%s/%s' % (prefix, sandbox), '-m', msg]
                with SvnCommand(*cmd) as svn:
                    print svn.read().replace('\n', ' ')

if __name__ == '__main__':
    main()
