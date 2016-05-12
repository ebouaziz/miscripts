#!/usr/bin/env python2.7

# Find Base64 encoded data in Joomla files, that may contain hidden malware

import multiprocessing
import re
import os
import sys

#cre = re.compile(r'((?:[A-Za-z0-9+/]{4}){2,}(?:[A-Za-z0-9+/]{2}'
#                 r'[AEIMQUYcgkosw048]=|[A-Za-z0-9+/][AQgw]==))')
cre = re.compile(r'((?:[A-Za-z0-9+/]{2}){32,})')
#                 r'[AEIMQUYcgkosw048]=|[A-Za-z0-9+/][AQgw]==))')

OFFSET = 128
SLEN = 64
WHITELIST = (
    # css image
    'AEwTps2TZ2ZmTn4+fPnHQ0NDf9mzpxp/v//f7OMjIzJIHOmT5+uA5RXT0tLW8s4Y',
    # ambiance.css
    'iVBORw0KGgoAAAANSUhEUgAAAMgAAADICAQAAAAHUWYVAABFFUlEQVQYGbzBCeDV',
    # PNG stuff
    'AAABBBCCCDDDEEEFFFGGGHHHIIIJJJKKKLLLMMMNNNOOOPPPQQQRRRSSSTTTUUUV',
    'aaabbbcccdddeeefffggghhhiiijjjkkklllmmmnnnooopppqqqrrrssstttuuuv',
    'DFDDFDDFDDFDDFDDFDDFDDFDDFDDFDDFDDFDDFDDFDDFDDFDDFDDFDDFDDFDDFDD',
    'dfddfddfddfddfddfddfddfddfddfddfddfddfddfddfddfddfddfddfddfddfdd',
    '////////////////////////////////////////////////////////////////',
    'GaaHbbIddKeeKffLfffggMhhMjjOkkPmmQnnRppSqqTrrUssVttVvvXwwYxxYyyZ',
    # GIF stuff
    '39BBBBBJBB9BV9BcJJBJJJJJRRJBZJBRRRVVZcRJcZJcZRkZRcZZccckcZsmcJRk',
    '11999B19B9991B99BB1BB9B9BJBBJJ19J91J99J9BJ9JJBBR99R9BRB9RBBZB9ZB',
    # PHP
    'vNumberOfDisk/vNoOfDiskWithStartOfCentralDirectory/vNoOfCentralD',
    'Vsig/C2ver/vbitflag/vcompmethod/vlastmodtime/vlastmoddate/Vcrc/V',
    'vTotalCentralDirectoryEntries/VSizeOfCentralDirectory/VCentralDi',
    'a100filename/a8mode/a8uid/a8gid/a12size/a12mtime/a8checksum/Ctyp',
    'vMethod/VTime/VCRC32/VCompressed/VUncompressed/vLength/vExtraLen',
    # google maps
    'ABQIAAAAYoE2kGTD63gv7gR3t7UXVhQTdAkbk1Fj6iiDV2Nno0MdXl3JPBTv43Ws',
    # dropbox
    'eyJhcHAiOiJqZng4enFwdGwyYXc1NGQiLCJzZWNyZXQiOiJuZ2prZmxkY2R3ZDhn',
    # azure
    'Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K',
    'com/sriramk/winazurestorage/blob/214010a2f8931bac9c96dfeb337d56f',
    # ?
    '99999B9BBBB9J91JB1JJ9ZJ3BBBBJBJFBJJJBJRRJBZRBZRJJJRRRRZRRZZRZZZc',
)
WHITELIST_PREFIX = (
    '/Type/Font/Subtype/TrueType/Name',
    'fabrik/plugins/visualization/googlemap',
    'fabrik/plugins/validationrule',
    'documentation/AppleApplications/Reference',
    'fabrik/plugins/visualization',

)
WHITELIST_EXTENSIONS = (
    'css',
    'pdf',
    'pem',
    'otf',
)

def detect(files):
    matched = []
    #print "+"
    for filepath in files:
        #sys.stdout.write('.')
        #sys.stdout.flush()
        with open(filepath, 'rb') as fp:
            data = fp.read()
        resume = True
        while resume and data:
            mo = cre.search(data[OFFSET:])
            if mo:
                b64 = mo.group(1)
                sample = b64[:SLEN]
                data = data[mo.end():]
                if sample in WHITELIST:
                    #print "Whitelist, resume to %d" % len(data)
                    continue
                skip = False
                for w in WHITELIST_PREFIX:
                    if sample.startswith(w):
                        #print "Whitelist, resume to %d" % len(data)
                        skip = True
                        break
                if skip:
                    continue
                # char repeated many times
                if len({x: None for x in sample}) <= 4:
                    continue
                if len(b64) > SLEN:
                    matched.append((filepath, sample))
                    resume = False
            else:
                resume = False
    return matched


def builder(path, count):
    entries = []
    for dirpath, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        if not files:
            continue
        entries.append([os.path.join(dirpath, f) for f in files 
                        if os.path.splitext(f)[1][1:].lower() not in 
                        WHITELIST_EXTENSIONS])
        if len(entries) == count:
            yield(entries)
            entries = []
    if entries:
        yield(entries)

def run():
    forks = 8
    pool = multiprocessing.Pool(forks)
    samples = {}
    for chunk in builder('.', forks):
        results = pool.map(detect, chunk)
        for result in results:
            for f, c in result:
                print "Base64 %s: %s" % (f, c)
                if c not in samples:
                    samples[c] = [f]
                else:
                    samples[c].append(f)
    print "-" * 78
    for c in samples:
        print "Signature %s in %d files:" % (c, len(samples[c]))
        for f in samples[c]:
            print "    %s" % f

def test():
    data = 'MIICWjCCAcMCAgGlMA0GCSqGSIb3DQEBBAUAMHUxCzAJBgNVBAYTAlVTMRgwFgYDVQQKEw9HVEUg'
    mo = cre.search(data)
    print mo

if __name__ == '__main__':
    #test()
    run()
