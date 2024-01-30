#!/usr/bin/env python

import argparse
import json
import numpy
from os import listdir
from os.path import isfile, join
import statistics
import pandas as pd
import matplotlib.pyplot as plt

from plot import read_rtp, read_capacity, read_cc_qdelay, read_rtp_latency

def get_latency(folder, basetime):
    latency = read_rtp_latency(
                folder + "/sender_rtp.log",
                folder + "/receiver_rtp.log",
                basetime,
            )
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

    res = statistics.mean(results)

    return res

def main():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument('--folder', default='', help='base folder')
    parser.add_argument('--plot', action='store_true',
                        help='plots a boxplot')

    args = parser.parse_args()

    print("test;utilization")

    for testcase in range(8): # per test case
        results = []
        qdelay_res = []
        latency_res = []
        count = 0

        for f in listdir(args.folder): # find all reptitions

            # check if it is a folder and has correct name
            if not isfile(join(args.folder, f)) and f.startswith(str(testcase)):
                count += 1
                folder = join(args.folder, f)

                # get base time
                with open(folder + "/config.json") as f:
                    d = json.load(f)
                    basetime = d['basetime']

                res = calc_utilization(folder, basetime)
                qdelay = get_qdelay(folder, basetime)
                latency= get_latency(folder, basetime)

                print('{:d};{:0.2f}'.format(count, res))

                results.append(res)
                qdelay_res.extend(qdelay)
                latency_res.extend(latency)

        if (count > 0):
            print('---')
            print('test {:d}, {:d} reps'.format(testcase, count))

            avg = statistics.mean(results)
            median = statistics.median_high(results)
            stdev = numpy.std(results)

            print('utilization: avg: {:0.4f}; median: {:0.4f}; stdev {:0.4f}'
                  .format(avg, median, stdev))

            print('qdaly:   avg: {:0.2f}; stdev: {:0.2f}; 97%-tile: {:0.2f}'.format(statistics.mean(qdelay_res),
                  numpy.std(qdelay_res), numpy.percentile(qdelay_res, 97)))

            print("latency: avg: {:0.2f}; 97%-tile {:0.2f}".format(statistics.mean(latency_res),
                  numpy.percentile(latency_res, 97)))

            # boxplot
            if (args.plot):
                boxplot_data = pd.DataFrame(latency_res, columns=['bw'])
                boxplot_data['bw'].plot(kind='box', title='utilization')
                plt.savefig(join(args.folder, 'boxplot.png'))
                # plt.show() 
 

if __name__ == "__main__":
    main()