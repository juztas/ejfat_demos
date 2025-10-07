#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 gr-ejfat author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import time
import threading
import numpy as np
from gnuradio import gr, gr_unittest, blocks
from gnuradio.ejfat import ejfat_shm_source
from ejfat_shm import ShmFIFO

class qa_ejfat_shm_source(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()
        self.shm_name = f"sr{int(time.time()*100) % 100000}"

    def tearDown(self):
        self.tb = None

    def test_instance(self):
        """Test that block can be instantiated (requires existing FIFO)"""
        # Create FIFO first
        fifo = ShmFIFO(name=self.shm_name, capacity=1024, entry_size=4096, create=True)

        try:
            # Now create source block
            instance = ejfat_shm_source(shm_name=self.shm_name)
            self.assertIsNotNone(instance)
        finally:
            fifo.close()
            fifo.unlink()

    def test_read_complex_data(self):
        """Test reading complex data from shared memory"""
        # Create test data
        test_data = np.array([1+1j, 2+2j, 3+3j, 4+4j, 5+5j], dtype=np.complex64)

        # Create FIFO and write data
        fifo = ShmFIFO(name=self.shm_name, capacity=1024, entry_size=4096, create=True)

        def write_data():
            """Background thread to write data"""
            time.sleep(0.1)  # Give source time to start
            data_bytes = test_data.tobytes()
            result = fifo.write_event(data_bytes, event_number=0)
            print(f"Write result: {result}")

        # Start writer thread
        writer = threading.Thread(target=write_data)
        writer.start()

        try:
            # Build flowgraph
            source = ejfat_shm_source(shm_name=self.shm_name, timeout=2.0)
            head = blocks.head(gr.sizeof_gr_complex, len(test_data))
            sink = blocks.vector_sink_c()

            self.tb.connect(source, head, sink)

            # Run flowgraph
            self.tb.run()

            # Wait for writer to finish
            writer.join()

            # Verify received data
            received_data = np.array(sink.data(), dtype=np.complex64)
            self.assertEqual(len(received_data), len(test_data), "Should receive all samples")
            np.testing.assert_array_almost_equal(test_data, received_data)

        finally:
            fifo.close()
            fifo.unlink()

    def test_multiple_events(self):
        """Test reading multiple events from shared memory"""
        # Create test data
        batch1 = np.array([1+1j, 2+2j, 3+3j], dtype=np.complex64)
        batch2 = np.array([4+4j, 5+5j, 6+6j], dtype=np.complex64)
        batch3 = np.array([7+7j, 8+8j, 9+9j], dtype=np.complex64)

        # Create FIFO and write data
        fifo = ShmFIFO(name=self.shm_name, capacity=1024, entry_size=4096, create=True)

        def write_data():
            """Background thread to write data"""
            time.sleep(0.1)  # Give source time to start
            fifo.write_event(batch1.tobytes(), event_number=0)
            time.sleep(0.05)
            fifo.write_event(batch2.tobytes(), event_number=1)
            time.sleep(0.05)
            fifo.write_event(batch3.tobytes(), event_number=2)

        # Start writer thread
        writer = threading.Thread(target=write_data)
        writer.start()

        try:
            # Build flowgraph
            source = ejfat_shm_source(shm_name=self.shm_name, timeout=2.0)
            head = blocks.head(gr.sizeof_gr_complex, len(batch1) + len(batch2) + len(batch3))
            sink = blocks.vector_sink_c()

            self.tb.connect(source, head, sink)

            # Run flowgraph
            self.tb.run()

            # Wait for writer to finish
            writer.join()

            # Verify received data
            received_data = np.array(sink.data(), dtype=np.complex64)
            expected_data = np.concatenate([batch1, batch2, batch3])
            self.assertEqual(len(received_data), len(expected_data), "Should receive all samples")
            np.testing.assert_array_almost_equal(expected_data, received_data)

        finally:
            fifo.close()
            fifo.unlink()


if __name__ == '__main__':
    gr_unittest.run(qa_ejfat_shm_source)
