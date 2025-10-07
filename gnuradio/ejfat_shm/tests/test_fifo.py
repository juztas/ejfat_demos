#!/usr/bin/env python3
"""Unit tests for ShmFIFO"""

import multiprocessing
import time
import pytest
from ejfat_shm import (
    ShmFIFO,
    WriteStatus,
    ShmFIFOExistsError,
    ShmFIFONotFoundError,
)


class TestShmFIFOBasic:
    """Basic functionality tests"""

    def test_create_and_close(self):
        """Test creating and closing a FIFO"""
        fifo = ShmFIFO("test_create", capacity=10, entry_size=1024, create=True)
        assert fifo is not None
        fifo.close()
        fifo.unlink()

    def test_context_manager(self):
        """Test using FIFO as context manager"""
        with ShmFIFO("test_context", capacity=10, entry_size=1024, create=True) as fifo:
            assert fifo is not None

    def test_cannot_create_twice(self):
        """Test that creating same FIFO twice raises error"""
        fifo1 = ShmFIFO("test_twice", capacity=10, entry_size=1024, create=True)
        try:
            with pytest.raises(ShmFIFOExistsError):
                fifo2 = ShmFIFO("test_twice", capacity=10, entry_size=1024, create=True)
        finally:
            fifo1.close()
            fifo1.unlink()

    def test_open_nonexistent(self):
        """Test opening non-existent FIFO raises error"""
        with pytest.raises(ShmFIFONotFoundError):
            fifo = ShmFIFO("nonexistent", create=False)


class TestShmFIFOWriteRead:
    """Write and read tests"""

    def test_single_write_read(self):
        """Test writing and reading a single event"""
        fifo = ShmFIFO("test_single", capacity=10, entry_size=1024, create=True)

        # Write
        data = b"Hello, World!"
        result = fifo.write_event(data, 12345)
        assert result.status == WriteStatus.SUCCESS
        assert result.total_drops == 0

        # Read (non-blocking with timeout)
        event_num, read_data = fifo.read_event(timeout=0)
        assert event_num == 12345
        assert read_data == data

        fifo.close()
        fifo.unlink()

    def test_multiple_events(self):
        """Test writing and reading multiple events"""
        fifo = ShmFIFO("test_multiple", capacity=100, entry_size=1024, create=True)

        num_events = 50
        for i in range(num_events):
            data = f"Event {i}".encode()
            result = fifo.write_event(data, i)
            assert result.status == WriteStatus.SUCCESS

        for i in range(num_events):
            event_num, data = fifo.read_event(timeout=1.0)
            assert event_num == i
            assert data == f"Event {i}".encode()

        fifo.close()
        fifo.unlink()

    def test_fifo_full(self):
        """Test FIFO full condition"""
        capacity = 5
        fifo = ShmFIFO("test_full", capacity=capacity, entry_size=1024, create=True)

        # Fill FIFO
        for i in range(capacity):
            result = fifo.write_event(b"data", i)
            assert result.status == WriteStatus.SUCCESS

        # Next write should fail
        result = fifo.write_event(b"overflow", 999)
        assert result.status == WriteStatus.FIFO_FULL
        assert result.total_drops == 1

        fifo.close()
        fifo.unlink()

    def test_data_too_large(self):
        """Test data too large error"""
        entry_size = 100
        fifo = ShmFIFO("test_large", capacity=10, entry_size=entry_size, create=True)

        # Data that's too large (entry_size - 16 metadata = 84 max)
        large_data = b"X" * 200
        result = fifo.write_event(large_data, 1)
        assert result.status == WriteStatus.DATA_TOO_LARGE
        assert result.total_drops == 1

        fifo.close()
        fifo.unlink()

    def test_read_timeout(self):
        """Test read timeout when no data available"""
        fifo = ShmFIFO("test_timeout", capacity=10, entry_size=1024, create=True)

        # Read with short timeout should return None
        result = fifo.read_event(timeout=0.1)
        assert result is None

        fifo.close()
        fifo.unlink()

    def test_circular_buffer(self):
        """Test that circular buffer wraps correctly"""
        capacity = 5
        fifo = ShmFIFO("test_circular", capacity=capacity, entry_size=1024, create=True)

        # Write and read more than capacity to test wrap-around
        num_events = 20
        for i in range(num_events):
            result = fifo.write_event(f"Event {i}".encode(), i)
            # Should succeed as we read immediately
            assert result.status == WriteStatus.SUCCESS

            event_num, data = fifo.read_event(timeout=0)
            assert event_num == i
            assert data == f"Event {i}".encode()

        fifo.close()
        fifo.unlink()


