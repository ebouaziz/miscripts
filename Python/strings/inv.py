#!/usr/bin/env python2.7

# Play with strings

def testme(si):
    """Revert a string, filtering out the vowel characters"""
    so = ''.join([c for c in reversed(si) if c.lower() not in 'aeiouy'])
    return so, len(so)

s = 'SylvAin DelislE'
print s
print testme(s)
