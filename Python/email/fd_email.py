#!/usr/bin/env python3

from argparse import ArgumentParser, FileType
import csv
import os
import sys

# Compute intersection of email address sets from raw list files


def extract(csvfp):
    data = []
    reader = csv.reader(csvfp)
    fields = []
    for row in reader:
        if not fields:
            fields = [x.lower() for x in row if x]
        else:
            data.append({x: y for x, y in zip(fields, row)})
    return data


def main():
    default_email_field = 'Email Address'
    parser = ArgumentParser(description='Filter emails. '
                            'Create a CSV file with email addresses'
                            'filtered from two CSV files')
    parser.add_argument('first', type=FileType('rt'),
                        help='First CSV input file')
    parser.add_argument('second', type=FileType('rt'),
                        help='Second CSV input file')
    parser.add_argument('output', type=FileType('wt'), nargs='?',
                        help='Text output file')
    parser.add_argument('-m', '--mode', required=True,
                        choices=('merge', 'missing', 'common', 'remove'),
                        help='Alternative email field name, default to "%s"' %
                        default_email_field)
    parser.add_argument('-e', '--email', default=default_email_field,
                        help='Alternative email field name, default to "%s"' %
                        default_email_field)

    args = parser.parse_args()

    sets = 'first second'.split()
    emails = {}
    for pos in 'first second'.split():
        tab = extract(getattr(args, pos))
        try:
            emails[pos] = set([x['email address'] for x in tab])
        except KeyError:
            raise ValueError("'No such column in %s CSV: '%s'" %
                             (pos, args.email))
    if args.mode == 'merge':
        new = emails[sets[0]] | emails[sets[1]]
    elif args.mode == 'common':
        new = emails[sets[0]] & emails[sets[1]]
    elif args.mode == 'remove':
        new = emails[sets[0]] - emails[sets[1]]
    elif args.mode == 'missing':
        new = set([email for email in emails[sets[1]]
                   if email not in emails[sets[0]]])
    print('%10d email addresses in first list' % len(emails[sets[0]]))
    print('%10d email addresses in second list' % len(emails[sets[1]]))
    print('%10d email addresses in output list' % len(new))
    if args.output:
        print(default_email_field, file=args.output)
        for email in sorted(new):
            print(email, file=args.output)


if __name__ == '__main__':
    main()
