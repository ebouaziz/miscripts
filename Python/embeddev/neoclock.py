#!/usr/bin/env python

# Map clock values to available register config

if __name__ == '__main__':
    for cpufreq in range(96, 204, 12):
        for prf_us in (100, 1000, 10000, 100000):
            period_scaler = int(cpufreq*prf_us)
            scaler_shift = 0
            period = period_scaler
            if period > 1<<16:
                period >>= 8
                scaler_shift += 8
            if period >= 1<<16:
                period >>=  8
                scaler_shift += 8
            print "%uMHz, prof %uus: %u: P: %u, S:%u" % \
                (cpufreq, prf_us, period_scaler, period, scaler_shift)
