#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 gr-ejfat author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr
from ejfat_shm import ShmFIFO, WriteStatus, ShmFIFOExistsError
import posix_ipc

class ejfat_shm_sink(gr.sync_block):
    """
    Sink block that writes complex vectors to shared memory FIFO.

    Uses ejfat_shm package for high-performance inter-process communication
    via POSIX shared memory with semaphore-based synchronization.

    Args:
        shm_name: Unique identifier for the shared memory FIFO
        capacity: Number of entries in circular buffer (default: 1024)
        entry_size: Maximum bytes per entry including metadata (default: 4096)
        vlen: Vector length for input (default: 1024)
    """
    def __init__(self, shm_name='ejfat_fifo', capacity=1024, entry_size=4096, vlen=1024):
        gr.sync_block.__init__(self,
            name="ejfat_shm_sink",
            in_sig=[(np.complex64, vlen)],
            out_sig=None)

        self.shm_name = shm_name
        self.capacity = capacity
        self.entry_size = entry_size
        self.vlen = vlen
        self.fifo = None
        self.event_number = 0
        self.total_samples_written = 0
        self.last_drop_count = 0

    def start(self):
        """Create shared memory FIFO when flowgraph starts"""
        # Clean up any existing shared memory objects from previous runs
        self._cleanup_existing_shm()

        try:
            self.fifo = ShmFIFO(
                name=self.shm_name,
                capacity=self.capacity,
                entry_size=self.entry_size,
                create=True
            )
            self.event_number = 0
            self.total_samples_written = 0
            self.last_drop_count = 0
            print(f"ShmFIFO Sink created: {self.shm_name} (capacity={self.capacity}, entry_size={self.entry_size})")
            return True
        except ShmFIFOExistsError as e:
            print(f"Error: {e}")
            print(f"Hint: Shared memory '{self.shm_name}' already exists. Clean it up first or use a different name.")
            return False
        except Exception as e:
            print(f"Error creating ShmFIFO: {e}")
            return False

    def _cleanup_existing_shm(self):
        """Clean up any existing shared memory objects and semaphores"""
        # The ejfat_shm package uses these naming conventions
        shm_name = f'/ejfat_shm_{self.shm_name}'
        sem_name = f'/ejfat_shm_{self.shm_name}_data'

        for resource_name in [shm_name, sem_name]:
            try:
                if '_data' in resource_name:
                    posix_ipc.unlink_semaphore(resource_name)
                    print(f"Cleaned up existing semaphore: {resource_name}")
                else:
                    posix_ipc.unlink_shared_memory(resource_name)
                    print(f"Cleaned up existing shared memory: {resource_name}")
            except posix_ipc.ExistentialError:
                # Resource doesn't exist, nothing to clean up
                pass
            except Exception as e:
                print(f"Warning: Could not clean up {resource_name}: {e}")

    def stop(self):
        """Close and unlink shared memory FIFO when flowgraph stops"""
        if self.fifo:
            stats = self.fifo.get_stats()
            print(f"\nShmFIFO Sink statistics:")
            print(f"  Total samples written: {self.total_samples_written}")
            print(f"  Total events written: {stats['total_writes']}")
            print(f"  Total drops: {stats['total_drops']}")

            self.fifo.close()
            self.fifo.unlink()
            self.fifo = None
        return True

    def work(self, input_items, output_items):
        """Write complex vectors to shared memory FIFO"""
        in0 = input_items[0]

        if not self.fifo:
            # FIFO not initialized, drop samples
            return len(in0)

        # Process each vector as a separate event
        for vector in in0:
            # Convert complex vector to bytes
            data = vector.tobytes()

            # Write to shared memory FIFO
            result = self.fifo.write_event(data, self.event_number)

            if result.status == WriteStatus.SUCCESS:
                self.event_number += 1
                self.total_samples_written += len(vector)

                # Check if drops occurred
                if result.total_drops > self.last_drop_count:
                    drops_since_last = result.total_drops - self.last_drop_count
                    print(f"Warning: {drops_since_last} event(s) dropped (FIFO full or data too large)")
                    self.last_drop_count = result.total_drops

            elif result.status == WriteStatus.FIFO_FULL:
                # FIFO is full, drop this batch
                # Event already counted in total_drops
                if result.total_drops > self.last_drop_count:
                    self.last_drop_count = result.total_drops

            elif result.status == WriteStatus.DATA_TOO_LARGE:
                # Data too large for entry size
                print(f"Error: Data size ({len(data)} bytes) exceeds maximum entry size ({self.entry_size - 16} bytes)")
                if result.total_drops > self.last_drop_count:
                    self.last_drop_count = result.total_drops

        return len(in0)
