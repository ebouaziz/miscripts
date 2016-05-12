#!/usr/bin/env python

# Quick and dirty script to generate a skeleton for weekly mails

import appscript as aps
import getpass
import os
import pprint
import sys
import time
import xmlrpclib

now = time.localtime()
weekday = int(time.strftime('%w', now))
yearday = int(time.strftime('%j', now))
daysback = weekday
if weekday < 4:
    # previous week, monday to saturday inclusive
    daysback += 7
    lastday = yearday-weekday
    # sunday 00:00
    lastdate = time.strptime('%s %s' % (now.tm_year, lastday), '%Y %j')
else:
    lastday = 0
    lastdate = now
firstday = yearday-daysback+1
firstdate = time.strptime('%s %s' % (now.tm_year, firstday), '%Y %j')
firsttime = time.mktime(firstdate)
lasttime = time.mktime(lastdate)

things=aps.app('Things')

# Locate the Logbook list
for list_ in things.lists():
    if list_.name() == 'Logbook':
        break
# Recover the TODOs from the Logbook, that is the completed items
print "Tasks:"
for todo in list_.to_dos():
    todotime = time.mktime(todo.completion_date().timetuple())
    if todotime > lasttime:
        print "Too young", todo.name()
    if todotime < firsttime:
        break
    tags = todo.tags()
    project = todo.project()
    if isinstance(project, aps.reference.Reference):
        tags.extend(project.tags())
    private = u'private' in [tag.name() for tag in tags]
    if not private:
        print '       *', todo.name()
print ''

for project in 'sdk prod tools'.split():
    user = os.getenv('USER')
    passwd = os.getenv('LDAP_PASSWD')
    if not passwd:
        prompt = '\nPlease submit your LDAP credentials\n' \
                 'Password: '
        passwd = getpass.getpass(prompt)

    try:
        url = 'http://' + user + ':' + passwd + \
            '@host.domain/trac/'+ project + '/login/xmlrpc'
    except TypeError:
        print "Missing LDAP password"
        sys.exit(1)

    server = xmlrpclib.ServerProxy(url)

    since = xmlrpclib.DateTime(firstdate)
    till = xmlrpclib.DateTime(lastdate)

    user = os.environ.get('USER')
    closed = {}
    if True:
        # print "Querying tickets..."
        for tid in server.ticket.getRecentChanges(since):
            for (date, author, field, old, new, perm) in \
              server.ticket.changeLog(tid):
                if author == user:
                    if field == 'resolution':
                        if new == 'fixed':
                            if tid in closed:
                                if closed[tid] > date:
                                    continue
                            # a ticket may have been modified since fixed
                            if (date >= since) and (date < till):
                                closed[tid] = date
        if closed:
            print project.title(), 'Tickets:'
        for tid in sorted(closed, key=lambda x: closed[x]):
            (_, time_created, time_changed, attributes) = server.ticket.get(tid)
            summary = attributes['summary']
            component = attributes['component']
            date = closed[tid]
            print ' ' * 6, '* #%d: %-18s - %s' % (tid, '(%s)' % component, summary)
        if closed:
            print ''

    # print "Querying pages..."
    if True:
        pages = {}
        for wikipage in server.wiki.getRecentChanges(since):
            author = wikipage['author']
            name = wikipage['name']
            version = wikipage['version']
            if author == user:
                while version:
                    wikipage = server.wiki.getPageInfo(name, version)
                    version -= 1
                    if not wikipage:
                        break
                    author = wikipage['author']
                    if author != user:
                        continue
                    date = wikipage['lastModified']
                    if date > till:
                        continue
                    if date < since:
                        break
                    if version == 1 and name not in pages:
                        pages[name] = 'New document'
                    else:
                        pages[name] = 'Update document'
        if pages:
            print project.title(), 'Wiki:'
        for name in pages:
            print ' ' * 6, '* %s: %s' % (pages[name], name)
        if pages:
            print ''
