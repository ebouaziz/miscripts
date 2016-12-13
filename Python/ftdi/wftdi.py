#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Web antenna selector"""

# Dependencies:
#   - pyserial (tested with 3.0)
#   - pyusb    (tested with 1.0)
#   - pyftdi   (tested with 0.13.2)
#   - cherrypy (tested with 7.0)
#   - jinja    (tested with 2.8)


import cherrypy
import os.path
import sys
from argparse import ArgumentParser
from collections import OrderedDict
from jinja2 import Environment, FileSystemLoader
from pyftdi.gpio import GpioController
from pyftdi.usbtools import UsbTools
from threading import Timer


class Root(object):

    PREFIX = 'ant'
    DEVICE = 0x6001
    ANTENNAS = {
        900: (4, 500),
        # 2450: (16, 500)
    }

    def __init__(self):
        ldir = os.path.dirname(__file__)
        self.env = Environment(loader=FileSystemLoader(ldir))
        self._antennas = {k: 1 for k in self.ANTENNAS}
        self._delays = {k: self.ANTENNAS[k][1] for k in self.ANTENNAS}
        self._ftdis = {k: None for k in self.ANTENNAS}
        self._bailout = False
        self._timers = {}
        self._started = False
        self._resume = True
        cherrypy.engine.subscribe('stop', self._stop)

    @cherrypy.expose
    def index(self, k='', v=''):
        if self._bailout:
            sys.exit(0)
        if k == 'restart':
            self._bailout = True
            raise cherrypy.HTTPRedirect("/")
        for ant in self._timers:
            self._timers[ant].cancel()
        self._timers = {}
        return self._generate()

    @cherrypy.expose
    def select(self, k='', v=''):
        if v == 'auto':
            return
        if k:
            ant = int(k.split('_')[-1])
            self._stop_autoswitch(ant)
            value = int(v)
            self._antennas[ant] = value
            self._update_antenna(ant)

    @cherrypy.expose
    def autoswitch(self, k='', v=''):
        ant = int(k.split('_')[-1])
        if ant in self._timers:
            self._timers[ant].cancel()
            del self._timers[ant]
        delay = int(v)
        self._delays[ant] = delay
        interval = float(int(v)/1000.0)
        timer = Timer(interval, self._switch_antenna, args=(ant, interval))
        self._timers[ant] = timer
        timer.start()

    @cherrypy.expose
    def status(self):
        if not self._started:
            return ''
        return not all([bool(self._ftdis[band]) for band in self.ANTENNAS]) \
            and 'No FTDI device' or 'Ok'

    def _stop_autoswitch(self, ant):
        if ant in self._timers:
            self._timers[ant].cancel()
            del self._timers[ant]

    def _switch_antenna(self, ant, interval):
        self._antennas[ant] = (self._antennas[ant] + 1) % self.ANTENNAS[ant][0]
        self._update_antenna(ant)
        if self._resume:
            timer = Timer(interval, self._switch_antenna, args=(ant, interval))
            self._timers[ant] = timer
            timer.start()

    def _update_antenna(self, ant):
            value = self._antennas[ant]
            # cherrypy.log('Update ant: %d, value %d' % (ant, value))
            try:
                self._connect()
                self._ftdis[ant].write_port(value)
            except Exception as e:
                cherrypy.log('FTDI Error: %s (%d MHz)' % (str(e), ant))
                self._ftdis[ant] = False

    def _generate(self):
        kwargs = {'antennas': OrderedDict(),
                  'antcount': len(self.ANTENNAS)}
        for band in reversed(sorted(list(self.ANTENNAS))):
            count = self.ANTENNAS[band][0]
            antname = '%s_%d' % (self.PREFIX, band)
            antenna = kwargs['antennas'][antname] = {}
            antenna['band'] = band
            antenna['ids'] = list(range(count))
            antenna['count'] = count
            antenna['group'] = 4
            antenna['sel'] = self._antennas[band]
            antenna['delay'] = self._delays[band]
        tmpl = self.env.get_template('index.html')
        return tmpl.render(**kwargs)

    def _connect(self):
        self._started = True
        for port, ant in enumerate(sorted(self.ANTENNAS), start=1):
            if self._ftdis[ant]:
                continue
            try:
                serial = os.environ.get('FTDI%d' % ant, None)
                gpio = GpioController()
                cherrypy.log("Open interface %s" % port)
                gpio.open(vendor=0x403, product=self.DEVICE, interface=port,
                          serial=serial, direction=0xFF)
                gpio.read_port()
                self._ftdis[ant] = gpio
            except Exception as e:
                cherrypy.log("Failed interface %s %s" % (port, e))
                self._ftdis[ant] = None
                cherrypy.log('FTDI Error: %s (%s)' % (str(e), serial))
                UsbTools.flush_cache()

    def _stop(self):
        self._resume = False


def main():
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 8080})

    current_dir = os.path.dirname(os.path.abspath(__file__))
    conf = {'/js': {'tools.staticdir.on': True,
                    'tools.staticdir.dir': os.path.join(current_dir, 'js')}}
    cherrypy.quickstart(Root(), '/', config=conf)


if __name__ == '__main__':
    argparser = ArgumentParser(description=sys.modules[__name__].__doc__)
    argparser.parse_args()
    main()
