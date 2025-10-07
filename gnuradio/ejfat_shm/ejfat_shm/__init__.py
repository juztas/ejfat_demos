"""ejfat_shm: High-performance FIFO queue using POSIX shared memory"""

from .fifo import ShmFIFO, WriteStatus, WriteResult
from .exceptions import (
    ShmFIFOError,
    ShmFIFOFullError,
    ShmFIFODataTooLargeError,
    ShmFIFOExistsError,
    ShmFIFONotFoundError,
)

__version__ = "0.1.0"

__all__ = [
    "ShmFIFO",
    "WriteStatus",
    "WriteResult",
    "ShmFIFOError",
    "ShmFIFOFullError",
    "ShmFIFODataTooLargeError",
    "ShmFIFOExistsError",
    "ShmFIFONotFoundError",
]
