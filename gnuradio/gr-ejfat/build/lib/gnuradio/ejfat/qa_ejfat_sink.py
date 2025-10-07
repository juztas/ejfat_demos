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
from gnuradio.ejfat import ejfat_sink

class qa_ejfat_sink(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_instance(self):
        """Test that block can be instantiated"""
        instance = ejfat_sink(filename='test.bin')
        self.assertIsNotNone(instance)

    def test_write_complex_data(self):
        """Test writing complex data to file"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            temp_filename = f.name

        try:
            # Create test data
            src_data = np.array([1+1j, 2+2j, 3+3j, 4+4j, 5+5j], dtype=np.complex64)

            # Build flowgraph
            src = blocks.vector_source_c(src_data, vlen=1)
            sink = ejfat_sink(filename=temp_filename)

            self.tb.connect(src, sink)
            self.tb.run()

            # Read back the file and verify
            read_data = np.fromfile(temp_filename, dtype=np.complex64)
            np.testing.assert_array_almost_equal(src_data, read_data)

        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.remove(temp_filename)


if __name__ == '__main__':
    gr_unittest.run(qa_ejfat_sink)
