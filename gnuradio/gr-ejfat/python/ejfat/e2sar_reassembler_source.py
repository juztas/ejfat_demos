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

class e2sar_reassembler_source(gr.sync_block):
    """
    Source block that receives complex vectors using E2SAR Reassembler.

    This block receives data via the E2SAR data plane reassembler and outputs
    complex64 vectors to GNU Radio.

    Args:
        uri: EJFAT URI string (e.g., "ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1")
        data_ip: Data plane IP address (e.g., "127.0.0.1")
        starting_port: Starting UDP port for receiving data
        vector_size: Size of output complex vectors (default: 1 for streaming samples)
        num_recv_threads: Number of receiver threads (default: 1)
        use_cp: Use control plane (default: False)
        with_lb_header: Expect load balancer header (default: True for testing without LB)
        event_timeout_ms: Event timeout in milliseconds (default: 5000)
    """
    def __init__(self, uri='', data_ip='127.0.0.1', starting_port=19522, vector_size=1,
                 num_recv_threads=1, use_cp=False, with_lb_header=True, event_timeout_ms=5000):
        gr.sync_block.__init__(self,
            name="e2sar_reassembler_source",
            in_sig=None,
            out_sig=[(np.complex64, vector_size)])

        self.uri = uri
        self.data_ip = data_ip
        self.starting_port = starting_port
        self.vector_size = vector_size
        self.num_recv_threads = num_recv_threads
        self.reassembler = None
        self.event_count = 0

        # Store configuration for initialization in start()
        self.use_cp = use_cp
        self.with_lb_header = with_lb_header
        self.event_timeout_ms = event_timeout_ms

    def start(self):
        """Initialize E2SAR reassembler when flowgraph starts"""
        try:
            # Create EJFAT URI
            ejfat_uri = e2sar_py.EjfatURI(uri=self.uri, tt=e2sar_py.EjfatURI.TokenType.instance)

            # Configure reassembler flags
            rflags = e2sar_py.DataPlane.Reassembler.ReassemblerFlags()
            rflags.useCP = self.use_cp
            rflags.withLBHeader = self.with_lb_header
            rflags.eventTimeout_ms = self.event_timeout_ms

            # Create reassembler
            self.reassembler = e2sar_py.DataPlane.Reassembler(
                ejfat_uri,
                e2sar_py.IPAddress.from_string(self.data_ip),
                self.starting_port,
                self.num_recv_threads,
                rflags)

            # Open and start reassembler
            res = self.reassembler.openAndStart()
            if res.has_error():
                print(f"Error starting E2SAR reassembler: {res.error().message}")
                return False

            print(f"E2SAR reassembler started: URI={self.uri}, data_ip={self.data_ip}:{self.starting_port}, vector_size={self.vector_size}")
            return True

        except Exception as e:
            print(f"Error initializing E2SAR reassembler: {e}")
            import traceback
            traceback.print_exc()
            return False

    def stop(self):
        """Stop E2SAR reassembler when flowgraph stops"""
        if self.reassembler:
            try:
                self.reassembler.stopThreads()
                print(f"E2SAR reassembler stopped. Total events received: {self.event_count}")
            except Exception as e:
                print(f"Error stopping reassembler: {e}")
            self.reassembler = None
        return True

    def work(self, input_items, output_items):
        """Receive complex vector samples via E2SAR reassembler"""
        out = output_items[0]
        noutput_items = len(out)

        if not self.reassembler:
            out[:] = 0
            return noutput_items

        try:
            items_produced = 0

            # Try to fill the output buffer with received events
            while items_produced < noutput_items:
                # Get an event as a 1D numpy array (non-blocking)
                recv_len, recv_array, event_num, data_id = self.reassembler.get1DNumpyArray(np.complex64().dtype)

                if recv_len == -2:
                    # Error receiving
                    break
                elif recv_len == -1:
                    # No message available
                    break
                elif recv_len > 0:
                    # Successfully received an event
                    self.event_count += 1

                    # Calculate how many vectors we received
                    num_samples = len(recv_array)
                    num_vectors = num_samples // self.vector_size

                    if num_vectors == 0:
                        # Not enough samples for even one vector
                        continue

                    # Reshape array into vectors
                    available_samples = num_vectors * self.vector_size
                    vectors = recv_array[:available_samples].reshape(num_vectors, self.vector_size)

                    # Copy vectors to output
                    vectors_to_copy = min(num_vectors, noutput_items - items_produced)
                    out[items_produced:items_produced + vectors_to_copy] = vectors[:vectors_to_copy]
                    items_produced += vectors_to_copy

                    if items_produced >= noutput_items:
                        break

            # If we didn't get any data, output zeros to avoid blocking the flowgraph
            if items_produced == 0:
                out[:] = 0
                return noutput_items

            # If we didn't fill the entire output buffer, zero the rest
            if items_produced < noutput_items:
                out[items_produced:] = 0

            return noutput_items

        except Exception as e:
            print(f"Error in work function: {e}")
            import traceback
            traceback.print_exc()
            out[:] = 0
            return noutput_items
