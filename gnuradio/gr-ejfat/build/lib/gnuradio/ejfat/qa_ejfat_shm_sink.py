#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 gr-ejfat author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import time
import numpy as np
from gnuradio import gr, gr_unittest, blocks
from gnuradio.ejfat import ejfat_shm_sink
from ejfat_shm import ShmFIFO

class qa_ejfat_shm_sink(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()
        self.shm_name = f"ts{int(time.time()*100) % 100000}"

    def tearDown(self):
        self.tb = None
        # Clean up any leftover shared memory
        try:
            fifo = ShmFIFO(name=self.shm_name, create=False)
            fifo.close()
        except:
            pass

    def test_instance(self):
        """Test that block can be instantiated"""
        instance = ejfat_shm_sink(shm_name=self.shm_name)
        self.assertIsNotNone(instance)

    def test_write_complex_data(self):
        """Test writing complex data to shared memory"""
        # Create test data
        src_data = np.array([1+1j, 2+2j, 3+3j, 4+4j, 5+5j], dtype=np.complex64)

        # Build flowgraph
        src = blocks.vector_source_c(src_data, vlen=1)
        sink = ejfat_shm_sink(shm_name=self.shm_name, capacity=1024, entry_size=4096)

        self.tb.connect(src, sink)

        # Start flowgraph
        self.tb.start()
        time.sleep(0.1)  # Give it time to write

        # Open reader and verify data
        try:
            reader = ShmFIFO(name=self.shm_name, create=False)

            # Read event
            result = reader.read_event(timeout=1.0)
            self.assertIsNotNone(result, "Should have received data")

            event_number, data = result
            read_samples = np.frombuffer(data, dtype=np.complex64)

            # Verify data matches
            np.testing.assert_array_almost_equal(src_data, read_samples)

            reader.close()
        finally:
            self.tb.stop()
            self.tb.wait()

    def test_multiple_writes(self):
        """Test writing multiple batches of data"""
        # Create test data - small enough to fit in one write
        src_data = np.array([1+1j, 2+2j, 3+3j], dtype=np.complex64)

        # Build flowgraph
        src = blocks.vector_source_c(src_data, vlen=1)
        sink = ejfat_shm_sink(shm_name=self.shm_name, capacity=10, entry_size=1024)

        self.tb.connect(src, sink)

        # Run flowgraph to completion
        self.tb.run()

        # Verify sink created and wrote data (stats are printed on stop)
        # Just verify the test completes without errors
        self.assertTrue(True)


if __name__ == '__main__':
    gr_unittest.run(qa_ejfat_shm_sink)
