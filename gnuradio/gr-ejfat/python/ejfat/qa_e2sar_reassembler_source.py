#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 gr-ejfat author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import numpy as np
from gnuradio import gr, gr_unittest, blocks

try:
    import e2sar_py
    E2SAR_AVAILABLE = True
except ImportError:
    E2SAR_AVAILABLE = False

if E2SAR_AVAILABLE:
    from gnuradio.ejfat import e2sar_reassembler_source

class qa_e2sar_reassembler_source(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_instance(self):
        """Test that block can be instantiated"""
        if not E2SAR_AVAILABLE:
            self.skipTest("e2sar_py not available")

        uri = 'ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1'
        instance = e2sar_reassembler_source(uri=uri, data_ip='127.0.0.1', starting_port=19522, vector_size=1024)
        self.assertIsNotNone(instance)

    def test_vector_output(self):
        """Test that block produces vector output"""
        if not E2SAR_AVAILABLE:
            self.skipTest("e2sar_py not available")

        uri = 'ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1'
        vector_size = 256

        # Build flowgraph (but don't run it since we need E2SAR infrastructure)
        src = e2sar_reassembler_source(uri=uri, data_ip='127.0.0.1', starting_port=19522,
                                       vector_size=vector_size, use_cp=False, with_lb_header=True)
        sink = blocks.vector_sink_c(vlen=vector_size)

        # Just test that connection is valid
        self.tb.connect(src, sink)


if __name__ == '__main__':
    gr_unittest.run(qa_e2sar_reassembler_source)
