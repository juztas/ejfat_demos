#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 gr-ejfat author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

try:
    import e2sar_py
    from e2sar_py.DataPlane import Segmenter
    E2SAR_AVAILABLE = True
except ImportError:
    E2SAR_AVAILABLE = False
    print("Warning: e2sar_py not available. ejfat_source will run in file-only mode.")

class ejfat_source(gr.sync_block):
    """
    Source block that reads complex stream from a binary file and optionally
    sends it via EJFAT Segmenter.

    Args:
        filename: Path to input file containing complex samples
        repeat: If True, loop the file playback; if False, output zeros after EOF
        use_ejfat: If True, send data via EJFAT Segmenter
        ejfat_uri: EJFAT URI string (e.g., "ejfat://host:port?sync=host:port&data=host:port")
        data_id: Unique identifier for segmentation point (uint16)
        event_src_id: Unique identifier for transmitting host (uint32)
        cpu_cores: Comma-separated CPU core list (e.g., "0,1,2,3" or empty for default)
        dpv6: Use IPv6 dataplane
        connected_socket: Use connected sockets
        use_cp: Enable control plane (sync packets)
        sync_period_ms: Sync thread period in milliseconds
        sync_periods: Number of sync periods for averaging
        mtu: MTU size (0 = auto-detect)
        num_send_sockets: Number of send sockets for LAG randomization
        snd_socket_buf_size: Socket buffer size in bytes
        rate_gbps: Send rate in Gbps (-1 = unlimited)
    """
    def __init__(self, filename='', repeat=True, use_ejfat=False,
                 ejfat_uri='', data_id=0, event_src_id=0, cpu_cores='',
                 dpv6=False, connected_socket=True, use_cp=True,
                 sync_period_ms=1000, sync_periods=2, mtu=1500,
                 num_send_sockets=4, snd_socket_buf_size=3145728,
                 rate_gbps=-1.0):
        gr.sync_block.__init__(self,
            name="ejfat_source",
            in_sig=None,
            out_sig=[np.complex64])

        # File parameters
        self.filename = filename
        self.repeat = repeat
        self.file_handle = None
        self.eof_reached = False

        # EJFAT parameters
        self.use_ejfat = use_ejfat and E2SAR_AVAILABLE
        self.ejfat_uri = ejfat_uri
        self.data_id = data_id
        self.event_src_id = event_src_id
        self.cpu_cores = cpu_cores

        # SegmenterFlags parameters
        self.dpv6 = dpv6
        self.connected_socket = connected_socket
        self.use_cp = use_cp
        self.sync_period_ms = sync_period_ms
        self.sync_periods = sync_periods
        self.mtu = mtu
        self.num_send_sockets = num_send_sockets
        self.snd_socket_buf_size = snd_socket_buf_size
        self.rate_gbps = rate_gbps

        # EJFAT objects
        self.segmenter = None
        self.event_number = 0

        if self.use_ejfat and not E2SAR_AVAILABLE:
            print("Warning: use_ejfat=True but e2sar_py not available. Running in file-only mode.")
            self.use_ejfat = False

    def start(self):
        """Open file and initialize EJFAT Segmenter when flowgraph starts"""
        # Open input file
        if self.filename:
            try:
                self.file_handle = open(self.filename, 'rb')
                self.eof_reached = False
            except IOError as e:
                print(f"Error opening file {self.filename}: {e}")
                return False

        # Initialize EJFAT Segmenter
        if self.use_ejfat:
            try:
                # Parse EJFAT URI
                uri_result = e2sar_py.EjfatURI.get_from_string(
                    self.ejfat_uri,
                    tt=e2sar_py.EjfatURI.TokenType.admin
                )

                if uri_result.has_error():
                    print(f"Error parsing EJFAT URI: {uri_result.error().message}")
                    return False

                uri = uri_result.value()

                # Configure SegmenterFlags
                flags = Segmenter.SegmenterFlags()
                flags.dpV6 = self.dpv6
                flags.connectedSocket = self.connected_socket
                flags.useCP = self.use_cp
                flags.syncPeriodMs = self.sync_period_ms
                flags.syncPeriods = self.sync_periods
                flags.mtu = self.mtu
                flags.numSendSockets = self.num_send_sockets
                flags.sndSocketBufSize = self.snd_socket_buf_size
                flags.rateGbps = self.rate_gbps

                # Parse CPU cores
                if self.cpu_cores:
                    cpu_core_list = [int(c.strip()) for c in self.cpu_cores.split(',')]
                    self.segmenter = Segmenter(uri, self.data_id, self.event_src_id,
                                              cpu_core_list, sflags=flags)
                else:
                    self.segmenter = Segmenter(uri, self.data_id, self.event_src_id,
                                              sflags=flags)

                # Start the segmenter
                result = self.segmenter.openAndStart()
                if result.has_error():
                    print(f"Error starting EJFAT Segmenter: {result.error().message}")
                    self.segmenter = None
                    return False

                print(f"EJFAT Segmenter started successfully")
                print(f"  MTU: {self.segmenter.getMTU()}")
                print(f"  Max payload: {self.segmenter.getMaxPldLen()}")
                self.event_number = 0

            except Exception as e:
                print(f"Error initializing EJFAT Segmenter: {e}")
                import traceback
                traceback.print_exc()
                self.segmenter = None
                return False

        return True

    def stop(self):
        """Close file and cleanup EJFAT Segmenter when flowgraph stops"""
        # Stop EJFAT Segmenter
        if self.segmenter:
            try:
                # Print final statistics
                stats = self.segmenter.getSendStats()
                print(f"\nEJFAT Segmenter Statistics:")
                print(f"  Messages sent: {stats.msgCnt}")
                print(f"  Errors: {stats.errCnt}")
                if stats.errCnt > 0:
                    print(f"  Last errno: {stats.lastErrno}")
                    print(f"  Last E2SAR error: {stats.lastE2SARError}")

                self.segmenter.stopThreads()
                self.segmenter = None
            except Exception as e:
                print(f"Error stopping EJFAT Segmenter: {e}")

        # Close file
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

        return True

    def work(self, input_items, output_items):
        """Read complex samples from file and optionally send via EJFAT"""
        out = output_items[0]
        noutput_items = len(out)

        if not self.file_handle:
            out[:] = 0
            return noutput_items

        # Try to read the requested number of samples
        try:
            data = np.fromfile(self.file_handle, dtype=np.complex64, count=noutput_items)

            if len(data) == noutput_items:
                # Successfully read all requested samples
                out[:] = data

                # Send via EJFAT if enabled
                if self.use_ejfat and self.segmenter:
                    result = self.segmenter.sendNumpyArray(
                        data, data.nbytes,
                        event_num=self.event_number,
                        data_id=self.data_id,
                        entropy=0
                    )
                    if result.has_error():
                        print(f"EJFAT send error: {result.error().message}")
                    else:
                        self.event_number += 1

                return noutput_items
            elif len(data) > 0:
                # Partial read - near end of file
                out[:len(data)] = data

                # Send via EJFAT if enabled
                if self.use_ejfat and self.segmenter:
                    result = self.segmenter.sendNumpyArray(
                        data, data.nbytes,
                        event_num=self.event_number,
                        data_id=self.data_id,
                        entropy=0
                    )
                    if result.has_error():
                        print(f"EJFAT send error: {result.error().message}")
                    else:
                        self.event_number += 1

                if self.repeat:
                    # Seek back to beginning for next read
                    self.file_handle.seek(0)
                else:
                    # Fill remainder with zeros
                    out[len(data):] = 0
                    self.eof_reached = True
                return noutput_items
            else:
                # EOF reached
                if self.repeat:
                    # Seek back to beginning and try again
                    self.file_handle.seek(0)
                    data = np.fromfile(self.file_handle, dtype=np.complex64, count=noutput_items)
                    if len(data) > 0:
                        out[:len(data)] = data
                        out[len(data):] = 0

                        # Send via EJFAT if enabled
                        if self.use_ejfat and self.segmenter:
                            result = self.segmenter.sendNumpyArray(
                                data, data.nbytes,
                                event_num=self.event_number,
                                data_id=self.data_id,
                                entropy=0
                            )
                            if result.has_error():
                                print(f"EJFAT send error: {result.error().message}")
                            else:
                                self.event_number += 1
                    else:
                        out[:] = 0
                else:
                    # Output zeros after EOF
                    out[:] = 0
                    self.eof_reached = True
                return noutput_items

        except Exception as e:
            print(f"Error reading from file: {e}")
            out[:] = 0
            return noutput_items
