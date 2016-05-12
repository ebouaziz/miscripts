#!/usr/bin/env python3

# Generate ADSL modem bit allocation map as SVG, from CPE data

import pygal
import re
import os
from telnetlib import Telnet

# /usr/sbin/dsl_cpe_pipe.sh g997bang 0

def normalise(s):
    return s.replace(b'\r',b'').replace(b'\n', b' ').replace(b'  ', b' ')

def extract(s):
    s = str(s, 'utf8')
    start = s.find('"')
    end = s.find('"', start+1)
    if end > 0:
        s = s[start+1:end-1].strip()
    else:
        s = s[start+1:].strip()
    # cre = re.compile(r'(?i)\((\d+),([\da-f]+)\)')
    cre = re.compile(r'(?i)([\da-f]+)')
    values = [int(val, 16) for val in cre.findall(s)]
    return values

def merge(a, b):
    a.extend([None] * (len(b) - len(a)))
    m = [x is not None and x or y for x,y in zip(a,b)]
    return m

def retrieve(host, user='root', password=''):
    tn = Telnet(host)
    # user = bytes(user, 'utf8')
    # tn.set_debuglevel(255)
    tn.read_until(b'login: ')
    tn.write(bytes('%s\r\n' % user, 'utf8'))
    tn.read_until(b'Password: ')
    tn.write(bytes('%s\r\n' % password, 'utf8'))
    tn.read_until(bytes('%s@gateway:~# ' % user, 'utf8'))
    tn.write(b'/usr/sbin/dsl_cpe_pipe.sh g997bansg 0\r\n')
    bits_up = tn.read_until(bytes('%s@gateway:~# ' % user, 'utf8'))
    tn.write(b'/usr/sbin/dsl_cpe_pipe.sh g997bansg 1\r\n')
    bits_down = tn.read_until(bytes('%s@gateway:~# ' % user, 'utf8'))
    #tn.write(b'/usr/sbin/dsl_cpe_pipe.sh g997gansg 0\r\n')
    #gain_up = tn.read_until(bytes('%s@gateway:~# ' % user, 'utf8'))
    #tn.write(b'/usr/sbin/dsl_cpe_pipe.sh g997gansg 1\r\n')
    #gain_down = tn.read_until(bytes('%s@gateway:~# ' % user, 'utf8'))
    tn.write(b'/usr/sbin/dsl_cpe_pipe.sh g997sansg 1\r\n')
    snr_down = tn.read_until(bytes('%s@gateway:~# ' % user, 'utf8'))
    tn.write(b'exit\r\n')
    bits_up = extract(normalise(bits_up))
    bits_down = extract(normalise(bits_down))
    bits = merge(bits_up, bits_down)
    snr_down = [x != 255 and x/2.55 or 0 for x in extract(normalise(snr_down))]
    #gain_up = extract(normalise(gain_up))
    #gain_down = extract(normalise(gain_down))
    #gain = merge(gain_up, gain_down)
    return bits, [], snr_down

def generate_bits(filename, bits):
    base = 4.3125
    chart = pygal.Bar(style=pygal.style.LightSolarizedStyle,
                      height=200,
                      range=(0.0, 16.0))
    chart.title = 'ADSL bit allocation'
    chart.x_labels = [not (x % 16) and '%.0fk' % (x*base) or ''
                      for x in range(257)]
    chart.add('Upload', bits[:32])
    chart.add('Download', [0] * 32 + bits[32:])
    chart.render_to_file(filename)

def generate_snr(filename, snr):
    base = 4.3125
    chart = pygal.Bar(#style=pygal.style.LightSolarizedStyle,
                      height=200,
                      #range=(0.0, 16.0)
                      )
    chart.title = 'ADSL SNR'
    chart.x_labels = [not (x % 16) and '%.0fk' % (x*base) or ''
                      for x in range(257)]
    chart.add('     SNR', snr)
    chart.render_to_file(filename)

def generate_html(filename):
    html = """<!DOCTYPE html>
<html>
  <head>
  </head>
  <body>
    <figure>
      <embed type="image/svg+xml" src="bits.svg" />
    </figure>
    <figure>
      <embed type="image/svg+xml" src="snr.svg" />
    </figure>
  </body>
</html>
    """
    with open(filename, 'wt') as out:
        out.write(html)

if __name__ == '__main__':
    passwd = os.getenv('ADSLPASS', None)
    if passwd is None:
        raise AssertionError('No passwd')
    bits, gain, snr = retrieve('192.168.83.1', 'root', passwd)
    generate_html('output.html')
    generate_bits('bits.svg', bits)
    generate_snr('snr.svg', snr)
