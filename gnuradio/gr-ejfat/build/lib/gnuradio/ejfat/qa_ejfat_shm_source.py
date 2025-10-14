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
import posix_ipc

class qa_ejfat_shm_source(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()
        self.shm_name = f"sr{int(time.time()*100) % 100000}"
        self.fifo = None

    def tearDown(self):
        # Proper cleanup: close and unlink any FIFO created during tests
        if self.fifo:
            try:
                self.fifo.close()
                self.fifo.unlink()
            except:
                pass
            self.fifo = None

        # Additional cleanup: remove any leftover shared memory objects
        shm_name = f'/ejfat_shm_{self.shm_name}'
        sem_name = f'/ejfat_shm_{self.shm_name}_data'

        for resource_name in [shm_name, sem_name]:
            try:
                if '_data' in resource_name:
                    posix_ipc.unlink_semaphore(resource_name)
                else:
                    posix_ipc.unlink_shared_memory(resource_name)
            except posix_ipc.ExistentialError:
                pass
            except:
                pass

        self.tb = None

    def test_instance(self):
        """Test that block can be instantiated (requires existing FIFO)"""
        # Create FIFO first
        self.fifo = ShmFIFO(name=self.shm_name, capacity=1024, entry_size=4096, create=True)

        # Now create source block
        instance = ejfat_shm_source(shm_name=self.shm_name, vlen=1)
        self.assertIsNotNone(instance)

    def test_read_complex_data(self):
        """Test reading complex data from shared memory"""
        # Create test data
        test_data = np.array([1+1j, 2+2j, 3+3j, 4+4j, 5+5j], dtype=np.complex64)

        # Create FIFO
        self.fifo = ShmFIFO(name=self.shm_name, capacity=1024, entry_size=4096, create=True)

        # Pre-write all data before starting flowgraph
        # With vlen=1, write each sample as a separate event
        for i, sample in enumerate(test_data):
            data_bytes = np.array([sample], dtype=np.complex64).tobytes()
            self.fifo.write_event(data_bytes, event_number=i)

        try:
            # Build flowgraph
            source = ejfat_shm_source(shm_name=self.shm_name, timeout=2.0, vlen=1)
            head = blocks.head(gr.sizeof_gr_complex, len(test_data))
            sink = blocks.vector_sink_c()

            self.tb.connect(source, head, sink)

            # Run flowgraph
            self.tb.run()

            # Verify received data
            received_data = np.array(sink.data(), dtype=np.complex64)
            self.assertEqual(len(received_data), len(test_data), "Should receive all samples")
            np.testing.assert_array_almost_equal(test_data, received_data)

        finally:
            pass  # cleanup handled by tearDown()

    def test_multiple_events(self):
        """Test reading multiple events from shared memory"""
        # Create test data
        batch1 = np.array([1+1j, 2+2j, 3+3j], dtype=np.complex64)
        batch2 = np.array([4+4j, 5+5j, 6+6j], dtype=np.complex64)
        batch3 = np.array([7+7j, 8+8j, 9+9j], dtype=np.complex64)

        # Create FIFO
        self.fifo = ShmFIFO(name=self.shm_name, capacity=1024, entry_size=4096, create=True)

        # Pre-write all data before starting flowgraph
        # With vlen=1, write each sample as a separate event
        event_num = 0
        for batch in [batch1, batch2, batch3]:
            for sample in batch:
                data_bytes = np.array([sample], dtype=np.complex64).tobytes()
                self.fifo.write_event(data_bytes, event_number=event_num)
                event_num += 1

        try:
            # Build flowgraph
            source = ejfat_shm_source(shm_name=self.shm_name, timeout=2.0, vlen=1)
            head = blocks.head(gr.sizeof_gr_complex, len(batch1) + len(batch2) + len(batch3))
            sink = blocks.vector_sink_c()

            self.tb.connect(source, head, sink)

            # Run flowgraph
            self.tb.run()

            # Verify received data
            received_data = np.array(sink.data(), dtype=np.complex64)
            expected_data = np.concatenate([batch1, batch2, batch3])
            self.assertEqual(len(received_data), len(expected_data), "Should receive all samples")
            np.testing.assert_array_almost_equal(expected_data, received_data)

        finally:
            pass  # cleanup handled by tearDown()


if __name__ == '__main__':
    gr_unittest.run(qa_ejfat_shm_source)
