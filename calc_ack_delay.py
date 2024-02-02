#!/usr/bin/env python

import argparse
import json
from os import listdir
from os.path import isfile, join
import statistics
import numpy

def get_ack_delay(file):
    ack_delays = []
    for line in file:
        if '"name":"transport:packet_sent","data"' in line:
            d = json.loads(line)
            for i in d['data']['frames']:
                if i["frame_type"] == "ack" and "ack_delay" in i:
                    ack_delays.append(i["ack_delay"])

    return ack_delays



def main():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument('--folder', default='', help='qlog file')

    args = parser.parse_args()
    ack_delays = []

    for f_name in listdir(args.folder): # find all reptitions

        # check if it is a folder and has correct name
        if not isfile(join(args.folder, f_name)):
            folder = join(args.folder, f_name)

            for file in listdir(folder): # find qlog file
                if (file.endswith("Server.qlog")):
                    with open(join(folder, file)) as f:
                        ack_delays.extend(get_ack_delay(f))


    avg = statistics.mean(ack_delays)
    tile = numpy.percentile(ack_delays, 97)

    print('avg {:0.3f}; 97%-tile: {:0.3f}, max: {:0.3f}'
            .format(avg, tile, numpy.max(ack_delays)))

if __name__ == "__main__":
    main()