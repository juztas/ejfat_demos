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
        use_host_address: Use IP address for gRPC instead of hostname (default: False)
        period_ms: SendState thread period in milliseconds (default: 100)
        validate_cert: Validate control plane TLS certificate (default: True)
        with_lb_header: Expect load balancer header (default: True for testing without LB)
        event_timeout_ms: Event timeout in milliseconds (default: 5000)
        rcv_socket_buf_size: Socket receive buffer size in bytes (default: 3145728)
        port_range: 2^portRange listening ports, -1 = auto (default: -1)
        epoch_ms: PID control epoch period in milliseconds (default: 1000)
        ki: PID integral gain (default: 0.0)
        kp: PID proportional gain (default: 0.0)
        kd: PID derivative gain (default: 0.0)
        set_point: PID setpoint for queue occupancy % (default: 0.0)
        weight: Node processing power weight (default: 1.0)
        min_factor: Min slot allocation factor (default: 0.5)
        max_factor: Max slot allocation factor (default: 2.0)
    """
    def __init__(self, uri='', data_ip='127.0.0.1', starting_port=19522, vector_size=1,
                 num_recv_threads=1, use_cp=False, use_host_address=False, period_ms=100,
                 validate_cert=True, with_lb_header=True, event_timeout_ms=5000,
                 rcv_socket_buf_size=3145728, port_range=-1, epoch_ms=1000,
                 ki=0.0, kp=0.0, kd=0.0, set_point=0.0, weight=1.0,
                 min_factor=0.5, max_factor=2.0):
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
        self.last_report_time = 0
        self.last_report_count = 0
        self.report_interval = 10.0  # Report every 10 seconds

        # Store configuration for initialization in start()
        # Control Plane Parameters
        self.use_cp = use_cp
        self.use_host_address = use_host_address
        self.period_ms = period_ms
        self.validate_cert = validate_cert

        # Network Parameters
        self.with_lb_header = with_lb_header
        self.event_timeout_ms = event_timeout_ms
        self.rcv_socket_buf_size = rcv_socket_buf_size
        self.port_range = port_range

        # PID Control Parameters
        self.epoch_ms = epoch_ms
        self.ki = ki
        self.kp = kp
        self.kd = kd
        self.set_point = set_point

        # Load Balancing Parameters
        self.weight = weight
        self.min_factor = min_factor
        self.max_factor = max_factor

    def start(self):
        """Initialize E2SAR reassembler when flowgraph starts"""
        try:
            print(f"\n{'='*60}")
            print(f"E2SAR REASSEMBLER INITIALIZATION")
            print(f"{'='*60}")
            print(f"URI: {self.uri}")
            print(f"Data IP: {self.data_ip}")
            print(f"Starting Port: {self.starting_port}")
            print(f"Vector Size: {self.vector_size}")
            print(f"Num Recv Threads: {self.num_recv_threads}")
            print(f"Use CP: {self.use_cp}")
            print(f"With LB Header: {self.with_lb_header}")
            print(f"Event Timeout (ms): {self.event_timeout_ms}")

            # Create EJFAT URI
            print(f"\n[REASSEMBLER] Creating EJFAT URI object...")
            ejfat_uri = e2sar_py.EjfatURI(uri=self.uri, tt=e2sar_py.EjfatURI.TokenType.instance)
            print(f"[REASSEMBLER] EJFAT URI created successfully")

            # Print parsed URI components
            print(f"[REASSEMBLER] URI Components:")
            print(f"[REASSEMBLER] Full URI: {ejfat_uri.to_string()}")

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

            # Configure reassembler flags
            print(f"\n[REASSEMBLER] Configuring reassembler flags...")
            rflags = e2sar_py.DataPlane.Reassembler.ReassemblerFlags()

            # Control Plane Parameters
            rflags.useCP = self.use_cp
            rflags.useHostAddress = self.use_host_address
            rflags.period_ms = self.period_ms
            rflags.validateCert = self.validate_cert

            # Network Parameters
            rflags.withLBHeader = self.with_lb_header
            rflags.eventTimeout_ms = self.event_timeout_ms
            rflags.rcvSocketBufSize = self.rcv_socket_buf_size
            rflags.portRange = self.port_range

            # PID Control Parameters
            rflags.epoch_ms = self.epoch_ms
            rflags.Ki = self.ki
            rflags.Kp = self.kp
            rflags.Kd = self.kd
            rflags.setPoint = self.set_point

            # Load Balancing Parameters
            rflags.weight = self.weight
            rflags.min_factor = self.min_factor
            rflags.max_factor = self.max_factor
            print(f"[REASSEMBLER] Flags configured")

            # Create reassembler
            print(f"\n[REASSEMBLER] Creating reassembler object...")
            print(f"[REASSEMBLER] Listen address: {self.data_ip}:{self.starting_port}")
            self.reassembler = e2sar_py.DataPlane.Reassembler(
                ejfat_uri,
                e2sar_py.IPAddress.from_string(self.data_ip),
                self.starting_port,
                self.num_recv_threads,
                rflags)
            print(f"[REASSEMBLER] Reassembler object created")

            # Open and start reassembler
            print(f"\n[REASSEMBLER] Calling OpenAndStart()...")
            res = self.reassembler.OpenAndStart()
            if res.has_error():
                error_msg = f"\n[REASSEMBLER] *** FATAL ERROR during openAndStart() ***\n"
                error_msg += f"[REASSEMBLER] Error code: {res.error().value}\n"
                error_msg += f"[REASSEMBLER] Error message: {res.error().message}\n"
                error_msg += f"{'='*60}\n"
                error_msg += f"\nE2SAR Reassembler failed to start - STOPPING FLOWGRAPH\n"
                print(error_msg)
                raise RuntimeError(f"E2SAR Reassembler failed to start: {res.error().message}")

            print(f"[REASSEMBLER] *** SUCCESSFULLY STARTED ***")
            print(f"[REASSEMBLER] Listening on {self.data_ip}:{self.starting_port}")
            print(f"{'='*60}\n")
            self.last_report_time = time.time()
            return True

        except RuntimeError:
            # Re-raise RuntimeError so it propagates up
            raise
        except Exception as e:
            error_msg = f"\n[REASSEMBLER] *** FATAL EXCEPTION during initialization ***\n"
            error_msg += f"[REASSEMBLER] Exception: {e}\n"
            print(error_msg)
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            print(f"\nE2SAR Reassembler initialization failed - STOPPING FLOWGRAPH\n")
            raise RuntimeError(f"E2SAR Reassembler initialization failed: {e}") from e

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
                    print(f"[REASSEMBLER] Error receiving (recv_len=-2)")
                    break
                elif recv_len == -1:
                    # No message available
                    break
                elif recv_len > 0:
                    # Successfully received an event
                    self.event_count += 1

                    # Time-based periodic reporting (every 10 seconds)
                    current_time = time.time()
                    if current_time - self.last_report_time >= self.report_interval:
                        events_since_last = self.event_count - self.last_report_count
                        elapsed = current_time - self.last_report_time
                        event_rate = events_since_last / elapsed if elapsed > 0 else 0
                        print(f"[REASSEMBLER] Status: {self.event_count} total events ({events_since_last} in {elapsed:.1f}s, {event_rate:.1f} events/s)")
                        self.last_report_time = current_time
                        self.last_report_count = self.event_count

                    # Calculate how many vectors we received
                    num_samples = len(recv_array)
                    num_vectors = num_samples // self.vector_size

                    if num_vectors == 0:
                        # Not enough samples for even one vector
                        print(f"[REASSEMBLER] Warning: Received {num_samples} samples, need {self.vector_size} for one vector")
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
            print(f"[REASSEMBLER] *** EXCEPTION in work function ***")
            print(f"[REASSEMBLER] Exception: {e}")
            import traceback
            traceback.print_exc()
            out[:] = 0
            return noutput_items
