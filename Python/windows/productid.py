#!/usr/bin/env python3

import sys


def mid(string, pos, length):
    return string[min(pos - 1, len(string)):pos - 1 + length]


def hex2key(keybytes):
    keyoutput = ''
    keyoffset = 52
    keybytes = list(keybytes)
    i = 28
    CHARS = "BCDFGHJKMPQRTVWXY2346789"
    while i >= 0:
        cur = 0
        x = 14
        while x >= 0:
            cur = cur * 256
            cur = keybytes[x + keyoffset] + cur
            keybytes[x + keyoffset] = (cur // 24) & 255
            cur = cur % 24
            x = x - 1
        i = i - 1
        keyoutput = ''.join((mid(CHARS, cur + 1, 1), keyoutput))
        if (((29 - i) % 6) == 0) and (i != -1):
            i = i - 1
            keyoutput = '-%s' % keyoutput
    return keyoutput


def find_digital_key(fp, maxline=0):
    SYNC, SECTION, KEY, CONT = range(4)
    state = SYNC
    sections = dict()
    value = None
    for n, line in enumerate(fp, start=1):
        line = line.strip()
        print('Line %8d' % n, end='\r')
        if not line:
            continue
        try:
            if state not in (CONT, ):
                if line.startswith('[') and line.endswith(']'):
                    subsections = line[1:-1].split('\\')
                    section = sections
                    for subsect in subsections:
                        section.setdefault(subsect, {})
                        section = section[subsect]
                    state = SECTION
                    continue
                if line.startswith('"'):
                    key, value = line.split('=', 1)
                    key = key.strip('"')
                    if line.endswith('\\'):
                        value = value[:-1]
                        state = CONT
                    else:
                        state = KEY
            else:
                value = ''.join((value, line))
                if not line.endswith('\\'):
                    state = KEY
                else:
                    value = value[:-1]
                    state = CONT
            if state == KEY:
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif ':' in value:
                    kind, value = value.split(':', 1)
                    kind = kind.lower()
                    if kind == 'dword':
                        value = int(value, 16)
                    elif kind.split('(')[0] == 'hex':
                        value = value.replace(',', '')
                        value = bytearray().fromhex(value)
                    else:
                        raise ValueError('Unknown kind: %s' % kind)
                section[key] = value
                value = None
        except ValueError as e:
            print('')
            raise ValueError('Error @ %d: %s "%s"' % (n, str(e), value))
        except TypeError as e:
            print('')
            print('Discard key %s' % key)
        if maxline and n > maxline:
            break
    print(' ' * 20, end='\r')
    return sections


def main(filename):
    with open(filename, 'rt', encoding='utf16') as regfp:
        sections = find_digital_key(regfp, maxline=500)
    key = 'HKEY_LOCAL_MACHINE:SOFTWARE:Microsoft:Windows NT:'\
          'CurrentVersion:DigitalProductId'
    digikey = sections
    for k in key.split(':'):
        digikey = digikey[k]
    print (hex2key(digikey))


if __name__ == '__main__':
    main(sys.argv[1])
