#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
file: streamer.py
This file is part of nfstream.

Copyright (C) 2019-20 - Zied Aouini <aouinizied@gmail.com>

nfstream is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

nfstream is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with nfstream.
If not, see <http://www.gnu.org/licenses/>.
"""
from .cache import NFCache
from .observer import NFObserver
from threading import Thread
from random import randrange
import socket
import zmq
import sys


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


class NFStreamer(object):
    """ Network Flow Streamer """

    def __init__(self, source=None, snaplen=65535, idle_timeout=30, active_timeout=300,
                 plugins=(), dissect=True, max_tcp_dissections=10, max_udp_dissections=16):
        self._nroots = 512

        valid_port_candidate_found = False
        while not valid_port_candidate_found:
            candidate = randrange(49152, 65536, 1)
            if not port_in_use(candidate):
                valid_port_candidate_found = True
                self.sock_name = "tcp://127.0.0.1:{}".format(candidate)
        try:
            self.cache = NFCache(observer=NFObserver(source=source, snaplen=snaplen, nroots=self._nroots),
                                 idle_timeout=idle_timeout,
                                 active_timeout=active_timeout,
                                 nroots=self._nroots,
                                 user_plugins=plugins,
                                 dissect=dissect,
                                 max_tcp_dissections=max_tcp_dissections,
                                 max_udp_dissections=max_udp_dissections,
                                 sock_name=self.sock_name)
        except OSError as ose:
            sys.exit(ose)
        except ValueError as ve:
            sys.exit(ve)
        except TypeError as te:
            sys.exit(te)
        self._producer = Thread(target=self.cache.run, args=())
        self._producer.daemon = True  # demonize thread
        self._stopped = False

    def __iter__(self):
        self._consumer = zmq.Context().socket(zmq.PULL)
        try:
            self._producer.start()
            self._consumer.connect(self.sock_name)
            while True:
                try:
                    flow = self._consumer.recv_pyobj()
                    if flow is None:
                        break
                    else:
                        yield flow
                except KeyboardInterrupt:
                    if not self._stopped:
                        self._stopped = True
                        self.cache.stopped = True
        except RuntimeError:
            return None




