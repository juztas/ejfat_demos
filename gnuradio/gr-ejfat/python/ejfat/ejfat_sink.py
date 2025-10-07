#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 gr-ejfat author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

class ejfat_sink(gr.sync_block):
    """
    Sink block that writes complex stream to a binary file.

    Args:
        filename: Path to output file for writing complex samples
    """
    def __init__(self, filename=''):
        gr.sync_block.__init__(self,
            name="ejfat_sink",
            in_sig=[np.complex64],
            out_sig=None)

        self.filename = filename
        self.file_handle = None

    def start(self):
        """Open file when flowgraph starts"""
        if self.filename:
            self.file_handle = open(self.filename, 'wb')
        return True

    def stop(self):
        """Close file when flowgraph stops"""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        return True

    def work(self, input_items, output_items):
        """Write complex samples to file"""
        in0 = input_items[0]

        if self.file_handle:
            # Write complex samples as binary data
            in0.tofile(self.file_handle)

        return len(input_items[0])
