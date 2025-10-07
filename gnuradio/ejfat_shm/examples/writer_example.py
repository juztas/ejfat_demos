#!/usr/bin/env python3
"""Example writer process using ShmFIFO"""

import time
import struct
from ejfat_shm import ShmFIFO, WriteStatus


def main():
    # Create FIFO (writer is responsible for creation)
    print("Creating FIFO 'my_fifo' with capacity=100, entry_size=4096")
    fifo = ShmFIFO("my_fifo", capacity=100, entry_size=4096, create=True)

    try:
        # Send some events
        for i in range(150):
            # Pack some data (example: timestamp + sequence number)
            timestamp = time.time()
            data = struct.pack('di', timestamp, i)
            event_num = i + 1000

            # Write to FIFO
            result = fifo.write_event(data, event_num)

            if result.status == WriteStatus.SUCCESS:
                print(f"Event {event_num}: Written successfully (drops: {result.total_drops})")
            elif result.status == WriteStatus.FIFO_FULL:
                print(f"Event {event_num}: FIFO FULL! Total drops: {result.total_drops}")
                # Handle backpressure - in real application might:
                # - Log to external system
                # - Trigger alerts
                # - Shed load
                # - Wait and retry
                time.sleep(0.1)  # Simple backoff
            elif result.status == WriteStatus.DATA_TOO_LARGE:
                print(f"Event {event_num}: Data too large! Total drops: {result.total_drops}")

            # Add small delay to simulate real workload
            time.sleep(0.05)

        # Print final statistics
        stats = fifo.get_stats()
        print("\nFinal Statistics:")
        print(f"  Total writes: {stats['total_writes']}")
        print(f"  Total drops: {stats['total_drops']}")
        print(f"  Entries available: {stats['entries_available']}")

    finally:
        # Cleanup
        print("\nCleaning up...")
        fifo.close()
        fifo.unlink()
        print("Done!")


if __name__ == "__main__":
    main()
