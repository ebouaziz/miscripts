#!/usr/bin/env python2.7

from argparse import ArgumentParser, FileType
import csv
import os
import sys

# Compute intersection of email address sets from raw list files

def main():
    default_email_field = 'email address'
    parser = ArgumentParser(description='Filter emails. '
                                'Create a file with all email addresses'
                                'defined in the first CSV file which are'
                                'not defined in the second CSV file')
    parser.add_argument('first', metavar='first', type=FileType('rt'),
                       help='First CSV input file')
    parser.add_argument('existing', metavar='existing', type=FileType('rt'),
                       help='Second CSV input file')
    parser.add_argument('output', metavar='output', type=FileType('wt'),
                       help='Text output file')
    parser.add_argument('-e', '--email', default=default_email_field,
                        help='Alternative email field name, default to "%s"' %
                        default_email_field)

    args = parser.parse_args()


def extract(filename):
    data = []
    with open(filename) as csvf:
        reader = csv.reader(csvf)
        fields = []
        for row in reader:
            if not fields:
                fields = [x.lower() for x in row if x]
            else:
                data.append({x:y for x, y in zip(fields, row)})
    return data

if __name__ == '__main__':
    main()
    sys.exit(1)
    a = extract('/Users/eblot/Desktop/members_export_4ae334d423.csv')
    emails_a = set([x['email address'] for x in a])
    b = extract('/Users/eblot/Desktop/segment_export_6d2f67350a.csv')
    emails_b = set([x['email address'] for x in b])
    result = emails_a-emails_b
    print >> sys.stderr, "Members: %d, Segment: %d, Delta: %d" % \
        tuple(map(len, (emails_a, emails_b, result)))
    for e in sorted(result):
        print e
