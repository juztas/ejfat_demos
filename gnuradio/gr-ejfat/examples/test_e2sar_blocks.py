#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2025 gr-ejfat author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""
Example flowgraph demonstrating E2SAR segmenter sink and reassembler source blocks.

This example creates two separate flowgraphs that can be run:
1. Transmitter: Generates complex signals and sends them via E2SAR segmenter
2. Receiver: Receives complex signals via E2SAR reassembler and saves to file

To run this example, you need:
- E2SAR installed with e2sar_py Python bindings
- Proper EJFAT URI configuration
- Network connectivity between segmenter and reassembler

Usage:
    # Run transmitter in one terminal
    python test_e2sar_blocks.py --tx

    # Run receiver in another terminal
    python test_e2sar_blocks.py --rx

    # Run loopback test (both tx and rx using localhost)
    python test_e2sar_blocks.py --loopback
"""

import numpy as np
import argparse
import time
from gnuradio import gr, blocks, analog
from gnuradio.ejfat import e2sar_segmenter_sink, e2sar_reassembler_source

# Configuration
EJFAT_URI_BASE = "ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data="
DATA_IP = "127.0.0.1"
DATA_PORT = 19522
DATA_ID = 0x0505
EVENT_SRC_ID = 0x11223344
VECTOR_SIZE = 1024  # Number of complex samples per event
SAMPLE_RATE = 1e6   # 1 MSps


class TransmitterFlowgraph(gr.top_block):
    """Transmitter flowgraph using E2SAR segmenter sink"""

    def __init__(self, uri, data_id, event_src_id, vector_size, sample_rate):
        gr.top_block.__init__(self, "E2SAR Transmitter")

        # Signal source - generate a tone
        freq = 10000  # 10 kHz tone
        self.signal_source = analog.sig_source_c(sample_rate, analog.GR_COS_WAVE, freq, 1.0, 0)

        # Stream to vector - convert stream to vectors for E2SAR
        self.stream_to_vector = blocks.stream_to_vector(gr.sizeof_gr_complex, vector_size)

        # E2SAR segmenter sink
        self.e2sar_sink = e2sar_segmenter_sink(
            uri=uri,
            data_id=data_id,
            event_src_id=event_src_id,
            vector_size=vector_size,
            use_cp=False,
            mtu=9000,
            rate_gbps=1.0
        )

        # Connect blocks
        self.connect(self.signal_source, self.stream_to_vector, self.e2sar_sink)


class ReceiverFlowgraph(gr.top_block):
    """Receiver flowgraph using E2SAR reassembler source"""

    def __init__(self, uri, data_ip, data_port, vector_size, output_file=None):
        gr.top_block.__init__(self, "E2SAR Receiver")

        # E2SAR reassembler source
        self.e2sar_source = e2sar_reassembler_source(
            uri=uri,
            data_ip=data_ip,
            starting_port=data_port,
            vector_size=vector_size,
            num_recv_threads=1,
            use_cp=False,
            with_lb_header=True,
            event_timeout_ms=5000
        )

        # Vector to stream - convert vectors back to stream
        self.vector_to_stream = blocks.vector_to_stream(gr.sizeof_gr_complex, vector_size)

        # Optional file sink to save received data
        if output_file:
            self.file_sink = blocks.file_sink(gr.sizeof_gr_complex, output_file, False)
            self.connect(self.e2sar_source, self.vector_to_stream, self.file_sink)
        else:
            # Just null sink if no output file specified
            self.null_sink = blocks.null_sink(gr.sizeof_gr_complex)
            self.connect(self.e2sar_source, self.vector_to_stream, self.null_sink)


def run_transmitter(uri, duration=10):
    """Run transmitter flowgraph"""
    print("Starting E2SAR Transmitter...")
    print(f"  URI: {uri}")
    print(f"  Data ID: {DATA_ID}")
    print(f"  Event Source ID: {EVENT_SRC_ID}")
    print(f"  Vector Size: {VECTOR_SIZE}")
    print(f"  Duration: {duration} seconds")

    tb = TransmitterFlowgraph(uri, DATA_ID, EVENT_SRC_ID, VECTOR_SIZE, SAMPLE_RATE)

    try:
        tb.start()
        print(f"Transmitting for {duration} seconds...")
        time.sleep(duration)
        tb.stop()
        tb.wait()
        print("Transmitter stopped.")
    except KeyboardInterrupt:
        print("\nStopping transmitter...")
        tb.stop()
        tb.wait()


def run_receiver(uri, data_ip, data_port, duration=10, output_file=None):
    """Run receiver flowgraph"""
    print("Starting E2SAR Receiver...")
    print(f"  URI: {uri}")
    print(f"  Data IP: {data_ip}")
    print(f"  Starting Port: {data_port}")
    print(f"  Vector Size: {VECTOR_SIZE}")
    print(f"  Duration: {duration} seconds")
    if output_file:
        print(f"  Output File: {output_file}")

    tb = ReceiverFlowgraph(uri, data_ip, data_port, VECTOR_SIZE, output_file)

    try:
        tb.start()
        print(f"Receiving for {duration} seconds...")
        time.sleep(duration)
        tb.stop()
        tb.wait()
        print("Receiver stopped.")
    except KeyboardInterrupt:
        print("\nStopping receiver...")
        tb.stop()
        tb.wait()


def main():
    parser = argparse.ArgumentParser(description='E2SAR GNU Radio Example')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--tx', action='store_true', help='Run transmitter')
    group.add_argument('--rx', action='store_true', help='Run receiver')
    group.add_argument('--loopback', action='store_true', help='Run loopback test')

    parser.add_argument('--duration', type=int, default=10, help='Duration in seconds')
    parser.add_argument('--data-ip', type=str, default=DATA_IP, help='Data plane IP address')
    parser.add_argument('--data-port', type=int, default=DATA_PORT, help='Data plane port')
    parser.add_argument('--output', type=str, default=None, help='Output file for receiver')

    args = parser.parse_args()

    # Construct URIs
    tx_uri = f"{EJFAT_URI_BASE}{args.data_ip}:{args.data_port}"
    rx_uri = f"{EJFAT_URI_BASE}{args.data_ip}"

    try:
        import e2sar_py
    except ImportError:
        print("ERROR: e2sar_py module not found!")
        print("Please install E2SAR with Python bindings:")
        print("  cd $E2SAR_PATH")
        print("  meson setup build")
        print("  meson compile -C build")
        print("  export PYTHONPATH=$E2SAR_PATH/build/src/pybind:$PYTHONPATH")
        return 1

    if args.tx:
        run_transmitter(tx_uri, args.duration)
    elif args.rx:
        run_receiver(rx_uri, args.data_ip, args.data_port, args.duration, args.output)
    elif args.loopback:
        print("Loopback test not yet implemented.")
        print("Please run transmitter and receiver in separate terminals:")
        print(f"  Terminal 1: python {__file__} --tx --duration {args.duration}")
        print(f"  Terminal 2: python {__file__} --rx --duration {args.duration}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
