#!/usr/bin/env python2.7

# Parse and decode an ARM-EABI MAP file

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
    loccre = re.compile(r'^\s+\.text.*(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+'
                        r'([^\(]*)(\(.*\))?', re.IGNORECASE)
    for n, l in enumerate(mapf.xreadlines()):
        n = n+1
        l = l.strip('\n').strip('\r')
        if l.startswith(' .text'):
            # if not text_section:
            #     print "TEXT @ %d" % n
            text_section = True
            if len(l) > 16 and l[len(' .text')+1] != ' ':
                continue
        elif l.startswith(' .'):
            # if text_section:
            #     print "END TEXT @ %d" % n
            text_section = False
        elif l.startswith(' *('):
            # if text_section:
            #     print "END TEXT @ %d" % n
            text_section = False
        if not text_section:
            continue
        lmo = loccre.search(l)
        smo = symcre.match(l)
        # if not lmo and not smo:
        #     pass
        #     #print "Unknown line @ %d:\n\t'%s'" % (n+1, l)
        if lmo:
            address = int(lmo.group(1), 16)
            symbols[address] = lmo.group(4)
            # print 'LMO %d %s' % (n, symbols[address])
        if smo:
            address = int(smo.group(1), 16)
            symbols[address] = smo.group(2)
            # print "@ %08x : %s" % (address, symbols[address])
    return symbols


def parse_abort_trace(tracef):
    stkcre = re.compile(r'^([0-9a-f]{8}):\s+((?:[0-9a-f]{2}\s+){16})',

                        re.IGNORECASE)
    regcre = re.compile(r'([A-Z]{2,3}):\s([0-9a-f]{8})', re.IGNORECASE)
    stack = []
    registers = {}
    for n, l in enumerate(tracef.readlines()):
        mo = stkcre.match(l)
        if mo:
            address = int(mo.group(1), 16)
            data = mo.group(2).strip(' ').replace('  ', ' ')
            bytes = data.split(' ')
            while len(bytes):
                word = binascii.unhexlify(''.join(bytes[0:4]))
                bytes[:] = bytes[4:]
                (value, ) = struct.unpack('<I', word)
                stack.append(value)
        if ',' in l:
            for reg in l.strip('\n').strip('\r').split(','):
                mo = regcre.match(reg.strip(' '))
                if mo:
                    registers[mo.group(1).lower()] = \
                        int('0x%s' % mo.group(2), 16)
    return reversed(stack), registers


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


def decode_stack(symbols, stack):
    print "Decoded stack:"
    for address in stack:
        symbol = find_symbol(symbols, address)
        if symbol:
            print "  0x%08x: %s" % (address, demangle(symbol))


def decode_registers(symbols, registers):
    print "Decoded registers:"
    for reg in regs:
        symbol = find_symbol(symbols, registers[reg])
        if symbol:
            print "  %s: %s" % (reg, demangle(symbol))


# -- Main -------------------------------------------------------------------

if __name__ == "__main__":
    usage = 'Usage: %prog [options]\n' \
            '   Parse an arm-eabi MAP file'
    optparser = OptionParser(usage=usage)
    optparser.add_option('-m', '--map', dest='map',
                         help='input ELF32 map file')
    optparser.add_option('-a', '--address', dest='address',
                         help='symbol address to look up')
    optparser.add_option('-t', '--trace', dest='trace',
                         help='frame trace to analyse')
    optparser.add_option('-i', '--input', dest='input',
                         help='read symbol address from the specified file')
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
            with options.input != '-' and open(options.input, 'r') or \
              sys.stdin as inp:
                for line in inp:
                    line = line.strip('\r\n\t ')
                    address = int(line, 16)
                    symbol = demangle(find_symbol(symbols, address))
                    if not symbol:
                        AssertionError('No symbol @ 0x%x' % address)
                    print "@ 0x%08x: %s" % (address, symbol)
        if options.trace:
            with (options.trace == '-') and sys.stdin or \
              open(options.trace, 'rt') as tracef:
                (stack, regs) = parse_abort_trace(tracef)
                decode_stack(symbols, stack)
                decode_registers(symbols, regs)

    except AssertionError, e:
        print >> sys.stderr, "Error: %s" % e
        sys.exit(1)
