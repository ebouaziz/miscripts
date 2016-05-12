#!/usr/bin/env python3

# Find errors in Postfix log SQLite DB

import re
import sys
from collections import defaultdict
from sqlite3 import connect

class PostfixSearch(object):

    """
    """

    def __init__(self):
        self._sql = None

    def load_db(self, dbpath):
        self._sql = connect(dbpath)

    def find_msg_by_subject(self, sender, subject):
        request = """
        SELECT raddr.email, msg.qid, st.status
            FROM email_insertion msg
            INNER JOIN email_recipient rcv ON msg.qid = rcv.qid
            INNER JOIN email_sender snd ON msg.qid = snd.qid
            INNER JOIN email_address saddr ON snd.emailid = saddr.id
            INNER JOIN email_address raddr ON rcv.emailid = raddr.id
            INNER JOIN email_subject esub ON esub.qid = msg.qid
            INNER JOIN subject sub ON sub.id = esub.subjectid
            INNER JOIN email_status est ON est.qid = msg.qid
            INNER JOIN status st ON est.statusid = st.id
        WHERE saddr.email = :sender
            AND sub.text LIKE :subject
        ORDER BY raddr.email
        """
        c = self._sql.cursor()
        c.execute(request, {'sender': sender, 'subject': subject})
        for row in c.fetchall():
            yield row

    def find_reason_by_qid(self, qid):
        request = """
        SELECT est.msg, datetime(est.date, 'unixepoch')
            FROM email_status est
        WHERE est.qid=:qid
        """
        c = self._sql.cursor()
        c.execute(request, {'qid': qid})
        return c.fetchone()


HOSTERROR_CRE = re.compile(r'^host\s([\w\.\-]+)'
                           r'\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]\s'
                           r'said:\s(\d{3})\s(.*)$')

def main(dbpath, sender, subject):
    ps = PostfixSearch()
    ps.load_db(dbpath)
    addresses = defaultdict(list)
    for email, qid, status in ps.find_msg_by_subject(sender, subject):
        addresses[email].append((status, qid))
    invalid = 0
    issues = {}
    for addr in sorted(addresses, key=lambda a: a.lower()):
        statuses = addresses[addr]
        if 'sent' not in [s[0] for s in statuses]:
            qid = [s[1] for s in statuses if s[0] == 'bounced']
            if not qid:
                # likely to be invalid addresses
                # print(addr, statuses)
                invalid +=1 
            else:
                reason, dt = ps.find_reason_by_qid(qid[0])
                issues[addr] = (dt, reason)
                #print(addr)
    for addr in sorted(issues, key=lambda a: issues[a][0]):
        dt, reason = issues[addr]
        # print("%-32s %-20s %s" % (addr, dt, reason))
        mo = HOSTERROR_CRE.match(reason)
        if mo:
            reason = mo.group(4)
            code = int(mo.group(3))
        else:
            reason = reason
            code = 500
        print("%s,%d,%s" % (addr, code, reason))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Missing DB", file=sys.stderr)
        exit(1)
    #main(sys.argv[1], 'Lettre%%Décembre 2015')
    main(sys.argv[1], 'paca@ml.ffplum.info', 'Newsletter Radios 8.33')
