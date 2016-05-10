#!/usr/bin/env python3

# Experiment Unicode vertical bars in a terminal

from time import sleep

for y in range(10):
    for x in range(8):
        print(' ', chr(0x2588-x), '\r', end='')
        sleep(0.05)
    for x in range(8):
        print(' ', chr(0x2581+x), '\r', end='')
        sleep(0.05)
