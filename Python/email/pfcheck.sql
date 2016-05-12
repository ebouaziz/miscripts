-- SELECT esub.qid FROM subject sub 
--  INNER JOIN email_subject esub ON esub.subjectid = sub.id 
-- WHERE sub.text LIKE 'Lettre%Décembre 2015';

-- SELECT addr.email FROM email_address addr 
--   INNER JOIN email_recipient rcp ON addr.id = rcp.emailid
--   WHERE rcp.qid IN
--     (SELECT esub.qid FROM subject sub 
--     INNER JOIN email_subject esub ON esub.subjectid = sub.id
--     WHERE sub.text LIKE 'Lettre%Décembre 2015'
--     AND esub.qid NOT IN (SELECT qid FROM email_removal));

--SELECT addr.email, datetime(ins.date, 'unixepoch'), host.ip, host.name, sub.text
--  FROM email_recipient rcp 
--    INNER JOIN email_address addr ON rcp.emailid = addr.id
--    INNER JOIN email_insertion ins ON ins.qid = rcp.qid
--    INNER JOIN host host ON host.id = ins.hostid
--    INNER JOIN email_subject esub ON esub.qid = ins.qid
--    INNER JOIN subject sub ON sub.id = esub.subjectid
--  WHERE addr.email LIKE 'eren%' AND sub.text LIKE 'Lettre%';
--SELECT addr.email, datetime(est.date, 'unixepoch'), st.status, est.msg 
--  FROM email_recipient rcp 
--    INNER JOIN email_address addr ON rcp.emailid = addr.id
--    INNER JOIN email_status est ON est.qid = rcp.qid
--    INNER JOIN status st ON est.statusid = st.id
--    INNER JOIN email_subject esub ON esub.qid = est.qid
--    INNER JOIN subject sub ON sub.id = esub.subjectid
--  WHERE addr.email LIKE 'eren%' AND sub.text LIKE 'Lettre%';
--SELECT addr.email, datetime(rem.date, 'unixepoch')
--  FROM email_recipient rcp 
--    INNER JOIN email_address addr ON rcp.emailid = addr.id
--    INNER JOIN email_removal rem ON rem.qid = rcp.qid
--    INNER JOIN email_subject esub ON esub.qid = rem.qid
--    INNER JOIN subject sub ON sub.id = esub.subjectid
--  WHERE addr.email LIKE 'eren%' AND sub.text LIKE 'Lettre%';

-- SELECT addr.email, datetime(est.date, 'unixepoch'), st.status, est.msg 
--   FROM email_recipient rcp 
--     INNER JOIN email_address addr ON rcp.emailid = addr.id
--     INNER JOIN email_status est ON est.qid = rcp.qid
--     INNER JOIN status st ON est.statusid = st.id
--   WHERE addr.email LIKE 'eren%';

--SELECT datetime(est.date, 'unixepoch'), addr.email, est.msg
--  FROM email_address addr 
--  INNER JOIN email_recipient rcp ON addr.id = rcp.emailid 
--  INNER JOIN email_status est ON est.qid = rcp.qid
--  INNER JOIN status st ON st.id = est.statusid
--  INNER JOIN email_subject esub ON esub.qid = est.qid
--  INNER JOIN subject sub ON sub.id = esub.subjectid
--  WHERE st.status = 'bounced'
--    AND sub.text LIKE 'Lettre%'
--  ORDER BY est.date ASC;

--SELECT DISTINCT saddr.email, saddr.id
--    FROM email_sender snd 
--    INNER JOIN email_address saddr ON saddr.id = snd.emailid
--WHERE saddr.email LIKE '%ffplum.info';

--SELECT sub.text, datetime(est.date, 'unixepoch'), addr.email, est.msg
--  FROM email_address addr 
--  INNER JOIN email_recipient rcp ON addr.id = rcp.emailid 
--  INNER JOIN email_status est ON est.qid = rcp.qid
--  INNER JOIN status st ON st.id = est.statusid
--  INNER JOIN email_subject esub ON esub.qid = est.qid
--  INNER JOIN subject sub ON sub.id = esub.subjectid
--  INNER JOIN email_sender snd ON rcp.qid = snd.qid
--  WHERE st.status = 'bounced'
--    AND snd.emailid = 1
--  ORDER BY sub.text, est.date ASC;

SELECT sub.text, datetime(est.date, 'unixepoch'), addr.email, est.msg
  FROM email_address addr 
  INNER JOIN email_recipient rcp ON addr.id = rcp.emailid 
  INNER JOIN email_status est ON est.qid = rcp.qid
  INNER JOIN status st ON st.id = est.statusid
  INNER JOIN email_subject esub ON esub.qid = est.qid
  INNER JOIN subject sub ON sub.id = esub.subjectid
  INNER JOIN email_sender snd ON rcp.qid = snd.qid
  WHERE st.status = 'bounced'
    AND snd.emailid = 1
    AND datetime(est.date, 'unixepoch') >= date('2016-04-13');

-- SELECT raddr.email
--   FROM email_address raddr 
--   INNER JOIN email_recipient rcp ON raddr.id = rcp.emailid 
--   INNER JOIN email_subject esub ON esub.qid = rcp.qid
--   INNER JOIN subject sub ON sub.id = esub.subjectid
--   WHERE sub.text LIKE 'Lettre%';

--SELECT rcv.emailid
--    FROM email_recipient rcv
--    WHERE rcv.emailid IN
--    (SELECT rcv.emailid
--            FROM email_insertion msg
--            INNER JOIN email_recipient rcv ON msg.qid = rcv.qid 
--            INNER JOIN email_sender snd ON msg.qid = snd.qid
--            INNER JOIN email_address saddr ON snd.emailid = saddr.id
--            INNER JOIN email_address raddr ON rcv.emailid = raddr.id
--            INNER JOIN email_subject esub ON esub.qid = msg.qid
--            INNER JOIN subject sub ON sub.id = esub.subjectid
--        WHERE saddr.email = 'ffplum@ml.ffplum.info'
--            AND sub.text LIKE 'Lettre%'
--            AND raddr.email LIKE '%.ru');

-- SELECT datetime(est.date, 'unixepoch'), sub.text, est.statusid
--     FROM email_recipient rcv
--     INNER JOIN email_status est ON est.qid = rcv.qid
--     INNER JOIN email_subject esub ON esub.qid = rcv.qid
--     INNER JOIN subject sub on sub.id = esub.subjectid
-- WHERE rcv.emailid = 8661 AND est.statusid != 2;

-- SELECT *
--     FROM email_recipient rcv
--     INNER JOIN email_status est ON est.qid = rcv.qid
-- WHERE rcv.emailid = 8661 AND est.statusid != 3;

--SELECT raddr.email, msg.qid
--    FROM email_insertion msg
--    INNER JOIN email_recipient rcv ON msg.qid = rcv.qid 
--    INNER JOIN email_sender snd ON msg.qid = snd.qid
--    INNER JOIN email_address saddr ON snd.emailid = saddr.id
--    INNER JOIN email_address raddr ON rcv.emailid = raddr.id
--    INNER JOIN email_subject esub ON esub.qid = msg.qid
--    INNER JOIN subject sub ON sub.id = esub.subjectid
--WHERE saddr.email = 'ffplum@ml.ffplum.info'
--    AND sub.text LIKE 'Lettre%';

