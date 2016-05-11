#!/usr/bin/env python

import re
import os
import sys
from neo.cli import Command
from neo.util import EasyOptionParser

# Decode raw output of NeoVM/QEMU and tie back the function names from an ELF
# file, in order to track the execution path of a virtual CAM application

def parse_symbols(elfpath):
    cre = re.compile(r'(?i)(?P<address>[0-9a-f]+)\s(?P<type>\w)'
                     r'\s(?P<symbol>.*)$')
    symbols = {}
    with Command('arm-eabi-nm', '-AC', elfpath) as nm:
        for l in nm:
            filename, info = l.strip('\n\r\t ').split(':', 1)
            mo = cre.match(info)
            if not mo:
                raise AssertionError('Unknown line format: %s' % info)
            address, type_, symbol = mo.groups()
            symbols[int(address, 16)] = (symbol, type_)
    return symbols

def find_symbol(symbols, address, min_address):
    addr = address & ~3
    max_offset = 0x1000
    while addr >= min_address:
        offset = address-addr
        if offset > max_offset:
            break
        if addr in symbols:
            return (symbols[addr], offset)
        addr -= 4
    return None, address-addr

def analyse_trace(tracepath, symbols, trig_addr, max_addr, short, show_line):
    min_addr = sorted(symbols)[0]
    cre = re.compile(r'(?i)\[([0-9a-f]+)\]\s*$')
    triggered = False
    with open(tracepath, 'rt') as trace:
        last_name = None
        last_offset = 0
        for pos, l in enumerate(trace, start=1):
            mo = cre.search(l.rstrip('\n\r\t '))
            if not mo:
                raise AssertionError('Unknown trace format: %s' % l)
            addr = int(mo.group(1), 16)
            if addr > max_addr:
                continue
            if not triggered:
                if addr < trig_addr:
                    continue
                triggered = True
            symbol, offset = find_symbol(symbols, addr, min_addr)
            if symbol:
                name, type_ = symbol[0], symbol[1]
                if last_name == name:
                    if not short:
                        if show_line:
                            print 'l%-8u' % pos,
                        print "%08x: %+8u" % (addr, offset-last_offset)
                else:
                    if len(name) > 60:
                        n = ''.join((name[:60],'...'))
                    else:
                        n = name
                    if show_line:
                        print 'l%-8u' % pos,
                    print "%08x: %s (%s)" % (addr, n, type_)
                last_offset = offset
            else:
                name, type_ = None, None 
                if show_line:
                    print 'l%-8u' % pos,
                print "%08x: ?" % addr
                last_offset = 0
            last_name = name

def main():
    usage = 'Usage: %prog [options]\n'\
            '  Show CPU execution path'
    optparser = EasyOptionParser(usage=usage)
    default_address = 0x80200040
    max_address = 0x81000000
    try:
        debug = False
        optparser.add_option('-e', '--elf', dest='elf',
                             help='input ELF file')
        optparser.add_option('-t', '--trace', dest='trace',
                             help='input Trace file')
        optparser.add_option('-a', '--address', dest='trig_addr',
                             help='trigger address', type='easyint',
                             default=default_address)
        optparser.add_option('-m', '--max', dest='max_addr',
                             help='upper address', type='easyint',
                             default=max_address)
        optparser.add_option('-s', '--short', dest='short',
                             action='store_true',
                             help='short view: only show function change')
        optparser.add_option('-l', '--line', dest='line',
                             action='store_true',
                             help='show trace line number')
        optparser.add_option('-d', '--debug', dest='debug',
                             action='store_true',
                             help='Show debug information')
        (options, args) = optparser.parse_args(sys.argv[1:])

        debug = options.debug
        if not options.elf or not os.path.isfile(options.elf):
            raise AssertionError('Invalid/missing ELF file')
        if not options.trace or not os.path.isfile(options.trace):
            raise AssertionError('Invalid/missing trace file')
        symbols = parse_symbols(options.elf)
        analyse_trace(options.trace, symbols,
                      options.trig_addr, options.max_addr,
                      options.short, options.line)
        # from pprint import pprint
        # pprint(symbols)

    except (AssertionError, IOError), e:
        if debug:
            import traceback
            traceback.print_exc()
        else:
            optparser.error(str(e) or 'Internal error, use -d')
        sys.exit(1)

if __name__ == '__main__':
    main()
