#!/usr/bin/env python

import argparse
import json
from os import listdir
from os.path import isfile, join
import statistics
import pandas as pd
import matplotlib.pyplot as plt

from plot import read_rtp, read_capacity

def calc_utilization(folder, testcase):
    basetime = 0

    # get base time
    with open(folder + "/config.json") as f:
        d = json.load(f)
        basetime = d['basetime']

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

        # print('{}, {}, {}'.format(index, row['rate'], cur_bandwidth))

        results.append(row['rate']/cur_bandwidth)

    res = statistics.mean(results)
    print('{};{}'.format(testcase, res))

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
        count = 0

        for f in listdir(args.folder): # find all reptitions

            # check if it is a folder and has correct name
            if not isfile(join(args.folder, f)) and f.startswith(str(testcase)):
                count += 1
                res = calc_utilization(join(args.folder, f), count)
                results.append(res)

        if (count > 0):
            # avg
            avg = statistics.mean(results)
            print('test {} reps {}: {}'.format(testcase, count, avg))

            # mean
            mean = statistics.median_high(results)
            print("median: ", mean)

            # boxplot
            if (args.plot):
                boxplot_data = pd.DataFrame(results, columns=['bw'])
                boxplot_data['bw'].plot(kind='box', title='utilization')
                plt.savefig(join(args.folder, 'boxplot.png'))
                # plt.show() 
 

if __name__ == "__main__":
    main()