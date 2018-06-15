#!/usr/bin/env python3

from os.path import join as joinpath
from time import monotonic as now


class CurrentTracker:

    HWMON = '/sys/bus/i2c/devices/0-0041/hwmon/hwmon0'

    CONFIG = {
        'ch2_active': False,
        'ch3_active': False,
        'avg_mode': 7,
        'volt_conv_time': 0,
        'shunt_conv_time': 7,
        'shunt1_resistor': 0.1*1e6,
    }

    def __init__(self):
        pass

    def configure(self):
        for config in self.CONFIG:
            with open(joinpath(self.HWMON, config), 'wb') as cfgfp:
                value = int(self.CONFIG[config])
                print("%s = %d" % (config, value))
                cfgfp.write(b'%d' % value)

    def capture(self, path):
        current_source = joinpath(self.HWMON, 'curr1_input')
        voltage_source = joinpath(self.HWMON, 'in1_input')
        with open(path, 'wt') as outfp:
            start_time = now()
            timeout = start_time + 60
            while True:
                with open(current_source, 'rt') as curfp:
                    mamps = int(curfp.read().strip())
                    timestamp = now()
                with open(voltage_source, 'rt') as curfp:
                    mvolts = int(curfp.read().strip())
                print('%.6f,%d,%d' % ((timestamp-start_time), mamps, mvolts),
                      file=outfp)
                if timestamp > timeout:
                    break

def main():
    tracker = CurrentTracker()
    tracker.configure()
    tracker.capture('ina3221.csv')


if __name__ == '__main__':
    main()

