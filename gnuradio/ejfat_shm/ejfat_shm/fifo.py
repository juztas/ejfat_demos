"""Shared memory FIFO implementation using POSIX shared memory"""

import mmap
import os
import struct
from enum import Enum
from typing import NamedTuple, Optional, Tuple

import posix_ipc

from .constants import (
    CAPACITY_OFFSET,
    DEFAULT_CAPACITY,
    DEFAULT_ENTRY_SIZE,
    ENTRY_METADATA_SIZE,
    ENTRY_SIZE_OFFSET,
    HEADER_FIELD_FORMAT,
    HEADER_SIZE,
    READ_INDEX_OFFSET,
    TOTAL_DROPS_OFFSET,
    TOTAL_READS_OFFSET,
    TOTAL_WRITES_OFFSET,
    WRITE_INDEX_OFFSET,
)
from .exceptions import ShmFIFOError, ShmFIFOExistsError, ShmFIFONotFoundError


class WriteStatus(Enum):
    """Status codes for write operations"""
    SUCCESS = 0
    FIFO_FULL = 1
    DATA_TOO_LARGE = 2


class WriteResult(NamedTuple):
    """Result of a write operation"""
    status: WriteStatus
    total_drops: int


class ShmFIFO:
    """
    High-performance FIFO queue using POSIX shared memory

    Single-writer, single-reader design with zero-copy data transfer
    and semaphore-based notifications.
    """

    def __init__(
        self,
        name: str,
        capacity: int = DEFAULT_CAPACITY,
        entry_size: int = DEFAULT_ENTRY_SIZE,
        create: bool = True
    ):
        """
        Initialize shared memory FIFO

        Args:
            name: Unique identifier for this FIFO
            capacity: Number of entries in circular buffer
            entry_size: Max bytes per entry (including 16-byte metadata)
            create: True for writer (creates shm/sem), False for reader (opens existing)

        Raises:
            ShmFIFOExistsError: If create=True and shared memory already exists
            ShmFIFONotFoundError: If create=False and shared memory doesn't exist
        """
        self.name = name
        self.capacity = capacity
        self.entry_size = entry_size
        self.create = create

        # Generate unique names for shared memory and semaphore
        self.shm_name = f"/ejfat_shm_{name}"
        self.sem_name = f"/ejfat_shm_{name}_data"

        # Calculate total memory size
        self.total_size = HEADER_SIZE + (capacity * entry_size)

        # Initialize objects
        self.shm: Optional[posix_ipc.SharedMemory] = None
        self.mmap: Optional[mmap.mmap] = None
        self.data_sem: Optional[posix_ipc.Semaphore] = None

        # Open or create shared memory and semaphore
        self._initialize()

    def _initialize(self):
        """Initialize shared memory and semaphore"""
        if self.create:
            # Writer: create shared memory and semaphore
            try:
                self.shm = posix_ipc.SharedMemory(
                    self.shm_name,
                    flags=posix_ipc.O_CREAT | posix_ipc.O_EXCL,
                    mode=0o600,
                    size=self.total_size
                )
            except posix_ipc.ExistentialError:
                raise ShmFIFOExistsError(
                    f"Shared memory '{self.shm_name}' already exists. "
                    "Use create=False to open existing FIFO or unlink() first."
                )

            # Create semaphore (initial value 0 - no data available)
            try:
                self.data_sem = posix_ipc.Semaphore(
                    self.sem_name,
                    flags=posix_ipc.O_CREAT | posix_ipc.O_EXCL,
                    mode=0o600,
                    initial_value=0
                )
            except posix_ipc.ExistentialError:
                self.shm.close_fd()
                self.shm.unlink()
                raise ShmFIFOExistsError(
                    f"Semaphore '{self.sem_name}' already exists"
                )

            # Map memory
            self.mmap = mmap.mmap(self.shm.fd, self.total_size)

            # Initialize header
            self._write_header_field(WRITE_INDEX_OFFSET, 0)
            self._write_header_field(READ_INDEX_OFFSET, 0)
            self._write_header_field(CAPACITY_OFFSET, self.capacity)
            self._write_header_field(ENTRY_SIZE_OFFSET, self.entry_size)
            self._write_header_field(TOTAL_WRITES_OFFSET, 0)
            self._write_header_field(TOTAL_READS_OFFSET, 0)
            self._write_header_field(TOTAL_DROPS_OFFSET, 0)

        else:
            # Reader: open existing shared memory and semaphore
            try:
                self.shm = posix_ipc.SharedMemory(
                    self.shm_name,
                    flags=0
                )
            except posix_ipc.ExistentialError:
                raise ShmFIFONotFoundError(
                    f"Shared memory '{self.shm_name}' not found. "
                    "Ensure writer has created the FIFO first."
                )

            # Open semaphore
            try:
                self.data_sem = posix_ipc.Semaphore(self.sem_name, flags=0)
            except posix_ipc.ExistentialError:
                self.shm.close_fd()
                raise ShmFIFONotFoundError(
                    f"Semaphore '{self.sem_name}' not found"
                )

            # Get actual shared memory size using fstat
            shm_size = os.fstat(self.shm.fd).st_size

            # Map memory using actual size from shared memory object
            self.mmap = mmap.mmap(self.shm.fd, shm_size)

            # Read configuration from header
            self.capacity = self._read_header_field(CAPACITY_OFFSET)
            self.entry_size = self._read_header_field(ENTRY_SIZE_OFFSET)

            # Update total_size based on actual values from header
            self.total_size = HEADER_SIZE + (self.capacity * self.entry_size)

    def _write_header_field(self, offset: int, value: int):
        """Write a 64-bit value to the header"""
        self.mmap.seek(offset)
        self.mmap.write(struct.pack(HEADER_FIELD_FORMAT, value))

    def _read_header_field(self, offset: int) -> int:
        """Read a 64-bit value from the header"""
        self.mmap.seek(offset)
        return struct.unpack(HEADER_FIELD_FORMAT, self.mmap.read(8))[0]

    def _atomic_increment(self, offset: int) -> int:
        """
        Atomically increment a header field and return the new value

        Note: This uses a simple read-modify-write. On x86, aligned 64-bit
        operations are atomic. For other architectures, consider using
        memory barriers or atomic operations.
        """
        value = self._read_header_field(offset)
        new_value = value + 1
        self._write_header_field(offset, new_value)
        return new_value

    def _get_entry_offset(self, index: int) -> int:
        """Calculate memory offset for a given entry index"""
        return HEADER_SIZE + (index * self.entry_size)

    def write_event(self, data: bytes, event_number: int) -> WriteResult:
        """
        Non-blocking write with status feedback

        Args:
            data: Packed byte array to queue
            event_number: 64-bit event identifier

        Returns:
            WriteResult with status and total_drops count
        """
        # Validate data size
        max_data_size = self.entry_size - ENTRY_METADATA_SIZE
        if len(data) > max_data_size:
            drops = self._atomic_increment(TOTAL_DROPS_OFFSET)
            return WriteResult(WriteStatus.DATA_TOO_LARGE, drops)

        # Check if FIFO is full
        write_idx = self._read_header_field(WRITE_INDEX_OFFSET)
        read_idx = self._read_header_field(READ_INDEX_OFFSET)

        if (write_idx - read_idx) >= self.capacity:
            drops = self._atomic_increment(TOTAL_DROPS_OFFSET)
            return WriteResult(WriteStatus.FIFO_FULL, drops)

        # Calculate position in circular buffer
        position = write_idx % self.capacity
        entry_offset = self._get_entry_offset(position)

        # Write entry: [event_number | data_size | data]
        self.mmap.seek(entry_offset)
        self.mmap.write(struct.pack('QQ', event_number, len(data)))
        self.mmap.write(data)

        # Atomically increment write index
        self._atomic_increment(WRITE_INDEX_OFFSET)
        self._atomic_increment(TOTAL_WRITES_OFFSET)

        # Signal data available
        self.data_sem.release()

        # Return success with current drop count
        drops = self._read_header_field(TOTAL_DROPS_OFFSET)
        return WriteResult(WriteStatus.SUCCESS, drops)

    def read_event(self, timeout: Optional[float] = None) -> Optional[Tuple[int, bytes]]:
        """
        Block until data available, then read next entry

        Args:
            timeout: Seconds to wait (None = block forever, 0 = non-blocking)

        Returns:
            (event_number, data) tuple or None if timeout/empty
        """
        # Wait for data to be available
        try:
            self.data_sem.acquire(timeout=timeout)
        except (posix_ipc.BusyError, posix_ipc.SignalError):
            # Timeout expired, non-blocking call with no data, or interrupted by signal
            return None

        # Calculate position in circular buffer
        read_idx = self._read_header_field(READ_INDEX_OFFSET)
        position = read_idx % self.capacity
        entry_offset = self._get_entry_offset(position)

        # Read entry: [event_number | data_size | data]
        self.mmap.seek(entry_offset)
        event_number, data_size = struct.unpack('QQ', self.mmap.read(16))
        data = self.mmap.read(data_size)

        # Atomically increment read index
        self._atomic_increment(READ_INDEX_OFFSET)
        self._atomic_increment(TOTAL_READS_OFFSET)

        return (event_number, data)

    def get_stats(self) -> dict:
        """
        Get current FIFO statistics

        Returns:
            Dictionary with counters and configuration
        """
        write_idx = self._read_header_field(WRITE_INDEX_OFFSET)
        read_idx = self._read_header_field(READ_INDEX_OFFSET)

        return {
            'write_index': write_idx,
            'read_index': read_idx,
            'entries_available': write_idx - read_idx,
            'capacity': self.capacity,
            'entry_size': self.entry_size,
            'total_writes': self._read_header_field(TOTAL_WRITES_OFFSET),
            'total_reads': self._read_header_field(TOTAL_READS_OFFSET),
            'total_drops': self._read_header_field(TOTAL_DROPS_OFFSET),
        }

    def close(self):
        """Unmap memory and close semaphore"""
        if self.mmap:
            self.mmap.close()
            self.mmap = None

        if self.shm:
            self.shm.close_fd()
            self.shm = None

        if self.data_sem:
            self.data_sem.close()
            self.data_sem = None

    def unlink(self):
        """
        Remove shared memory and semaphore (writer only)

        Should be called by the writer process when done
        """
        if not self.create:
            raise ShmFIFOError(
                "unlink() should only be called by the writer (create=True)"
            )

        # Unlink shared memory
        if self.shm:
            try:
                self.shm.unlink()
            except posix_ipc.ExistentialError:
                pass  # Already unlinked

        # Unlink semaphore
        if self.data_sem:
            try:
                self.data_sem.unlink()
            except posix_ipc.ExistentialError:
                pass  # Already unlinked

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        if self.create:
            self.unlink()
