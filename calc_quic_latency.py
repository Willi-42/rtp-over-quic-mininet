#!/usr/bin/env python

import argparse
import json
from os import listdir
from os.path import isfile, join
import statistics
import numpy
from calc_ack_delay import get_all_qlogs

def get_timestamp(log, type) ->  dict[str, int]:
    ts = dict()
    ref_time = 0

    # get server recv ts
    for line in log:
        if ref_time == 0:
            d = json.loads(line)
            refString = d['trace']['common_fields']['reference_time']
            ref_time = int(float(refString))

        if type in line:
            d = json.loads(line)

            got_datagram = False

            for frame in d['data']['frames']:
                if frame["frame_type"] == "datagram":
                    got_datagram = True

            if not got_datagram:
                continue

            newTs = ref_time + int(float(d['time']))

            header =  d['data']['header']
            pn = header['packet_number']
            ts[pn] = newTs

    return ts

def get_latency_of_file(server_log, client_log):
    server_received_ts = get_timestamp(server_log, 
                                       '"name":"transport:packet_received"')
    client_send_ts = get_timestamp(client_log, 
                                       '"name":"transport:packet_sent"')
    drop_cnt = 0
    latencies = []
    for pn, sendTs in client_send_ts.items():
        if pn not in server_received_ts:
            drop_cnt += 1
            continue
        recvTs = server_received_ts[pn]
        latecny = recvTs - sendTs
        latencies.append(latecny)

    return latencies

def get_quic_latency(folder):
    latencies = []
    server_log = ""
    client_log = ""

    for file in listdir(folder): # find qlog file
        if (file.endswith("Server.qlog")):
            server_log = join(folder, file)
        if (file.endswith("Client.qlog")):
            client_log = join(folder, file)  

    with open(server_log) as slog:
        with open(client_log) as clog:
            latencies = get_latency_of_file(slog, clog)

    return latencies

def main():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument('--folder', default='', help='qlog file')

    args = parser.parse_args()

    latency = []

    for f_name in listdir(args.folder): # find testcase folders
        # check if subfolder
        if not isfile(join(args.folder, f_name)):
            folder = join(args.folder, f_name)
            latency.extend(get_quic_latency(folder))


    avg = statistics.mean(latency)
    tile = numpy.percentile(latency, 97)

    print('avg {:0.3f}; 97%-tile: {:0.3f}, max: {:0.3f}'
            .format(avg, tile, numpy.max(latency)))

if __name__ == "__main__":
    main()