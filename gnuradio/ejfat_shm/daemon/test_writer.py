#!/usr/bin/env python3
"""
Simple test writer for EJFAT SHM daemon testing.
Writes events to shared memory FIFO for daemon to forward via EJFAT.
"""

import sys
import time
import signal

# Add parent directory to path to import ejfat_shm
sys.path.insert(0, '..')

from ejfat_shm import ShmFIFO, WriteStatus

def signal_handler(sig, frame):
    print('\nShutdown requested...')
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    # Configuration
    fifo_name = "test_fifo"
    capacity = 100
    entry_size = 4096
    num_events = 1000
    event_delay = 0.1  # seconds between events

    print(f"Creating SHM FIFO: {fifo_name}")
    print(f"  Capacity: {capacity} entries")
    print(f"  Entry size: {entry_size} bytes")
    print(f"  Will send {num_events} events")
    print()

    # Create FIFO
    try:
        fifo = ShmFIFO(fifo_name, capacity=capacity, entry_size=entry_size, create=True)
    except Exception as e:
        print(f"Error creating FIFO: {e}")
        print("If FIFO already exists, remove with:")
        print(f"  rm /dev/shm/ejfat_shm_{fifo_name}*")
        return 1

    print("FIFO created successfully")
    print("Starting event writer (Ctrl+C to stop)...")
    print()

    # Write events
    events_sent = 0
    events_dropped = 0

    try:
        for i in range(num_events):
            # Create event data
            data = f"Test event {i} - timestamp {time.time()}".encode()

            # Write event
            result = fifo.write_event(data, event_number=i)

            if result.status == WriteStatus.SUCCESS:
                events_sent += 1
                if i % 10 == 0:  # Print every 10th event
                    print(f"[{i:4d}] Sent event {i}, size {len(data)} bytes")
            elif result.status == WriteStatus.FIFO_FULL:
                events_dropped += 1
                print(f"[{i:4d}] WARNING: FIFO full! Event {i} dropped. Total drops: {result.total_drops}")
            elif result.status == WriteStatus.DATA_TOO_LARGE:
                events_dropped += 1
                print(f"[{i:4d}] ERROR: Data too large for event {i}")

            # Delay between events
            time.sleep(event_delay)

        print()
        print("=" * 60)
        print(f"Writing completed:")
        print(f"  Events sent: {events_sent}")
        print(f"  Events dropped: {events_dropped}")
        print()

        # Get final statistics
        stats = fifo.get_stats()
        print("FIFO Statistics:")
        print(f"  Total writes: {stats['total_writes']}")
        print(f"  Total reads: {stats['total_reads']}")
        print(f"  Total drops: {stats['total_drops']}")
        print(f"  Entries available: {stats['entries_available']}")
        print()

        # Wait a bit for daemon to read remaining events
        if stats['entries_available'] > 0:
            print(f"Waiting for daemon to read {stats['entries_available']} remaining events...")
            time.sleep(5)

            stats = fifo.get_stats()
            print(f"Remaining entries: {stats['entries_available']}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Cleanup
        print()
        print("Cleaning up...")
        fifo.close()
        fifo.unlink()
        print("FIFO closed and removed")

    return 0

if __name__ == "__main__":
    sys.exit(main())
