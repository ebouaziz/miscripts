#!/usr/bin/env python3

# Create an SQLite DB from Postfix log for further (error) analysis

import os
import re
from sqlite3 import connect, IntegrityError
import sys

from email.header import decode_header
from time import localtime, mktime, strftime, strptime, time

# Issues:
#   Does not handle colliding MSGID (reused ones). Collisions do occur!!
#   Does not handle years (missing from postfix log)

class PostfixLog(object):

    """
    """

    MSGID_CRE = re.compile(r'^([0-9A-F]{10}): (.*)$')
    INFO_CRE = re.compile(r'^([a-z][a-z\-]+)=')
    SUBJECT_CRE = re.compile(r'^(?:(.*)\s|)from\s[^;]+;\s(.*)$')
    HOST_CRE = re.compile(r'([\w\.\-]+)'
                          r'\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]')

    def __init__(self):
        self._sql = None
        self._subjects = {}

    def create_db(self, dbpath):
        self._sql = connect(dbpath)
        sql = """
        CREATE TABLE subject(id INTEGER PRIMARY KEY,
                             text TEXT UNIQUE);
        CREATE UNIQUE INDEX subject_text ON subject(text);

        CREATE TABLE host(id INTEGER PRIMARY KEY,
                          ip TEXT UNIQUE,
                          name TEXT);

        CREATE TABLE status(id INTEGER PRIMARY KEY,
                            status TEXT UNIQUE);
        CREATE UNIQUE INDEX status_status ON status(status);

        CREATE TABLE email_insertion(qid INTEGER UNIQUE,
                                     date INTEGER,
                                     hostid INTEGER);
        CREATE INDEX email_insertion_hostid ON email_insertion(hostid);

        CREATE TABLE email_removal(qid INTEGER UNIQUE,
                                   date INTEGER);

        CREATE TABLE email_status(qid INTEGER,
                                  date INTEGER,
                                  statusid INTEGER,
                                  count INTEGER,
                                  msg TEXT);
        CREATE UNIQUE INDEX email_status_qid ON email_status(qid, statusid);

        CREATE TABLE email_subject(qid INTEGER UNIQUE,
                                   subjectid INTEGER);
        CREATE INDEX email_subject_subjectid ON email_subject(subjectid);

        CREATE TABLE email_sender(qid INTEGER UNIQUE,
                                  emailid INTEGER);

        CREATE TABLE email_recipient(qid INTEGER UNIQUE,
                                     emailid INTEGER);

        CREATE TABLE email_message(qid INTEGER UNIQUE,
                                   msgid TEXT);
        CREATE INDEX email_message_msgid ON email_message(msgid);

        CREATE TABLE email_address(id INTEGER PRIMARY KEY,
                                   email TEXT UNIQUE);
        CREATE UNIQUE INDEX email_address_email ON email_address(email);
        """
        c = self._sql.cursor()
        c.executescript(sql)

    def load_db(self, dbpath):
        self._sql = connect(dbpath)

    def parse(self, year, fp):
        for n, l in enumerate(fp, start=1):
            l = l.strip()
            datestr = l[:15]
            l = l[16:].lstrip(' ')
            datetp = strptime("%d %s" % (year, datestr), "%Y %b %d %H:%M:%S")
            date = int(mktime(datetp))
            host, process, l = l.split(' ', 2)
            if not process.startswith('postfix/'):
                continue
            parent, r = process.split('/', 1)
            child, r = r.split('[', 1)
            pid, r = r.split(']', 1)
            mo = self.MSGID_CRE.match(l)
            if not mo:
                continue
            qid = int(mo.group(1), 16)
            msg = mo.group(2).strip()
            mo = self.INFO_CRE.match(msg)
            try:
                if not mo:
                    if msg == 'removed':
                        self._remove_msg(qid, date)
                        continue
                    if msg.startswith('warning: header Subject: '):
                        sid = self._store_msg_subject(qid, date,
                                                msg.split(':', 2)[2].strip())
                        continue
                    if msg.startswith('sender non-delivery notification: '):
                        self._create_msg_non_delivery(qid, date,
                                                msg.split(':', 1)[1].strip())
                        continue
                    if msg.startswith('replace: '):
                        self._replace_msg_id(qid, date,
                                             msg.split(':', 1)[1].strip())
                        continue
                    if msg.startswith('milter-reject: '):
                        continue
                    # print('Unsupported msg: %s' % l, file=sys.stderr)
                    continue
                info = mo.group(1).replace('-', '_')
                f = getattr(self, '_handle_%s' % info)
                f(qid, date, msg[len(info)+1:])
            except (ValueError, TypeError, IntegrityError) as e:
                raise ValueError('%s "%s" @ line %d' % (str(e), l, n))
        self._sql.commit()

    def _remove_msg(self, qid, date):
        c = self._sql.cursor()
        c.execute('INSERT INTO email_removal VALUES (?, ?)', (qid, date))

    def _store_msg_subject(self, qid, date, subject):
        mo = self.SUBJECT_CRE.match(subject)
        if not mo:
            raise ValueError('Invalid subject syntax "%s"' % subject)
        subject_parts = []
        subject_string = mo.group(1)
        if subject_string:
            for text, charset in decode_header(subject_string):
                try:
                    if not charset and isinstance(text, bytes):
                        charset = 'ascii'
                    if charset:
                        text = text.decode(charset, 'replace')
                except UnicodeDecodeError as e:
                    raise ValueError(text)
                if text != '? ':
                    subject_parts.append(text)
            subject = ''.join(subject_parts)
        else:
            subject = ''
        params = mo.group(2)
        if subject not in self._subjects:
            c = self._sql.cursor()
            c.execute('SELECT id FROM subject WHERE text=:subject',
                      {'subject': subject})
            row = c.fetchone()
            if not row:
                c.execute('INSERT INTO subject (text) VALUES (?)', (subject,))
                c.execute('SELECT id FROM subject WHERE text=:subject',
                          {'subject': subject})
                row = c.fetchone()
            self._subjects[subject] = row[0]
        subid = self._subjects[subject]
        c = self._sql.cursor()
        c.execute('SELECT subjectid FROM email_subject WHERE qid=:qid',
                  {'qid': qid})
        row = c.fetchone()
        if not row:
            c.execute('INSERT INTO email_subject VALUES (?, ?)',
                      (qid, subid))
        else:
            stored_subid = row[0]
            if stored_subid != subid:
                print("Subject mismatch: %d %d" % (stored_subid, subid),
                      file=sys.stderr)
        return subid

    def _create_msg_non_delivery(self, qid, date, newqid):
        pass

    def _replace_msg_id(self, qid, date, msg):
        pass

    def _handle_uid(self, qid, date, msg):
        pass

    def _handle_message_id(self, qid, date, msg):
        msg = msg.strip('<>').strip()
        if not msg:
            return
        c = self._sql.cursor()
        c.execute('INSERT INTO email_message VALUES (?, ?)', (qid, msg))

    def _handle_from(self, qid, date, msg):
        from_parts = msg.split(',', 1)
        self._store_email(qid, 'sender', from_parts[0])

    def _handle_to(self, qid, date, msg):
        to_parts = msg.split(',')
        self._store_email(qid, 'recipient', to_parts[0])
        parts = {}
        k = None
        for p in to_parts[1:]:
            m = [x.strip() for x in p.split('=', 1)]
            if len(m) < 2:
                if k:
                    parts[k] = ''.join((parts[k], m[0]))
                    continue
            k = m[0]
            parts[k] = m[1]
        if 'status' in parts:
            status, info = parts['status'].split(' ', 1)
            self._store_status(qid, date, status, info)

    def _handle_client(self, qid, date, msg):
        host_parts = msg.split(',', 1)
        hostid = self._store_host(host_parts[0])
        c = self._sql.cursor()
        c.execute('INSERT INTO email_insertion VALUES (?, ?, ?)',
                  (qid, date, hostid))

    def _store_host(self, host):
        mo = self.HOST_CRE.match(host)
        if not mo:
            raise ValueError('Unknown host definition %s' % host)
        c = self._sql.cursor()
        c.execute('SELECT id FROM host WHERE ip=:ip', {'ip': mo.group(2)})
        row = c.fetchone()
        if not row:
            c.execute('INSERT INTO host (ip, name) VALUES (?, ?)',
                      (mo.group(2), mo.group(1)))
            c.execute('SELECT id FROM host WHERE ip=:ip', {'ip': mo.group(2)})
            row = c.fetchone()
        hostid = row[0]
        return hostid

    def _store_email(self, qid, table, address):
        address = address.strip('<>')
        c = self._sql.cursor()
        c.execute('SELECT id FROM email_address WHERE email=:email',
                  {'email': address})
        row = c.fetchone()
        if not row:
            c.execute('INSERT INTO email_address(email) VALUES (?)',
                      (address,))
            c.execute('SELECT id FROM email_address WHERE email=:email',
                      {'email': address})
            row = c.fetchone()
        emailid = row[0]
        c.execute('SELECT emailid FROM email_%s WHERE qid=:qid' % table,
                  {'qid': qid})
        row = c.fetchone()
        if row:
            last_emailid = row[0]
            if last_emailid != emailid:
                print('Sender redefined for %x: %d' % (qid, emailid),
                      file=sys.stderr)
            return
        c.execute('INSERT INTO email_%s VALUES (?, ?)' % table,
                  (qid, emailid))

    def _get_status(self, status, create=False):
        status = status.strip().lower()
        c = self._sql.cursor()
        c.execute('SELECT id FROM status WHERE status=:status',
                  {'status': status})
        row = c.fetchone()
        if not row:
            if not create:
                raise ValueError('No such status: %s' % status)
            c.execute('INSERT INTO status(status) VALUES (?)', (status,))
            c.execute('SELECT id FROM status WHERE status=:status',
                  {'status': status})
            row = c.fetchone()
        statusid = row[0]
        return statusid

    def _store_status(self, qid, date, status, info):
        c = self._sql.cursor()
        statusid = self._get_status(status, True)
        msg = status != 'deferred' and info.lstrip('(').rstrip(')') or ''
        c.execute('SELECT count FROM email_status WHERE qid=:qid '
                  'AND statusid=:statusid',
                  {'qid': qid, 'statusid': statusid})
        row = c.fetchone()
        count = row and row[0] or 0
        c.execute('INSERT OR REPLACE INTO email_status VALUES (?, ?, ?, ?, ?)',
                      (qid, date, statusid, count+1, msg))

    def show_stats_1(self):
        c = self._sql.cursor()
        c.execute('SELECT id, text FROM subject')
        for subid, text in c.fetchall():
            if text.startswith('Lettre'):
                print (subid, text)
                c.execute('SELECT qid FROM email_subject '
                          'WHERE subjectid=:subid', {'subid': subid})
                for qid, in c.fetchall():
                    c.execute('SELECT date FROM email_insertion '
                              'WHERE qid=:qid', {'qid': qid})
                    row = c.fetchone()
                    ins_date = localtime(row[0])
                    c.execute('SELECT date FROM email_removal '
                              'WHERE qid=:qid', {'qid': qid})
                    row = c.fetchone()
                    del_date = row and localtime(row[0])
                    c.execute('SELECT es.date, s.status, es.count FROM email_status es'
                              ' INNER JOIN status s ON es.statusid = s.id '
                              'WHERE qid=:qid '
                              'ORDER BY es.date', {'qid': qid})
                    sequence = []
                    for row in c.fetchall():
                        status, count = row[1:3]
                        sequence.append((status, count))
                        #if sequence and sequence[-1][0] == status:
                        #    sequence[-1] = (status, sequence[-1][1]+1)
                        #else:
                        #    sequence.append((status, 1))
                    seqstr = ', '.join(['%s:%d' % s for s in sequence])
                    print("%010X %s - %s (%s)" % (qid,
                          strftime("%x %X", ins_date),
                          del_date and strftime("%x %X", del_date) or ' ' * 17,
                          seqstr))

    def show_stats_2(self):
        c = self._sql.cursor()
        c.execute('SELECT id, text FROM subject WHERE text LIKE \'Lettre%\'')
        for subid, text in c.fetchall():
            print(text)

