#!/usr/bin/env python3
"""Benchmark ShmFIFO performance"""

import multiprocessing
import time
import struct
from ejfat_shm import ShmFIFO, WriteStatus


def writer_process(fifo_name: str, num_events: int, entry_size: int):
    """Writer process for benchmarking"""
    fifo = ShmFIFO(fifo_name, capacity=1024, entry_size=entry_size, create=True)

    # Prepare test data (fill to max size for worst case)
    max_data_size = entry_size - 16  # minus metadata
    test_data = b'X' * max_data_size

    print(f"Writer: Sending {num_events} events of {max_data_size} bytes each")

    start_time = time.time()
    successful = 0
    dropped = 0

    for i in range(num_events):
        result = fifo.write_event(test_data, i)
        if result.status == WriteStatus.SUCCESS:
            successful += 1
        else:
            dropped += 1

    end_time = time.time()
    elapsed = end_time - start_time

    stats = fifo.get_stats()

    print(f"\nWriter Statistics:")
    print(f"  Duration: {elapsed:.3f} seconds")
    print(f"  Events sent: {num_events}")
    print(f"  Successful writes: {successful}")
    print(f"  Dropped: {dropped}")
    print(f"  Throughput: {successful/elapsed:.0f} events/sec")
    print(f"  Bandwidth: {(successful * max_data_size)/(elapsed * 1024 * 1024):.2f} MB/sec")
    print(f"  Total writes from stats: {stats['total_writes']}")
    print(f"  Total drops from stats: {stats['total_drops']}")

    # Give reader time to catch up
    time.sleep(2)

    fifo.close()
    fifo.unlink()


def reader_process(fifo_name: str, expected_events: int):
    """Reader process for benchmarking"""
    # Wait for writer to create FIFO
    time.sleep(0.5)

    fifo = ShmFIFO(fifo_name, create=False)

    print("Reader: Starting to read events")

    start_time = time.time()
    events_read = 0
    bytes_read = 0

    while events_read < expected_events:
        result = fifo.read_event(timeout=5.0)
        if result:
            event_num, data = result
            events_read += 1
            bytes_read += len(data)
        else:
            # Timeout - writer might be done
            break

    end_time = time.time()
    elapsed = end_time - start_time

    stats = fifo.get_stats()

    print(f"\nReader Statistics:")
    print(f"  Duration: {elapsed:.3f} seconds")
    print(f"  Events read: {events_read}")
    print(f"  Bytes read: {bytes_read}")
    print(f"  Throughput: {events_read/elapsed:.0f} events/sec")
    print(f"  Bandwidth: {bytes_read/(elapsed * 1024 * 1024):.2f} MB/sec")
    print(f"  Total reads from stats: {stats['total_reads']}")
    print(f"  Final drops: {stats['total_drops']}")

    fifo.close()


def run_benchmark(num_events: int = 100000, entry_size: int = 4096):
    """Run a benchmark with writer and reader processes"""
    fifo_name = "benchmark_fifo"

    print("=" * 60)
    print(f"ShmFIFO Benchmark")
    print(f"  Events: {num_events}")
    print(f"  Entry size: {entry_size} bytes")
    print(f"  Capacity: 1024 entries")
    print("=" * 60)

    # Create processes
    writer = multiprocessing.Process(
        target=writer_process,
        args=(fifo_name, num_events, entry_size)
    )
    reader = multiprocessing.Process(
        target=reader_process,
        args=(fifo_name, num_events)
    )

    # Start processes
    writer.start()
    reader.start()

    # Wait for completion
    writer.join()
    reader.join()

    print("\n" + "=" * 60)
    print("Benchmark complete!")
    print("=" * 60)


def run_latency_test(num_samples: int = 1000):
    """Test round-trip latency"""
    fifo_name = "latency_fifo"

    print("\n" + "=" * 60)
    print("Latency Test (single event round-trip)")
    print("=" * 60)

    def writer():
        fifo = ShmFIFO(fifo_name, capacity=10, entry_size=1024, create=True)
        time.sleep(0.5)  # Let reader connect

        latencies = []

        for i in range(num_samples):
            # Write timestamp
            start = time.perf_counter()
            data = struct.pack('d', start)
            fifo.write_event(data, i)

            # Simple delay between messages
            time.sleep(0.001)

        fifo.close()
        fifo.unlink()

    def reader():
        time.sleep(0.3)
        fifo = ShmFIFO(fifo_name, create=False)

        latencies = []

        for i in range(num_samples):
            result = fifo.read_event(timeout=5.0)
            if result:
                end = time.perf_counter()
                event_num, data = result
                start = struct.unpack('d', data)[0]
                latency = (end - start) * 1000000  # microseconds
                latencies.append(latency)

        if latencies:
            latencies.sort()
            print(f"\nLatency Statistics ({len(latencies)} samples):")
            print(f"  Min: {min(latencies):.2f} μs")
            print(f"  Max: {max(latencies):.2f} μs")
            print(f"  Mean: {sum(latencies)/len(latencies):.2f} μs")
            print(f"  Median: {latencies[len(latencies)//2]:.2f} μs")
            print(f"  P95: {latencies[int(len(latencies)*0.95)]:.2f} μs")
            print(f"  P99: {latencies[int(len(latencies)*0.99)]:.2f} μs")

        fifo.close()

    w = multiprocessing.Process(target=writer)
    r = multiprocessing.Process(target=reader)

    w.start()
    r.start()

    w.join()
    r.join()


if __name__ == "__main__":
    import sys

    # Run throughput benchmark
    if len(sys.argv) > 1:
        num_events = int(sys.argv[1])
    else:
        num_events = 100000

    if len(sys.argv) > 2:
        entry_size = int(sys.argv[2])
    else:
        entry_size = 4096

    run_benchmark(num_events, entry_size)

    # Run latency test
    run_latency_test(1000)
