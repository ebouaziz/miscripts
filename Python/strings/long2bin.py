#!/usr/bin/env python2.7

# Deal with long integer encoded as binary strings

# sample long integer
l = (2**32-2)*(2**32-3)*(2**32-7)
# input long integer
print "%x" % l

# create a list
ls = []
while l:
    # extract each byte of the long integer and store it into the list
    bot = l&((1<<8)-1)
    l >>= 8
    ls.append(bot)
# pad the list up to 32 items
ls.extend([0]*(32-len(ls)))
# reverse the list
ls.reverse()
# build up output data (signature)
binstring = [chr(c) for c in ls]

# output debug string
print "(%d) %s" % (len(binstring), ''.join('%x' % c for c in ls))
