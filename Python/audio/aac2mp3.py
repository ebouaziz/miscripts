#!/usr/bin/env python3

# Mass re-encode AAC files into MP3 files using several cores if possible

from multiprocessing import Queue, Process, current_process
import os
import sys
from subprocess import Popen, DEVNULL


def convert(src, dst, bitrate):
    dstpath = os.path.dirname(dst)
    if dstpath and not os.path.isdir(dstpath):
        try:
            os.makedirs(dstpath)
        except FileExistsError:
            pass
    self = current_process()
    print("%d: Convert %s" % (self.pid, os.path.basename(src)))
    p = Popen(['/usr/local/bin/ffmpeg', '-threads', '1',
               '-i', src, '-vn', '-y', '-b:a', '%dk' % bitrate, dst],
              stdout=DEVNULL, stderr=DEVNULL)
    p.wait()
    print("%d: done" % self.pid)


def mass_convert(topsrc, topdst):
    for dirpath, dirs, files in os.walk(topsrc, followlinks=True):
        relpath = os.path.relpath(dirpath, topsrc)
        for f in files:
            base, ext = os.path.splitext(f)
            if ext not in ('.m4a', '.aac', '.mp4'):
                continue
            src = os.path.join(dirpath, f)
            dst = os.path.join(topdst, relpath, '%s.mp3' % base)
            yield (src, dst)


def builder(topsrc, topdst):
    for src, dst in mass_convert(topsrc, topdst):
        if os.path.isfile(dst):
            src_size = os.stat(dst).st_size
            dst_size = os.stat(src).st_size
            if src_size > (dst_size//2):
                # print("Skip %s, already exists" % os.path.abspath(dst))
                continue
        yield((src, dst))


def executer(provider, terminator):
    while True:
        src, dst = provider.get()
        if not src:
            print("End of process")
            break
        convert(src, dst, 192)
    self = current_process()
    print("About to terminate %s" % self)
    terminator.put(self)


def run(topsrc, topdst):
    forks = 10
    provider = Queue()
    terminator = Queue()
    processes = set([Process(target=executer, args=(provider, terminator))
                     for f in range(forks)])
    for p in processes:
        p.start()
    for task in builder(topsrc, topdst):
        provider.put(task)
    for p in processes:
        provider.put((None, None))
    while processes:
        p = terminator.get()
        print("%s is about to terminate" % p)
        processes.remove(p)
        p.join()


if __name__ == '__main__':
    src = sys.argv[1]
    dst = sys.argv[2]
    if not os.path.isdir(src) or not os.path.isdir(dst):
        sys.exit(1)
    run(src, dst)
