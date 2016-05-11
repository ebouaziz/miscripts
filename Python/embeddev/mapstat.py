#!/usr/bin/env python2.7

# Show memory footprint from an arm-eabi MAP file

from optparse import OptionParser
from subprocess import Popen, PIPE, STDOUT
import binascii
import os
import re
import struct
import sys

demangle_cache = {}

def to_int(value):
    """Parse a string and convert it into a value"""
    if not value:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, long):
        return int(value)
    mo = re.match('(?i)^\s*(\d+)\s*(?:([KM])B?)?\s*$', value)
    if mo:
        mult = { 'k': (1<<10), 'm': (1<<20) }
        value = int(mo.group(1))
        value *= mo.group(2) and mult[mo.group(2).lower()] or 1
        return value
    return int(value.strip(), value.startswith('0x') and 16 or 10)

def parse_map_file(mapf, debug):
    DISCARDED_SECTION = ('debug*', 'comment*', 'ARM*', 'note*')
    in_section = None # Tri-state: None, True, False
    dsccre = re.compile(r'|'.join([x.replace('.',r'\.').replace('*',r'.*')
                                   for x in DISCARDED_SECTION]))
    symcre = re.compile(r'^\s+(0x[0-9a-f]+)\s+([a-z_]\w+)', re.IGNORECASE)
    bldcre = re.compile(r'^(?:CMakeFiles|.*/(?:build|arm-eabi))/'
                        r'([\w_\./]+\.[ao])(\(.*\))?$')
    empcre = re.compile(r'^\s\*\([\w\.]+\*?\)\s*$')
    igncre = re.compile(r'^\s(\*fill\*|COMMON)')
    last = ''
    section = None
    sectionname = None
    sections = {}
    for n,l in enumerate(mapf.readlines()):
        l = l.strip('\n').strip('\r')
        if l.startswith('.'):
            last = ''
            if sectionname:
                sections[section] = { 'symbols': section_symbols,
                                      'sizes' : section_sizes,
                                      'objects' : section_objects }
            section = l[1:].split(' ')[0]
            if section not in ('text', 'bss' ,'rodata' ,'data'):
            # if dsccre.match(section):
                sectionname = None
                continue
            sectionname = '.%s' % section
            if debug:
                print "SECTION %s" % section
            section_symbols = {}
            section_sizes = {}
            section_objects = {}
            bklcre = re.compile(r'^\s\.' + section + r'\.[\w_\.]+\s*$')
            loccre = re.compile(r'^\s\.' + section +
                                r'.*(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+'
                                r'(.*)(?:\(.*\))?',
                                re.IGNORECASE)
        if not sectionname:
            continue
        if l.startswith(sectionname):
            if not in_section and debug:
                print "START OF %s SECTION @ %d" % (section.upper(), n)
            in_section = True
            continue
        if l.startswith(' ' + sectionname):
            if bklcre.match(l):
                last = l
                continue
        elif l.startswith(' .'):
            if in_section is not None:
                if in_section and debug:
                    print "END OF %s SECTION @ %d" % (section.upper(), n+1)
                in_section = False
        elif empcre.match(l) or igncre.match(l):
            continue
        elif l.endswith('(size before relaxing)') or l.endswith('. = .'):
            continue
        elif l.startswith(' *('):
            if l[3:].startswith(sectionname):
                continue
            if in_section is not None:
                if in_section and debug:
                    print "END OF %s SECTION @ %d" % (section.upper(), n+1)
                in_section = False
        if not in_section:
            last = ''
            continue
        if last:
            l = '%s%s' % (last, l)
            last = ''
        lmo = loccre.match(l)
        smo = symcre.match(l)
        if lmo:
            text_module = ''
            text_len = to_int(lmo.group(2))
            bo = bldcre.match(lmo.group(3))
            if bo:
                _, text_module = os.path.split(bo.group(1))
                if text_len:
                    obj = bo.group(2)
                    if obj:
                        obj = obj.strip('()')
                        section_objects.setdefault(obj, 0)
                        section_objects[obj] += text_len
            else:
                text_module = lmo.group(3)
                print "Not found %s" % text_module
            if text_len:
                section_sizes.setdefault(text_module, 0)
                section_sizes[text_module] += text_len
            #print "%s: %d" % (text_module, text_len)
        elif smo:
            address = int(smo.group(1), 16)
            section_symbols[address] = smo.group(2)
        elif debug:
            print "Unknown line @ %d:\n\t'%s'" % (n+1, l)
            print "Broken line? %s" % (bklcre.match(l) and True or False)
    return sections

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

def show_stats(filename, sections):
    modules = {}
    for s in sections:
        sizes = sections[s]['sizes']
        for mod in sizes:
            modules[mod] = True
    modules = sorted(modules.keys())
    print ' %-25s' % os.path.basename(filename),
    print ' '.join(["%10s" % s for s in sections])
    print '-' * (26+len(sections)*11)
    totalcount = {}
    for m in modules:
        print " %-23s |" % m,
        for s in sections:
            module = sections[s]['sizes']
            count = m in module and module[m] or 0
            print "%10d" % count,
            totalcount.setdefault(s, 0)
            totalcount[s] += count
        print ""
    print '-' * (26+len(sections)*11)
    print " %-23s |" % 'Total',
    for t in sections:
        print "%10d" % totalcount[t],


#--- Main -------------------------------------------------------------------

if __name__ == "__main__":
    usage = 'Usage: %prog [options]\n' \
            '   Show memory footprint from a MAP file'
    optparser = OptionParser(usage=usage)
    optparser.add_option('-m', '--map', dest='map',
                         help='input ELF32 map file')
    optparser.add_option('-d', '--debug', dest='debug', action='store_true',
                         help='show debug messages')
    (options, args) = optparser.parse_args(sys.argv[1:])

    try:
        if not options.map:
            raise AssertionError('Missing map file')
        with open(options.map, 'rt') as mapf:
            sections = parse_map_file(mapf, options.debug)
            mapf.close()
            show_stats(options.map, sections)
            #import pprint
            #for s in sections:
            #    v = sections[s]
            #    print "%s: sizes %s" % (s, pprint.pformat(v['sizes']))
            #pprint.pprint(sections)
            #print "Text total: %d" % sum(text_size.values())

    except AssertionError, e:
        print >> sys.stderr, "Error: %s" % e
        sys.exit(1)
