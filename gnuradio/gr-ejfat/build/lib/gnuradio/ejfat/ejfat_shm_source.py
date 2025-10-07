#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 gr-ejfat author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr
from ejfat_shm import ShmFIFO, ShmFIFONotFoundError
import posix_ipc

class ejfat_shm_source(gr.sync_block):
    """
    Source block that reads complex vectors from shared memory FIFO.

    Uses ejfat_shm package for high-performance inter-process communication
    via POSIX shared memory with semaphore-based synchronization.

    Args:
        shm_name: Unique identifier for the shared memory FIFO
        timeout: Seconds to wait for data (None=block forever, 0=non-blocking)
        vlen: Vector length for output (default: 1024)
    """
    def __init__(self, shm_name='ejfat_fifo', timeout=None, vlen=1024):
        gr.sync_block.__init__(self,
            name="ejfat_shm_source",
            in_sig=None,
            out_sig=[(np.complex64, vlen)])

        self.shm_name = shm_name
        self.timeout = timeout
        self.vlen = vlen
        self.fifo = None
        self.total_samples_read = 0
        self.total_events_read = 0
        self.last_event_number = -1

    def start(self):
        """Open existing shared memory FIFO when flowgraph starts"""
        try:
            self.fifo = ShmFIFO(
                name=self.shm_name,
                create=False
            )
            self.total_samples_read = 0
            self.total_events_read = 0
            self.last_event_number = -1

            stats = self.fifo.get_stats()
            print(f"ShmFIFO Source connected: {self.shm_name} (capacity={stats['capacity']}, entry_size={stats['entry_size']})")
            return True
        except ShmFIFONotFoundError as e:
            print(f"Error: {e}")
            print(f"Hint: Ensure the writer (ejfat_shm_sink) has created the FIFO first.")
            return False
        except Exception as e:
            print(f"Error opening ShmFIFO: {e}")
            return False

    def stop(self):
        """Close shared memory FIFO when flowgraph stops"""
        if self.fifo:
            stats = self.fifo.get_stats()
            print(f"\nShmFIFO Source statistics:")
            print(f"  Total samples read: {self.total_samples_read}")
            print(f"  Total events read: {self.total_events_read}")
            print(f"  Last event number: {self.last_event_number}")

            self.fifo.close()
            self.fifo = None

        # Clean up shared memory if we're the last one to stop
        self._cleanup_orphaned_shm()
        return True

    def _cleanup_orphaned_shm(self):
        """Clean up orphaned shared memory objects if the sink stopped unexpectedly"""
        # The ejfat_shm package uses these naming conventions
        shm_name = f'/ejfat_shm_{self.shm_name}'
        sem_name = f'/ejfat_shm_{self.shm_name}_data'

        for resource_name in [shm_name, sem_name]:
            try:
                if '_data' in resource_name:
                    posix_ipc.unlink_semaphore(resource_name)
                    print(f"Cleaned up orphaned semaphore: {resource_name}")
                else:
                    posix_ipc.unlink_shared_memory(resource_name)
                    print(f"Cleaned up orphaned shared memory: {resource_name}")
            except posix_ipc.ExistentialError:
                # Resource doesn't exist, nothing to clean up
                pass
            except Exception as e:
                print(f"Warning: Could not clean up {resource_name}: {e}")

    def work(self, input_items, output_items):
        """Read complex vectors from shared memory FIFO"""
        out = output_items[0]
        nvectors = len(out)

        if not self.fifo:
            # FIFO not initialized, output zeros
            out[:] = 0
            return nvectors

        vectors_produced = 0

        # Read events from FIFO
        while vectors_produced < nvectors:
            # Determine timeout based on how much data we've already produced
            # Use provided timeout only on first read, then non-blocking for subsequent reads
            read_timeout = self.timeout if vectors_produced == 0 else 0

            # Read event from FIFO
            result = self.fifo.read_event(timeout=read_timeout)

            if result is None:
                # No data available
                if vectors_produced == 0:
                    # No data at all, output zeros
                    out[:] = 0
                    return nvectors
                else:
                    # We have some data, return what we have
                    break

            event_number, data = result
            self.total_events_read += 1

            # Check for missing events
            if self.last_event_number >= 0 and event_number != self.last_event_number + 1:
                missed = event_number - self.last_event_number - 1
                print(f"Warning: Missed {missed} event(s) (last={self.last_event_number}, current={event_number})")

            self.last_event_number = event_number

            # Convert bytes to complex samples
            samples = np.frombuffer(data, dtype=np.complex64)

            # Ensure samples match the expected vector length
            if len(samples) != self.vlen:
                print(f"Warning: Event {event_number} has {len(samples)} samples, expected {self.vlen}. Padding/truncating.")
                if len(samples) < self.vlen:
                    # Pad with zeros
                    padded = np.zeros(self.vlen, dtype=np.complex64)
                    padded[:len(samples)] = samples
                    samples = padded
                else:
                    # Truncate
                    samples = samples[:self.vlen]

            # Copy vector to output
            out[vectors_produced] = samples
            vectors_produced += 1
            self.total_samples_read += len(samples)

        # Fill any remaining output with zeros
        if vectors_produced < nvectors:
            out[vectors_produced:] = 0

        return nvectors
