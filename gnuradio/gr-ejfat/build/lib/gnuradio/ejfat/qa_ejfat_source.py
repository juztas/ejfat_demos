#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 gr-ejfat author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import os
import tempfile
import numpy as np
from gnuradio import gr, gr_unittest, blocks
from gnuradio.ejfat import ejfat_source

class qa_ejfat_source(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_instance(self):
        """Test that block can be instantiated"""
        instance = ejfat_source(filename='test.bin')
        self.assertIsNotNone(instance)

    def test_read_complex_data(self):
        """Test reading complex data from file"""
        # Create temporary file with test data
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            temp_filename = f.name

        try:
            # Create and write test data
            src_data = np.array([1+1j, 2+2j, 3+3j, 4+4j, 5+5j], dtype=np.complex64)
            src_data.tofile(temp_filename)

            # Build flowgraph
            src = ejfat_source(filename=temp_filename, repeat=False)
            dst = blocks.vector_sink_c()

            self.tb.connect(src, dst)
            self.tb.run()

            # Verify the read data
            result_data = np.array(dst.data(), dtype=np.complex64)
            # Check that we got at least the test data
            np.testing.assert_array_almost_equal(src_data, result_data[:len(src_data)])

        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def test_repeat_mode(self):
        """Test that repeat mode loops the file"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            temp_filename = f.name

        try:
            # Create small test data
            src_data = np.array([1+1j, 2+2j], dtype=np.complex64)
            src_data.tofile(temp_filename)

            # Build flowgraph with head block to limit output
            src = ejfat_source(filename=temp_filename, repeat=True)
            head = blocks.head(gr.sizeof_gr_complex, 6)  # Read 6 samples (3x the file)
            dst = blocks.vector_sink_c()

            self.tb.connect(src, head)
            self.tb.connect(head, dst)
            self.tb.run()

            # Should have repeated the pattern
            result_data = np.array(dst.data(), dtype=np.complex64)
            self.assertEqual(len(result_data), 6)

        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.remove(temp_filename)


if __name__ == '__main__':
    gr_unittest.run(qa_ejfat_source)
