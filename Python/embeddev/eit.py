#!/usr/bin/env python3

import os
import re
import sys

# Another parser, whose aim has been lost, as many other ones :-)

demangle_cache = {}

def to_int(value):
    """Parse a string and convert it into a value"""
    if not value:
        return 0
    if isinstance(value, int):
        return value
    mo = re.match('(?i)^\s*(\d+)\s*(?:([KM])B?)?\s*$', value)
    if mo:
        mult = { 'k': (1<<10), 'm': (1<<20) }
        value = int(mo.group(1))
        value *= mo.group(2) and mult[mo.group(2).lower()] or 1
        return value
    return int(value.strip(), value.startswith('0x') and 16 or 10)

def parse_eit(filename):
    functions = []
    with open(filename, 'rt') as eit:
        for l in eit:
            l = l.strip()
            if not l.startswith('EIT['):
                continue
            parts = l.split()
            addr = 0
            content = 0
            for p in parts:
                if p.startswith('fn:'):
                    addr = int(p.split(':')[1] ,16)
                if p.startswith('content:'):
                    content = int(p.strip(',').split(':')[1] ,16)
            if content != 1:
                functions.append(addr)
    return functions


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
                print ("SECTION %s" % section)
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
                print ("START OF %s SECTION @ %d" % (section.upper(), n))
            in_section = True
            continue
        if l.startswith(' ' + sectionname):
            if bklcre.match(l):
                last = l
                continue
        elif l.startswith(' .'):
            if in_section is not None:
                if in_section and debug:
                    print ("END OF %s SECTION @ %d" % (section.upper(), n+1))
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
                    print ("END OF %s SECTION @ %d" % (section.upper(), n+1))
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
                # print ("Not found %s" % text_module)
            if text_len:
                section_sizes.setdefault(text_module, 0)
                section_sizes[text_module] += text_len
            # print "%s: %d" % (text_module, text_len)
        elif smo:
            address = int(smo.group(1), 16)
            section_symbols[address] = smo.group(2)
        elif debug:
            print ("Unknown line @ %d:\n\t'%s'" % (n+1, l))
            print ("Broken line? %s" % (bklcre.match(l) and True or False))
    return sections

def parse_map(filename):
    with open(filename, 'rt') as mapf:
        sections = parse_map_file(mapf, False)
        functions = sections['text']['symbols']
    return functions

def parse_asm(filename):
    hexcre = re.compile('(?i)^([0-9A-F]{8})[:\s]')
    entries = {}
    with open(filename, 'rt') as asm:
        for l in asm:
            l = l.strip()
            mo = hexcre.match(l)
            if mo:
                addr = int(mo.group(1), 16)
                if addr not in entries:
                    entries[addr] = l
    return entries

if __name__ == '__main__':
    addresses = parse_eit(sys.argv[1])
    #names = parse_map(sys.argv[2])
    #for addr in sorted(names):
    #    print("%08x" % addr)
    lines = parse_asm(sys.argv[2])
    for addr in addresses:
        if addr in lines:
            print(lines[addr]) 
        else:
            print("Not found: %08x" % addr)