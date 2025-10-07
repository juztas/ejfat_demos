#!/usr/bin/env python3
"""Example reader process using ShmFIFO"""

import struct
from ejfat_shm import ShmFIFO


def main():
    # Open existing FIFO (reader doesn't create)
    print("Opening existing FIFO 'my_fifo'")
    print("Waiting for writer to create it...")

    # In real application, might want retry logic here
    try:
        fifo = ShmFIFO("my_fifo", create=False)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the writer process is running first!")
        return

    print("Connected to FIFO!")
    print("Reading events (Ctrl+C to stop)...\n")

    try:
        events_read = 0
        while True:
            # Read with 5 second timeout
            result = fifo.read_event(timeout=5.0)

            if result:
                event_num, data = result
                events_read += 1

                # Unpack data (matching writer format)
                timestamp, sequence = struct.unpack('di', data)

                print(f"Event {event_num}: seq={sequence}, timestamp={timestamp:.6f}")

                # Every 10 events, show statistics
                if events_read % 10 == 0:
                    stats = fifo.get_stats()
                    print(f"  [Stats: reads={stats['total_reads']}, "
                          f"available={stats['entries_available']}, "
                          f"total_drops={stats['total_drops']}]")
            else:
                print("No data for 5 seconds, checking again...")
                # In real application might:
                # - Exit if expected end of stream
                # - Check if writer is still alive
                # - Continue waiting

    except KeyboardInterrupt:
        print("\n\nShutting down...")

    finally:
        # Print final statistics
        stats = fifo.get_stats()
        print("\nFinal Statistics:")
        print(f"  Total reads: {stats['total_reads']}")
        print(f"  Total writes: {stats['total_writes']}")
        print(f"  Total drops: {stats['total_drops']}")
        print(f"  Remaining entries: {stats['entries_available']}")

        # Cleanup
        fifo.close()
        print("Done!")


if __name__ == "__main__":
    main()
