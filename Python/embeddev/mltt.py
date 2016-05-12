#!/usr/bin/env python2.7

# Just another helper based on MAP file and output traces

from optparse import OptionParser
from subprocess import Popen, PIPE, STDOUT
import binascii
import re
import struct
import sys

demangle_cache = {}

def parse_map_file(mapf):
    symbols = {}
    text_section = False
    symcre = re.compile(r'^\s+(0x[0-9a-f]+)\s+([a-z_]\w+)', re.IGNORECASE)
    loccre = re.compile(r'^\s+\.text.*(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+([^\(]*)(\(.*\))?',
                        re.IGNORECASE)
    for n,l in enumerate(mapf.xreadlines()):
        n = n+1
        l = l.strip('\n').strip('\r')
        if l.startswith(' .text'):
            #if not text_section:
            #    print "TEXT @ %d" % n
            text_section = True
            if len(l) > 16 and l[len(' .text')+1] != ' ':
                continue
        elif l.startswith(' .'):
            #if text_section:
            #    print "END TEXT @ %d" % n
            text_section = False
        elif l.startswith(' *('):
            #if text_section:
            #    print "END TEXT @ %d" % n
            text_section = False
        if not text_section:
            continue
        lmo = loccre.search(l)
        smo = symcre.match(l)
        #if not lmo and not smo:
        #    pass
        #    #print "Unknown line @ %d:\n\t'%s'" % (n+1, l)
        if lmo:
            address = int(lmo.group(1), 16)
            symbols[address] = lmo.group(4)
            #print 'LMO %d %s' % (n, symbols[address])
        if smo:
            address = int(smo.group(1), 16)
            symbols[address] = smo.group(2)
            #print "@ %08x : %s" % (address, symbols[address])
    return symbols

def find_symbol(symbols, address):
    symbol = None
    for addr in sorted(symbols.keys()):
        if addr > address:
            return symbol
        elif addr <= address:
            symbol = symbols[addr]
    return None

def demangle(symbol):
    if not symbol:
        return symbol
    global demangle_cache
    if symbol in demangle_cache:
        return demangle_cache[symbol]
    args = ['arm-eabi-c++filt', symbol]
    demangle = symbol
    try:
        cppfilter = Popen(args, stdout=PIPE)
        demangle = cppfilter.stdout.readlines()[0].strip('\n')
        cppfilter.wait()
    except:
        pass
    demangle_cache[symbol] = demangle
    return demangle

def decode_mltt(symbols, inp, threshold, verbose=False):
    # MLTT caller: 0x80291bf4, buff: 0x80542e20, size: 0x8
    mre = r'^MLTT caller: (0x[0-9a-f]+), buff: (0x[0-9a-f]+), size: (0x[0-9a-f]+)'
    mcre = re.compile(mre, re.IGNORECASE)

    leaks = {}
    for line in inp:
        line = line.strip('\r\n\t ')
        mo = mcre.match(line)
        if mo:
            (caller, buff, size) = [int(x, 16) for x in mo.groups()]
            if caller: # discard empty entries in the dumped table
                leaks.setdefault(caller, []).append(size)

    callers = reversed(sorted(leaks, key=lambda x: len(leaks[x])))
    for caller in callers:
        symbol = demangle(find_symbol(symbols, caller)) or str(caller)
        distribution = {}
        for size in leaks[caller]:
            if size not in distribution:
                distribution[size] = 1
            else:
                distribution[size] += 1
        maxdist = list(reversed(sorted(distribution.values())))[0]
        if maxdist <= threshold:
            break
        count = len(leaks[caller])
        size = sum(leaks[caller])
        print "%-40s: %3d objects, %6d alloc. bytes, @ 0x%08x" % \
                (symbol, count, size, caller)
        if verbose:
            import pprint
            pprint.pprint(distribution)


#--- Main -------------------------------------------------------------------

if __name__ == "__main__":
    usage = 'Usage: %prog [options]\n' \
            '   Decode memory leak tracker info'
    optparser = OptionParser(usage=usage)
    optparser.add_option('-m', '--map', dest='map',
                         help='input ELF32 map file')
    optparser.add_option('-a', '--address', dest='address',
                         help='symbol address to look up')
    optparser.add_option('-i', '--input', dest='input',
                         help='MLTT input file')
    optparser.add_option('-t', '--threshold', dest='threshold',
                         help='Minimum count of objects to declare a leak',
                         default='4')
    optparser.add_option('-v', '--verbose', dest='verbose',
                         action='store_true', help='Verbose mode')
    (options, args) = optparser.parse_args(sys.argv[1:])

    try:
        if not options.map:
            raise AssertionError('Missing map file')
        with open(options.map, 'rt') as mapf:
            symbols = parse_map_file(mapf)
            mapf.close()
        if options.address:
            address = int(options.address, 16)
            symbol = demangle(find_symbol(symbols, address))
            if not symbol:
                 AssertionError('No symbol @ 0x%x' % address)
            print "Symbol %s @ 0x%x" % (symbol, address)
        if options.input:
            with options.input != '-' and open(options.input, 'r') \
                or sys.stdin as inp:
                decode_mltt(symbols, inp, int(options.threshold),
                            options.verbose)

    except AssertionError, e:
        print >> sys.stderr, "Error: %s" % e
        sys.exit(1)
