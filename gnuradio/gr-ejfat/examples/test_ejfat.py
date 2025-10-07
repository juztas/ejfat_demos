#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple test script for EJFAT source and sink blocks
"""

import numpy as np
from gnuradio import gr, blocks
from gnuradio import ejfat

class test_flowgraph(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "EJFAT Test")

        # Parameters
        test_file = "/tmp/test_ejfat.bin"

        # Generate test data
        test_data = [1+1j, 2+2j, 3+3j, 4+4j, 5+5j]
        src = blocks.vector_source_c(test_data, vlen=1)

        # Write to file
        sink = ejfat.ejfat_sink(filename=test_file)

        # Connect: source -> sink
        self.connect(src, sink)

def main():
    tb = test_flowgraph()
    print("Writing test signal to /tmp/test_ejfat.bin...")
    tb.run()
    print("Done! File created successfully.")
    print("\nTo read back the file, create a flowgraph with:")
    print("  ejfat_source -> QT GUI Frequency Sink")

if __name__ == '__main__':
    main()
