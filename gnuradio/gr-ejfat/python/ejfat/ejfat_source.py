#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 gr-ejfat author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

class ejfat_source(gr.sync_block):
    """
    Source block that reads complex stream from a binary file.

    Args:
        filename: Path to input file containing complex samples
        repeat: If True, loop the file playback; if False, output zeros after EOF
    """
    def __init__(self, filename='', repeat=True):
        gr.sync_block.__init__(self,
            name="ejfat_source",
            in_sig=None,
            out_sig=[np.complex64])

        self.filename = filename
        self.repeat = repeat
        self.file_handle = None
        self.eof_reached = False

    def start(self):
        """Open file when flowgraph starts"""
        if self.filename:
            try:
                self.file_handle = open(self.filename, 'rb')
                self.eof_reached = False
            except IOError as e:
                print(f"Error opening file {self.filename}: {e}")
                return False
        return True

    def stop(self):
        """Close file when flowgraph stops"""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        return True

    def work(self, input_items, output_items):
        """Read complex samples from file"""
        out = output_items[0]
        noutput_items = len(out)

        if not self.file_handle:
            out[:] = 0
            return noutput_items

        # Try to read the requested number of samples
        try:
            data = np.fromfile(self.file_handle, dtype=np.complex64, count=noutput_items)

            if len(data) == noutput_items:
                # Successfully read all requested samples
                out[:] = data
                return noutput_items
            elif len(data) > 0:
                # Partial read - near end of file
                out[:len(data)] = data
                if self.repeat:
                    # Seek back to beginning for next read
                    self.file_handle.seek(0)
                else:
                    # Fill remainder with zeros
                    out[len(data):] = 0
                    self.eof_reached = True
                return noutput_items
            else:
                # EOF reached
                if self.repeat:
                    # Seek back to beginning and try again
                    self.file_handle.seek(0)
                    data = np.fromfile(self.file_handle, dtype=np.complex64, count=noutput_items)
                    if len(data) > 0:
                        out[:len(data)] = data
                        out[len(data):] = 0
                    else:
                        out[:] = 0
                else:
                    # Output zeros after EOF
                    out[:] = 0
                    self.eof_reached = True
                return noutput_items

        except Exception as e:
            print(f"Error reading from file: {e}")
            out[:] = 0
            return noutput_items
