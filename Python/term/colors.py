#!/usr/bin/env python2.7

# Generate not so pseudo random colors for use with a 256-color terminal

from math import floor

COLORS = (0x94, 0xcc, 0x5d, 0x2c, 0x76, 0xd1, 0x81, 0x27, 0x53, 0xd6,
          0xa3, 0x21, 0x30, 0xb8, 0xc6, 0x63, 0x31, 0x9a, 0xd0, 0xa4,
          0x21, 0x30, 0xb8, 0xc7, 0x3f, 0x31, 0x9a, 0xcb, 0x5d, 0x2c,
          0x76, 0xd0, 0xa4, 0x27, 0x53, 0xd6)


def hsv2rgb(h, s, v):
    h = float(h)
    s = float(s)
    v = float(v)
    h60 = h / 60.0
    h60f = floor(h60)
    hi = int(h60f) % 6
    f = h60 - h60f
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r, g, b = 0, 0, 0
    if hi == 0:
        r, g, b = v, t, p
    elif hi == 1:
        r, g, b = q, v, p
    elif hi == 2:
        r, g, b = p, v, t
    elif hi == 3:
        r, g, b = p, q, v
    elif hi == 4:
        r, g, b = t, p, v
    elif hi == 5:
        r, g, b = v, p, q
    #  r, g, b = int(r * 255), int(g * 255), int(b * 255)
    return r, g, b


def rgb2hsv(r, g, b):
    # r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx-mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g-b)/df) + 360) % 360
    elif mx == g:
        h = (60 * ((b-r)/df) + 120) % 360
    elif mx == b:
        h = (60 * ((r-g)/df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = df/mx
    v = mx
    return h, s, v


#print len(COLORS)
#M = 6.0
#for color in COLORS:
#    # c == 16 + 36 x r + 6 x g + b
#    c = color-16
#    r = (c//36)/M
#    c %= 36
#    g = (c//6)/M
#    c %= 6
#    b = c/M
#    h, s, v = rgb2hsv(r, g, b)
#    r2, g2, b2 = hsv2rgb(h, s, v)
#    print "%3d : %.3f %.3f %.3f -> %.0f %.3f %.3f" % (color, r, g, b, h, s, v)
#    print "    : %.3f %.3f %.3f" % (r2, g2, b2)

STEPS = 11
FULL = 360
LOOPS = 2
inc = FULL/STEPS
for loop in range(LOOPS):
    init = float(loop)/LOOPS
    c = init*inc
    for s in range(STEPS):
        print c
        c += inc
