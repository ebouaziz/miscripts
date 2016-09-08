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


class Root(object):

    PREFIX = 'ant'
    ANTENNAS = {900: (4,),
                2450: (16,)}

    def __init__(self):
        ldir = os.path.dirname(__file__)
        self.env = Environment(loader=FileSystemLoader(ldir))
        self._antennas = {'%s%d' % (self.PREFIX, k): 1
                          for k in self.ANTENNAS}
        self._bailout = False
        self._ftdis = {k: None for k in self.ANTENNAS}

    @cherrypy.expose
    def index(self, k='', v=''):
        if self._bailout:
            sys.exit(0)
        if k == 'restart':
            self._bailout = True
            raise cherrypy.HTTPRedirect("/")

        if k:
            self._antennas[k] = int(v)
            ant = int(k.split('_')[0].replace(self.PREFIX, ''))

            try:
                self._connect()
                self._ftdis[ant].write_port(self._antennas[k])
            except Exception as e:
                cherrypy.log('FTDI Error: %s (%d MHz)' % (str(e), ant))
                self._ftdis[ant] = False

        kwargs = {'antennas': OrderedDict()}
        for band in reversed(sorted(list(self.ANTENNAS))):
            count, = self.ANTENNAS[band]
            antname = '%s%d' % (self.PREFIX, band)
            antenna = kwargs['antennas'][antname] = {}
            antenna['band'] = band
            antenna['ids'] = list(range(count))
            antenna['count'] = count
            antenna['group'] = 4
            antenna['status'] = bool(self._ftdis[band])
            antenna['sel'] = self._antennas[antname]

        #from pprint import pprint
        #pprint(kwargs)
        tmpl = self.env.get_template('index.html')
        return tmpl.render(**kwargs)

    def _connect(self):
        for port, ant in enumerate(sorted(self.ANTENNAS), start=1):
            if self._ftdis[ant]:
                continue
            try:
                serial = os.environ.get('FTDI%d' % ant, None)
                gpio = GpioController()
                gpio.open(vendor=0x403, product=0x6010, interface=port,
                          serial=serial, direction=0xFF)
                gpio.read_port()
                self._ftdis[ant] = gpio
            except Exception as e:
                self._ftdis[ant] = None
                cherrypy.log('FTDI Error: %s (%s)' % (str(e), serial))
                UsbTools.flush_cache()


def main():
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 8080})

    current_dir = os.path.dirname(os.path.abspath(__file__))
    conf = {'/js': {'tools.staticdir.on': True,
                    'tools.staticdir.dir': os.path.join(current_dir, 'js')}}
    cherrypy.quickstart(Root(), '/', config=conf)


if __name__ == '__main__':
    argparser = ArgumentParser(description=sys.modules[__name__].__doc__)
    argparser.add_argument('-u', '--ftdi900',
                           help='FTDI device name for 900 MHz')
    argparser.add_argument('-w', '--ftdi2450',
                           help='FTDI device name for 2.45 GHz')
    args = argparser.parse_args()
    os.environ['FTDI2450'] = args.ftdi2450 or ''
    os.environ['FTDI900'] = args.ftdi900 or ''
    main()
