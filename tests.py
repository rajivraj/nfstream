#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
file: tests.py
This file is part of nfstream.

Copyright (C) 2019-20 - Zied Aouini <aouinizied@gmail.com>

nfstream is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

nfstream is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with nfstream.
If not, see <http://www.gnu.org/licenses/>.
"""

import unittest
from nfstream import NFStreamer, NFPlugin
import os
import csv


def get_files_list(path):
    files = []
    for r, d, f in os.walk(path):
        for file in f:
            if '.pcap' in file:
                files.append(os.path.join(r, file))
    return files


def get_app_dict(path):
    with open(path) as csvfile:
        reader = csv.DictReader(csvfile)
        app = {}
        for row in reader:
            try:
                app[row['ndpi_proto']] += int(row['s_to_c_bytes']) + int(row['c_to_s_bytes'])
            except KeyError:
                app[row['ndpi_proto']] = 0
                app[row['ndpi_proto']] += int(row['s_to_c_bytes']) + int(row['c_to_s_bytes'])
    return app


def build_ground_truth_dict(path):
    list_gt = get_files_list(path)
    ground_truth = {}
    for file in list_gt:
        ground_truth[file.split('/')[-1]] = get_app_dict(file)
    return ground_truth


class TestMethods(unittest.TestCase):
    def test_no_unknown_protocols_without_timeouts(self):
        files = get_files_list("tests/pcap/")
        ground_truth_ndpi = build_ground_truth_dict("tests/result/")
        self.maxDif = None
        print("----------------------------------------------------------------------")
        print(".Testing on {} applications:".format(len(files)))
        for test_file in files:
            streamer_test = NFStreamer(source=test_file, idle_timeout=60000, active_timeout=60000)
            test_case_name = test_file.split('/')[-1]
            print(test_case_name)
            result = {}
            for flow in streamer_test:
                if flow.application_name != 'Unknown':
                    try:
                        result[flow.application_name] += flow.total_bytes
                    except KeyError:
                        result[flow.application_name] = flow.total_bytes
            print(result)
            self.assertEqual(result, ground_truth_ndpi[test_case_name])
            del streamer_test
            print('PASS.')

    def test_expiration_management(self):
        print("\n----------------------------------------------------------------------")
        print(".Testing Streamer expiration management:")
        streamer_test = NFStreamer(source='tests/pcap/facebook.pcap', active_timeout=0)
        flows = []
        for flow in streamer_test:
            flows.append(flow)
        self.assertEqual(len(flows), 60)
        print('PASS.')

    def test_flow_str_representation(self):
        print("\n----------------------------------------------------------------------")
        print(".Testing Flow string representation:")
        streamer_test = NFStreamer(source='tests/pcap/facebook.pcap')
        flows = []
        for flow in streamer_test:
            flows.append(flow)
        del streamer_test
        print(flows[0])
        print('PASS.')

    def test_unfound_device(self):
        print("\n----------------------------------------------------------------------")
        print(".Testing unfoud device")
        try:
            streamer_test = NFStreamer(source="inexisting_file.pcap")
        except SystemExit:
            print("PASS.")

    def test_noroot_live(self):
        print("\n----------------------------------------------------------------------")
        print(".Testing live capture (noroot)")
        try:
            streamer_test = NFStreamer(idle_timeout=0)
        except SystemExit:
            print("PASS.")

    def test_user_plugins(self):
        class feat_1(NFPlugin):
            def on_update(self, obs, entry):
                if entry.total_packets == 1:
                    entry.feat_1 == obs.length

        print("\n----------------------------------------------------------------------")
        print(".Testing adding user plugins.")
        streamer_test = NFStreamer(source='tests/pcap/facebook.pcap', plugins=[feat_1()])
        for flow in streamer_test:
            if flow.id == 0:
                self.assertEqual(flow.feat_1, 0)
            else:
                self.assertEqual(flow.feat_1, 0)
        del streamer_test
        print('PASS.')


if __name__ == '__main__':
    unittest.main()
