#!/usr/bin/env python3

# DVB channel tool output parser/generator

import os
import sys

def parse(fp):
    transponders = []
    columns = ((0, 2), (3, 8), (12, 1), (14, 8), (23, 4), (28, 2), (33, 4))
    for l in fp:
        l = l.strip()
        pos = l.find('#')
        if pos != -1:
            l = l[:pos]
        if not l:
            continue
        cols = [l[x:x+s].strip() for x,s in columns]
        transponders.append(cols)
        #print(':'.join(cols))
    return transponders

def generate(prefix, tps):
    template = """
        freq=%(frequency)d
        pol=%(pol)s
        srate=%(symbolrate)d
        delivery_system=DVB%(type)s
        switch_type=c
        sat_number=1
        autoconfiguration=full
        autoconf_radios=1
        ip_http=0.0.0.0
        port_http=4028
        sap=1
        sap_default_group=%%type
    """
    tpl = '\n'.join([l.strip() for l in template.split('\n') if l.strip()])
    for typ, freq, pol, srate, fec, rol, mod in tps:
        frequency = int(freq[:-3] or 0)
        if not frequency:
            continue
        symbolrate = int(srate[:-3])
        name = '%s_%d.conf' % (prefix, frequency)
        text = tpl % {'frequency': frequency,
                      'pol': pol.lower(),
                      'symbolrate': symbolrate,
                      'type': typ.upper()}
        with open(name, 'wt') as fp:
            print(text, file=fp)
            if mod:
                print('modulation=%s' % mod.upper(), file=fp)
            if rol:
                print('rolloff=%s' % rol, file=fp)
            if fec:
                print('coderate=%s' % fec.lower(), file=fp)

def main(name):
    with open(name, 'rt') as fp:
        tps = parse(fp)
    generate(os.path.splitext(name)[0], tps)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Missing input file', file=sys.stderr)
        exit(1)
    main(sys.argv[1])
