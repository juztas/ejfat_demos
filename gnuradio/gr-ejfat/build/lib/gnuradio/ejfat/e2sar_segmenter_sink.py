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
import time

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
        self.last_report_time = 0
        self.last_report_count = 0
        self.report_interval = 10.0  # Report every 10 seconds

        # Store configuration for initialization in start()
        self.use_cp = use_cp
        self.mtu = mtu
        self.rate_gbps = rate_gbps

    def start(self):
        """Initialize E2SAR segmenter when flowgraph starts"""
        try:
            print(f"\n{'='*60}")
            print(f"E2SAR SEGMENTER INITIALIZATION")
            print(f"{'='*60}")
            print(f"URI: {self.uri}")
            print(f"Data ID: {self.data_id}")
            print(f"Event Source ID: {self.event_src_id}")
            print(f"Vector Size: {self.vector_size}")
            print(f"Use CP: {self.use_cp}")
            print(f"MTU: {self.mtu}")
            print(f"Rate (Gbps): {self.rate_gbps}")

            # Create EJFAT URI
            print(f"\n[SEGMENTER] Creating EJFAT URI object...")
            ejfat_uri = e2sar_py.EjfatURI(uri=self.uri, tt=e2sar_py.EjfatURI.TokenType.instance)
            print(f"[SEGMENTER] EJFAT URI created successfully")

            # Print parsed URI components
            print(f"[SEGMENTER] URI Components:")
            print(f"[SEGMENTER] Full URI: {ejfat_uri.to_string()}")

            # Get control plane address (load balancer)
            cp_addr_res = ejfat_uri.get_cp_addr()
            if not cp_addr_res.has_error():
                cp_ip, cp_port = cp_addr_res.value()
                print(f"  - Control Plane (LB): {str(cp_ip)}:{cp_port}")
            else:
                print(f"  - Control Plane (LB): ERROR - {cp_addr_res.error().message}")

            # Get data plane address
            if ejfat_uri.has_data_addr_v4():
                data_addr_res = ejfat_uri.get_data_addr_v4()
                if not data_addr_res.has_error():
                    data_ip, data_port = data_addr_res.value()
                    print(f"  - Data Plane: {str(data_ip)}:{data_port}")
                else:
                    print(f"  - Data Plane: ERROR - {data_addr_res.error().message}")
            else:
                print(f"  - Data Plane: Not specified in URI")

            # Get sync address if present
            if ejfat_uri.has_sync_addr():
                sync_addr_res = ejfat_uri.get_sync_addr()
                if not sync_addr_res.has_error():
                    sync_ip, sync_port = sync_addr_res.value()
                    print(f"  - Sync: {str(sync_ip)}:{sync_port}")
            else:
                print(f"  - Sync: Not specified")

            # Configure segmenter flags
            print(f"\n[SEGMENTER] Configuring segmenter flags...")
            sflags = e2sar_py.DataPlane.Segmenter.SegmenterFlags()
            sflags.useCP = self.use_cp
            sflags.mtu = self.mtu
            sflags.rateGbps = self.rate_gbps
            sflags.syncPeriodMs = 1000
            sflags.syncPeriods = 5
            print(f"[SEGMENTER] Flags configured")

            # Create segmenter
            print(f"\n[SEGMENTER] Creating segmenter object...")
            self.segmenter = e2sar_py.DataPlane.Segmenter(
                ejfat_uri, self.data_id, self.event_src_id, sflags)
            print(f"[SEGMENTER] Segmenter object created")

            # Open and start segmenter
            print(f"\n[SEGMENTER] Calling OpenAndStart()...")
            res = self.segmenter.OpenAndStart()
            if res.has_error():
                error_msg = f"\n[SEGMENTER] *** FATAL ERROR during openAndStart() ***\n"
                error_msg += f"[SEGMENTER] Error code: {res.error().value}\n"
                error_msg += f"[SEGMENTER] Error message: {res.error().message}\n"
                error_msg += f"{'='*60}\n"
                error_msg += f"\nE2SAR Segmenter failed to start - STOPPING FLOWGRAPH\n"
                print(error_msg)
                raise RuntimeError(f"E2SAR Segmenter failed to start: {res.error().message}")

            print(f"[SEGMENTER] *** SUCCESSFULLY STARTED ***")
            print(f"{'='*60}\n")
            self.last_report_time = time.time()
            return True

        except RuntimeError:
            # Re-raise RuntimeError so it propagates up
            raise
        except Exception as e:
            error_msg = f"\n[SEGMENTER] *** FATAL EXCEPTION during initialization ***\n"
            error_msg += f"[SEGMENTER] Exception: {e}\n"
            print(error_msg)
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            print(f"\nE2SAR Segmenter initialization failed - STOPPING FLOWGRAPH\n")
            raise RuntimeError(f"E2SAR Segmenter initialization failed: {e}") from e

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
            for i, vector in enumerate(in0):
                # Convert complex64 to numpy array if not already
                if not isinstance(vector, np.ndarray):
                    vector = np.array(vector, dtype=np.complex64)

                # Send the vector as a numpy array
                nbytes = vector.nbytes
                res = self.segmenter.sendNumpyArray(vector, nbytes, self.event_num, self.data_id, 0)

                if res.has_error():
                    print(f"[SEGMENTER] *** ERROR sending event {self.event_num} ***")
                    print(f"[SEGMENTER] Error code: {res.error().value}")
                    print(f"[SEGMENTER] Error message: {res.error().message}")
                    print(f"[SEGMENTER] Vector {i}/{len(in0)}, nbytes={nbytes}")
                else:
                    self.event_num += 1

                    # Time-based periodic reporting (every 10 seconds)
                    current_time = time.time()
                    if current_time - self.last_report_time >= self.report_interval:
                        events_since_last = self.event_num - self.last_report_count
                        elapsed = current_time - self.last_report_time
                        event_rate = events_since_last / elapsed if elapsed > 0 else 0
                        print(f"[SEGMENTER] Status: {self.event_num} total events ({events_since_last} in {elapsed:.1f}s, {event_rate:.1f} events/s)")
                        self.last_report_time = current_time
                        self.last_report_count = self.event_num

        except Exception as e:
            print(f"[SEGMENTER] *** EXCEPTION in work function ***")
            print(f"[SEGMENTER] Exception: {e}")
            import traceback
            traceback.print_exc()

        return len(input_items[0])
