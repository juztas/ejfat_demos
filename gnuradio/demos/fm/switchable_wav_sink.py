#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Switchable WAV File Sink Block

A custom GNU Radio block that can switch output WAV files on command.
Receives filename via a message port.
"""

import numpy as np
from gnuradio import gr
import wave
import pmt


class switchable_wav_sink(gr.sync_block):
    """
    WAV file sink that can switch output files via message port.
    """
    def __init__(self, sample_rate=48000, channels=2):
        gr.sync_block.__init__(
            self,
            name="switchable_wav_sink",
            in_sig=[np.float32, np.float32] if channels == 2 else [np.float32],
            out_sig=None
        )

        self.sample_rate = sample_rate
        self.channels = channels
        self.wav_file = None
        self.current_filename = None

        # Register message port for receiving filename commands
        self.message_port_register_in(pmt.intern("filename"))
        self.set_msg_handler(pmt.intern("filename"), self.handle_filename_msg)

    def handle_filename_msg(self, msg):
        """Handle incoming filename message."""
        try:
            # Close current file if open
            if self.wav_file is not None:
                self.wav_file.close()
                self.wav_file = None
                print(f"Closed WAV file: {self.current_filename}")

            # Get new filename from message
            if pmt.is_pair(msg):
                # Message is (key, value) pair
                filename = pmt.symbol_to_string(pmt.cdr(msg))
            else:
                # Message is just the filename
                filename = pmt.symbol_to_string(msg)

            # Only open new WAV file if filename is non-empty
            if filename and filename.strip():
                self.current_filename = filename
                self.wav_file = wave.open(filename, 'wb')
                self.wav_file.setnchannels(self.channels)
                self.wav_file.setsampwidth(2)  # 16-bit PCM
                self.wav_file.setframerate(self.sample_rate)
                print(f"Started recording to: {filename}")
            else:
                self.current_filename = None
                print("WAV recording stopped (no filename provided)")

        except Exception as e:
            print(f"Error switching WAV file: {e}")
            self.wav_file = None
            self.current_filename = None

    def work(self, input_items, output_items):
        """Process audio samples and write to current WAV file."""
        if self.wav_file is None:
            # No file open, just consume the input
            return len(input_items[0])

        try:
            # Get input samples
            if self.channels == 2:
                left = input_items[0]
                right = input_items[1]

                # Interleave channels
                num_samples = len(left)
                interleaved = np.empty(num_samples * 2, dtype=np.float32)
                interleaved[0::2] = left
                interleaved[1::2] = right
            else:
                interleaved = input_items[0]

            # Convert float32 [-1.0, 1.0] to int16
            scaled = np.clip(interleaved * 32767, -32768, 32767)
            samples_int16 = scaled.astype(np.int16)

            # Write to WAV file
            self.wav_file.writeframes(samples_int16.tobytes())

        except Exception as e:
            print(f"Error writing to WAV file: {e}")

        return len(input_items[0])

    def stop(self):
        """Close WAV file on flowgraph stop."""
        if self.wav_file is not None:
            self.wav_file.close()
            self.wav_file = None
        return True
