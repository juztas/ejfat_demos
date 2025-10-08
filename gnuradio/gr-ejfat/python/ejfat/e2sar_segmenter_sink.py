#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 gr-ejfat author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr
import e2sar_py

class e2sar_segmenter_sink(gr.sync_block):
    """
    Sink block that sends complex vectors using E2SAR Segmenter.

    This block takes complex64 vectors from GNU Radio and sends them via
    the E2SAR data plane segmenter for transmission over EJFAT.

    Args:
        uri: EJFAT URI string (e.g., "ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1:19522")
        data_id: Data identifier (uint16)
        event_src_id: Event source identifier (uint32)
        vector_size: Size of input complex vectors (default: 1 for streaming samples)
        use_cp: Use control plane (default: False)
        mtu: Maximum transmission unit (default: 9000)
        rate_gbps: Target data rate in Gbps (default: 1.0)
    """
    def __init__(self, uri='', data_id=1, event_src_id=1, vector_size=1,
                 use_cp=False, mtu=9000, rate_gbps=1.0):
        gr.sync_block.__init__(self,
            name="e2sar_segmenter_sink",
            in_sig=[(np.complex64, vector_size)],
            out_sig=None)

        self.uri = uri
        self.data_id = data_id
        self.event_src_id = event_src_id
        self.vector_size = vector_size
        self.event_num = 0
        self.segmenter = None

        # Store configuration for initialization in start()
        self.use_cp = use_cp
        self.mtu = mtu
        self.rate_gbps = rate_gbps

    def start(self):
        """Initialize E2SAR segmenter when flowgraph starts"""
        try:
            # Create EJFAT URI
            ejfat_uri = e2sar_py.EjfatURI(uri=self.uri, tt=e2sar_py.EjfatURI.TokenType.instance)

            # Configure segmenter flags
            sflags = e2sar_py.DataPlane.Segmenter.SegmenterFlags()
            sflags.useCP = self.use_cp
            sflags.mtu = self.mtu
            sflags.rateGbps = self.rate_gbps
            sflags.syncPeriodMs = 1000
            sflags.syncPeriods = 5

            # Create segmenter
            self.segmenter = e2sar_py.DataPlane.Segmenter(
                ejfat_uri, self.data_id, self.event_src_id, sflags)

            # Open and start segmenter
            res = self.segmenter.openAndStart()
            if res.has_error():
                print(f"Error starting E2SAR segmenter: {res.error().message}")
                return False

            print(f"E2SAR segmenter started: URI={self.uri}, data_id={self.data_id}, vector_size={self.vector_size}")
            return True

        except Exception as e:
            print(f"Error initializing E2SAR segmenter: {e}")
            return False

    def stop(self):
        """Stop E2SAR segmenter when flowgraph stops"""
        if self.segmenter:
            try:
                self.segmenter.stopThreads()
                print(f"E2SAR segmenter stopped. Total events sent: {self.event_num}")
            except Exception as e:
                print(f"Error stopping segmenter: {e}")
            self.segmenter = None
        return True

    def work(self, input_items, output_items):
        """Send complex vector samples via E2SAR segmenter"""
        if not self.segmenter:
            return len(input_items[0])

        in0 = input_items[0]

        try:
            # Each input vector becomes one event
            for vector in in0:
                # Convert complex64 to numpy array if not already
                if not isinstance(vector, np.ndarray):
                    vector = np.array(vector, dtype=np.complex64)

                # Send the vector as a numpy array
                nbytes = vector.nbytes
                res = self.segmenter.sendNumpyArray(vector, nbytes, self.event_num, self.data_id, 0)

                if res.has_error():
                    print(f"Error sending event {self.event_num}: {res.error().message}")
                else:
                    self.event_num += 1

        except Exception as e:
            print(f"Error in work function: {e}")

        return len(input_items[0])
