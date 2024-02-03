#!/usr/bin/env python

import argparse
import json
import numpy
from os import listdir
from os.path import isfile, join
import statistics
import pandas as pd
import matplotlib.pyplot as plt

from plot import read_rtp, read_capacity, read_cc_qdelay, read_rtp_latency, read_cc_all

def get_latency(folder, basetime, plot):
    latency = read_rtp_latency(
                folder + "/sender_rtp.log",
                folder + "/receiver_rtp.log",
                basetime,
            )
    if (plot):
        latency.plot(y='diff', title='latency')
        plt.savefig(join(folder, 'latency.png'))

    res = []
    for index, row in latency.iterrows():
       latency_ms = row['diff'] * 1000
       res.append(latency_ms)

    return res

def get_qdelay(folder, basetime):
    # get bandwidth
    q_delay = read_cc_qdelay(
                folder + "/cc.log",
                basetime,
            )
    res = []
    for index, row in q_delay.iterrows():
        q_delay_ms = row['queue delay'] * 1000
        res.append(q_delay_ms)

    return res

def calc_utilization(folder, basetime):
    # get bandwidth
    receiver_rtp = read_rtp(
                folder + "/receiver_rtp.log",
                basetime,
            )
    
    # get capacity
    capacity_raw = read_capacity(
                folder + "/capacity.log",
                basetime,
            )
    
    capacity = dict()
    for index, row in capacity_raw.iterrows():
        capacity[index.round(freq='S')] = row['bandwidth']

    results = []
    cur_bandwidth = 1000000 # TODO: rtp data sometimes starts at :01
    i = 0
    
    for index, row in receiver_rtp.iterrows():
        if index.round(freq='S') in capacity:
            cur_bandwidth = capacity[index.round(freq='S')]

        if (i <= 20): # skip startup phase
            i+= 1
            continue

        results.append(row['rate']/cur_bandwidth)

    return results

def main():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument('--folder', default='', help='base folder')
    parser.add_argument('--plot', action='store_true',
                        help='plots a boxplot')
    parser.add_argument('--latex', action='store_true',
                        help='prints res in latex table row')

    args = parser.parse_args()

    print("test;utilization")

    for testcase in range(8): # per test case
        utilization_res = []
        qdelay_res = []
        latency_res = []
        count = 0

        for f_name in listdir(args.folder): # find all reptitions

            # check if it is a folder and has correct name
            if not isfile(join(args.folder, f_name)) and f_name.startswith(str(testcase)):
                count += 1
                folder = join(args.folder, f_name)

                # get base time
                with open(folder + "/config.json") as f:
                    d = json.load(f)
                    basetime = d['basetime']

                utilization = calc_utilization(folder, basetime)
                qdelay = get_qdelay(folder, basetime)
                latency= get_latency(folder, basetime, args.plot)

                print('{:s}; {:0.2f}'
                      .format(f_name, statistics.mean(utilization)))

                utilization_res.extend(utilization)
                qdelay_res.extend(qdelay)
                latency_res.extend(latency)

                if (args.plot):
                    data = read_cc_all(folder + "/cc.log", basetime)

                    data.plot(y='bytesInFlightLog', title='bytesInFligth')
                    plt.savefig(join(folder, 'bytesInFligth.png'))

                    data.plot(y='cwnd', title='cwnd')
                    plt.savefig(join(folder, 'cwnd.png'))

                    data.plot(y='queue delay', title='queue delay')
                    plt.savefig(join(folder, 'qdelay.png'))

        if (count > 0):
            print('---')
            print('test {:d}, {:d} reps'.format(testcase, count))

            util_avg = statistics.mean(utilization_res)
            util_median = statistics.median_high(utilization_res)
            util_stdev = numpy.std(utilization_res)

            qdelay_avg = statistics.mean(qdelay_res)
            qdelay_stdev = numpy.std(qdelay_res)
            qdelay_ptile = numpy.percentile(qdelay_res, 97)

            latency_avg = statistics.mean(latency_res)
            latency_stdev = numpy.std(latency_res)
            latency_ptile = numpy.percentile(latency_res, 97)

            print('utilization: avg: {:0.4f}; median: {:0.4f}; stdev {:0.4f}'
                  .format(util_avg, util_median, util_stdev))

            print('qdaly:   avg: {:0.2f}; stdev: {:0.2f}; 97%-tile: {:0.2f}'
                  .format(qdelay_avg, qdelay_stdev, qdelay_ptile))

            print("latency: avg: {:0.2f}; stdev: {:0.2f}; 97%-tile {:0.2f}"
                  .format(latency_avg, latency_stdev, latency_ptile))

            if (args.latex):
                print("? & {:0.1f}\% & {:0.1f} & {:0.1f} & {:0.1f} & {:0.1f} & {:0.1f} & {:0.1f} & {:0.1f}\\\\"
                      .format(util_avg*100, util_stdev*100, latency_avg, latency_stdev, latency_ptile,
                              qdelay_avg, qdelay_stdev, qdelay_ptile))


if __name__ == "__main__":
    main()