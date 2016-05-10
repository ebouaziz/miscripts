#!/usr/bin/env python3

# Convert a (french) CSV file into a Trac table

import csv
import re
import sys


def main(path, sort=None):
    with open(path, 'rt', encoding='iso8859-1') as csvfp:
        rdr = csv.reader(csvfp, delimiter=';')
        rows = [r for r in rdr]
        widths = []
        hextra = 2*len('=**')
        cre = re.compile(r'[A-Z][a-z]+[A-Z][a-z]+')
        def escape_camelcase(mo):
            return "!%s" % mo.group(0)
        nrows = []
        for n, row in enumerate(rows):
            cols = [cre.sub(escape_camelcase, col) for col in row]
            wcols = [len(col.strip()) for col in cols]
            count = len(wcols)-len(widths)
            widths.extend([0] * count)
            if n == 0:
                widths = [max(a, b+hextra) for a, b in zip(widths, wcols)]
            else:
                widths = [max(a, b) for a, b in zip(widths, wcols)]
            nrows.append(cols)
        if isinstance(sort, tuple) or isinstance(sort, list):
            rows, nrows = nrows[:1], nrows[1:]
            nrows.sort(key=lambda item: [item[pos] for pos in sort])
            rows.extend(nrows)
        for n, row in enumerate(rows):
            if n == 0:
                fmts = ["=**%%-%ds**=" % (width-hextra) for width in widths]
                data = ('||'.join([fmt % col for fmt, col in zip(fmts, row)]))
                print('||%s||' % data)
                fmts = ["%%-%ds" % (width) for width in widths]
            else:
                data = '||'.join([fmt % col.strip() for fmt, col in zip(fmts, row)])
                print('||%s||' % data)


if __name__ == '__main__':
    main(sys.argv[1], (1, 0, 2))