class TestShmFIFOStatistics:
    """Statistics tests"""

    def test_stats(self):
        """Test statistics reporting"""
        fifo = ShmFIFO("test_stats", capacity=10, entry_size=1024, create=True)

        # Initial stats
        stats = fifo.get_stats()
        assert stats['total_writes'] == 0
        assert stats['total_reads'] == 0
        assert stats['total_drops'] == 0
        assert stats['capacity'] == 10
        assert stats['entry_size'] == 1024

        # Write some events
        for i in range(3):
            fifo.write_event(b"data", i)

        stats = fifo.get_stats()
        assert stats['total_writes'] == 3
        assert stats['entries_available'] == 3

        # Read one event
        fifo.read_event(timeout=0)

        stats = fifo.get_stats()
        assert stats['total_reads'] == 1
        assert stats['entries_available'] == 2

        fifo.close()
        fifo.unlink()


class TestShmFIFOMultiprocess:
    """Multi-process tests"""

    def test_writer_reader_processes(self):
        """Test writer and reader in separate processes"""

        def writer(fifo_name, num_events):
            fifo = ShmFIFO(fifo_name, capacity=100, entry_size=1024, create=True)
            for i in range(num_events):
                fifo.write_event(f"Event {i}".encode(), i)
                time.sleep(0.01)
            fifo.close()
            fifo.unlink()

        def reader(fifo_name, num_events, result_queue):
            time.sleep(0.1)  # Wait for writer to create FIFO
            fifo = ShmFIFO(fifo_name, create=False)
            events = []
            for _ in range(num_events):
                result = fifo.read_event(timeout=5.0)
                if result:
                    events.append(result)
            fifo.close()
            result_queue.put(events)

        fifo_name = "test_multiproc"
        num_events = 10
        result_queue = multiprocessing.Queue()

        writer_proc = multiprocessing.Process(target=writer, args=(fifo_name, num_events))
        reader_proc = multiprocessing.Process(target=reader, args=(fifo_name, num_events, result_queue))

        writer_proc.start()
        reader_proc.start()

        writer_proc.join(timeout=10)
        reader_proc.join(timeout=10)

        # Verify results
        events = result_queue.get()
        assert len(events) == num_events
        for i, (event_num, data) in enumerate(events):
            assert event_num == i
            assert data == f"Event {i}".encode()


class TestShmFIFOEdgeCases:
    """Edge case tests"""

    def test_zero_length_data(self):
        """Test writing zero-length data"""
        fifo = ShmFIFO("test_zero", capacity=10, entry_size=1024, create=True)

        result = fifo.write_event(b"", 123)
        assert result.status == WriteStatus.SUCCESS

        event_num, data = fifo.read_event(timeout=0)
        assert event_num == 123
        assert data == b""

        fifo.close()
        fifo.unlink()

    def test_max_size_data(self):
        """Test writing maximum size data"""
        entry_size = 1024
        max_data_size = entry_size - 16  # minus metadata
        fifo = ShmFIFO("test_maxsize", capacity=10, entry_size=entry_size, create=True)

        data = b"X" * max_data_size
        result = fifo.write_event(data, 456)
        assert result.status == WriteStatus.SUCCESS

        event_num, read_data = fifo.read_event(timeout=0)
        assert event_num == 456
        assert len(read_data) == max_data_size
        assert read_data == data

        fifo.close()
        fifo.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
