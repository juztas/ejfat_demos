#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Simple E2SAR Segmenter/Reassembler Test
#
# This script demonstrates a basic loopback test of the E2SAR segmenter
# and reassembler blocks in a single flowgraph.
#

import numpy as np
import time
from gnuradio import gr, blocks, analog
from gnuradio.ejfat import e2sar_segmenter_sink, e2sar_reassembler_source

# Configuration
DATA_IP = "127.0.0.1"
DATA_PORT = 19522
EJFAT_URI = f"ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data={DATA_IP}:{DATA_PORT}"
DATA_ID = 0x0505      # 1285 in decimal
EVENT_SRC_ID = 0x11223344  # 287454020 in decimal
VECTOR_SIZE = 1024    # Number of complex samples per event
SAMPLE_RATE = 1e6     # 1 MSps
SIGNAL_FREQ = 10000   # 10 kHz test tone


class E2SARLoopbackTest(gr.top_block):
    """
    Simple loopback test flowgraph.

    Signal flow:
    1. Generate 10 kHz cosine wave
    2. Throttle to sample rate
    3. Convert stream to vectors
    4. Send via E2SAR segmenter
    5. Receive via E2SAR reassembler
    6. Convert vectors back to stream
    7. Display statistics
    """

    def __init__(self):
        gr.top_block.__init__(self, "E2SAR Loopback Test")

        ##################################################
        # TRANSMITTER PATH
        ##################################################

        # Signal source - generate a 10 kHz tone
        self.signal_source = analog.sig_source_c(
            SAMPLE_RATE,
            analog.GR_COS_WAVE,
            SIGNAL_FREQ,
            1.0,  # amplitude
            0     # offset
        )

        # Throttle to avoid CPU overload
        self.throttle = blocks.throttle(
            gr.sizeof_gr_complex,
            SAMPLE_RATE,
            True  # ignore tags
        )

        # Convert stream to vectors for E2SAR
        self.stream_to_vector = blocks.stream_to_vector(
            gr.sizeof_gr_complex,
            VECTOR_SIZE
        )

        # E2SAR segmenter sink - sends data
        self.e2sar_sink = e2sar_segmenter_sink(
            uri=EJFAT_URI,
            data_id=DATA_ID,
            event_src_id=EVENT_SRC_ID,
            vector_size=VECTOR_SIZE,
            use_cp=False,
            mtu=9000,
            rate_gbps=1.0
        )

        ##################################################
        # RECEIVER PATH
        ##################################################

        # E2SAR reassembler source - receives data
        self.e2sar_source = e2sar_reassembler_source(
            uri=EJFAT_URI,
            data_ip=DATA_IP,
            starting_port=DATA_PORT,
            vector_size=VECTOR_SIZE,
            num_recv_threads=1,
            use_cp=False,
            with_lb_header=True,
            event_timeout_ms=5000
        )

        # Convert vectors back to stream
        self.vector_to_stream = blocks.vector_to_stream(
            gr.sizeof_gr_complex,
            VECTOR_SIZE
        )

        # Head block to limit samples (optional)
        # self.head = blocks.head(gr.sizeof_gr_complex, int(SAMPLE_RATE * 10))

        # Null sink - just receive and discard
        self.null_sink = blocks.null_sink(gr.sizeof_gr_complex)

        ##################################################
        # CONNECTIONS
        ##################################################

        # Transmitter chain
        self.connect(
            self.signal_source,
            self.throttle,
            self.stream_to_vector,
            self.e2sar_sink
        )

        # Receiver chain
        self.connect(
            self.e2sar_source,
            self.vector_to_stream,
            self.null_sink
        )


def main():
    print("=" * 70)
    print("E2SAR Segmenter/Reassembler Loopback Test")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  EJFAT URI:        {EJFAT_URI}")
    print(f"  Data IP:          {DATA_IP}")
    print(f"  Data Port:        {DATA_PORT}")
    print(f"  Data ID:          0x{DATA_ID:04X} ({DATA_ID})")
    print(f"  Event Source ID:  0x{EVENT_SRC_ID:08X} ({EVENT_SRC_ID})")
    print(f"  Vector Size:      {VECTOR_SIZE} samples")
    print(f"  Sample Rate:      {SAMPLE_RATE/1e6:.1f} MSps")
    print(f"  Signal Frequency: {SIGNAL_FREQ/1e3:.1f} kHz")
    print()
    print("Signal Flow:")
    print("  1. Generate 10 kHz cosine wave")
    print("  2. Throttle to sample rate")
    print("  3. Convert stream to vectors")
    print("  4. Send via E2SAR segmenter")
    print("  5. Receive via E2SAR reassembler")
    print("  6. Convert vectors back to stream")
    print("  7. Sink (discard)")
    print()

    # Check for E2SAR Python bindings
    try:
        import e2sar_py
        print("✓ E2SAR Python bindings found")
    except ImportError:
        print("✗ ERROR: e2sar_py module not found!")
        print()
        print("Please install E2SAR with Python bindings:")
        print("  1. Locate or clone E2SAR repository")
        print("  2. cd $E2SAR_PATH")
        print("  3. meson setup build")
        print("  4. meson compile -C build")
        print("  5. export PYTHONPATH=$E2SAR_PATH/build/src/pybind:$PYTHONPATH")
        print()
        return 1

    print()
    print("Starting flowgraph...")
    print("Press Ctrl+C to stop")
    print()

    tb = E2SARLoopbackTest()

    try:
        tb.start()

        # Run for a period of time and show status
        duration = 30  # seconds
        for i in range(duration):
            time.sleep(1)
            if (i + 1) % 5 == 0:
                print(f"Running... ({i+1}/{duration} seconds)")

        print()
        print("Stopping flowgraph...")
        tb.stop()
        tb.wait()

        print()
        print("Test completed successfully!")
        print()

    except KeyboardInterrupt:
        print()
        print("Interrupted by user")
        tb.stop()
        tb.wait()

    except Exception as e:
        print()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        tb.stop()
        tb.wait()
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