"""SELECT addr.email, stat.status
   FROM email_status es
     INNER JOIN status stat ON stat.id = es.statusid
     INNER JOIN email_recipient rcpt ON es.qid = rcpt.qid
     INNER JOIN email_address addr ON addr.id = rcpt.emailid
   WHERE es.qid=0x907E7266D6;
"""

"""SELECT addr.email FROM email_insertion ins
     INNER JOIN email_recipient rcp ON ins.qid = rcp.qid
     INNER JOIN email_address addr ON addr.id = rcp.emailid
     LEFT JOIN email_removal rmv ON ins.qid = rmv.qid
   WHERE rmv.qid IS NULL;
"""

"""SELECT addr.email FROM email_address addr
     INNER JOIN email_recipient rcp ON addr.id = rcp.emailid
   WHERE rcp.qid IN
     (SELECT esub.qid FROM subject sub
        INNER JOIN email_subject esub ON esub.subjectid = sub.id
      WHERE sub.text LIKE 'Lettre%Décembre 2015'
        AND esub.qid NOT IN (SELECT qid FROM email_removal));
"""

def main(dbpath, year):
    pfl = PostfixLog()
    if not os.path.isfile(dbpath):
        pfl.create_db(dbpath)
    else:
        pfl.load_db(dbpath)
    pfl.parse(year, sys.stdin)
    # pfl.show_stats_2()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Missing DB or/and year", file=sys.stderr)
        exit(1)
    year = int(sys.argv[2])
    if year not in (2015, 2016):
        raise ValueError('Invalid year: %s' % sys.argv[2])
    main(sys.argv[1], year)
