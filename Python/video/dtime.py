#!/usr/bin/env python3

"""Documentation
"""

from argparse import ArgumentParser
from datetime import datetime as dt, timedelta as td
from math import floor
from sys import exit, modules, stderr
from traceback import format_exc


def parsetime(timestr, fps=25.0):
    parts = timestr.split('.')
    main = parts[0]
    if len(parts) == 1:
        ms = 0
    if len(parts) == 2:
        frame = int(parts[1])
        if frame >= fps:
            raise ValueError('Invalid frame count')
        ms = 1000.0*frame/fps
    else:
        raise ValueError('Invalid time format')
    fmt = ':'.join(['%%%s' % f for f in reversed('SMH'[:main.count(':')+1])])
    mt = dt.strptime(main, fmt).timetuple()
    return td(seconds=mt.tm_sec, minutes=mt.tm_min, hours=mt.tm_hour,
              milliseconds=ms)


def difftime(ts1, ts2, fps=25.0):
    t1 = parsetime(ts1, fps)
    t2 = parsetime(ts2, fps)
    if t2 > t1:
        delta = t2 - t1
    else:
        delta = t1 - t2
    ts = delta.total_seconds()
    s = floor(ts)
    ms = ts-s
    its = td(seconds=s)
    frame = int(fps*ms)
    return '%s.%d' % (its, frame)


def main():
    """Main routine"""

    debug = False
    try:
        argparser = ArgumentParser(description=modules[__name__].__doc__)
        argparser.add_argument('times', nargs=2,
                               help='times to substract')
        argparser.add_argument('-f', '--fps', type=float, default=25.0,
                               help='frames per second')
        argparser.add_argument('-v', '--verbose', action='count', default=0,
                               help='increase verbosity')
        argparser.add_argument('-d', '--debug', action='store_true',
                               help='enable debug mode')
        args = argparser.parse_args()
        debug = args.debug

        delta = difftime(*args.times, args.fps)
        print(delta)

    except Exception as e:
        print('\nError: %s' % e, file=stderr)
        if debug:
            print(format_exc(chain=False), file=stderr)
        exit(1)
    except KeyboardInterrupt:
        exit(2)


if __name__ == '__main__':
    main()

