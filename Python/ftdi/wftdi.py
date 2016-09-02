#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dependencies:
  - pyserial (tested with 3.0)
  - pyusb    (tested with 1.0)
  - pyftdi   (tested with 0.13.2)
  - cherrypy (tested with 7.0)
  - jinja    (tested with 2.8)
"""

import cherrypy
import os.path
import sys
from collections import OrderedDict
from jinja2 import Environment, FileSystemLoader
from pyftdi.gpio import GpioController, GpioException


class Root(object):

    PREFIX = 'gpio'
    PINS = 8

    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('.'))

        self._output = 0

    @cherrypy.expose
    def index(self, k='', v=''):
        checked = v == 'true'
        if k.startswith(self.PREFIX):
            ix = int(k.split('_', 1)[1])
            if checked:
                self._output |= (1 << ix)
            else:
                self._output &= ~(1 << ix)
        elif k == 'restart':
            sys.exit(0)
        # print('%08x' % self._output)
        try:
            self._connect()
            self._gpio.write_port(self._output)
        except Exception:
            self._gpio = False
        gpios = OrderedDict()
        for k in range(self.PINS):
            gpios['_'.join((self.PREFIX, '%d' % k))] = \
                 (self._output & (1 << k)) and 'checked' or 'unckecked'
        tmpl = self.env.get_template('index.html')
        return tmpl.render(gpios=gpios, ftdi=bool(self._gpio))

    def _connect(self):
        if self._gpio:
            return
        try:
            gpio = GpioController()
            gpio.open(vendor=0x403, product=0x6014, interface=1,
                      direction=(1 << self.PINS) - 1)
            self._gpio = gpio
        except Exception as e:
            cherrypy.log('FTDI Error: %s' % str(e))


cherrypy.config.update({'server.socket_port': 8080})

cherrypy.quickstart(Root())
