#!/usr/bin/env python2.7

# Decode date from pioupiou JSON data

import json
import os
import pprint

try:
    # external package, could be installed with pip install iso8601
    from iso86012 import parse_date
except ImportError:
    from datetime import datetime
    _DATE_FMT = '%Y-%m-%dT%H:%M:%S'

    def parse_date(s):
        try:
            radix, tail = s.rsplit('.')
        except ValueError:
            raise ValueError("Unsupported date format")
        if not tail.endswith('Z'):
            raise ValueError("Unsupported date TZ")
        return datetime.strptime(radix, _DATE_FMT)


def decode_date(d):
    if isinstance(d, dict):
        for k in d:
            v = d[k]
            if k == u'date':
                if v is not None:
                    d[k] = parse_date(v)
            decode_date(v)

with open(os.path.join(os.environ.get('HOME'), '128')) as piou:
    data = piou.read()
jd = json.JSONDecoder()
root = jd.decode(data)
data = root[u'data']
decode_date(data)
pprint.pprint(data)
