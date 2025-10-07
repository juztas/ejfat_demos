"""Custom exceptions for shared memory FIFO"""


class ShmFIFOError(Exception):
    """Base exception for all ShmFIFO errors"""
    pass


class ShmFIFOFullError(ShmFIFOError):
    """Raised when attempting to write to a full FIFO"""
    pass


class ShmFIFODataTooLargeError(ShmFIFOError):
    """Raised when data is larger than the entry size"""
    pass


class ShmFIFONotFoundError(ShmFIFOError):
    """Raised when attempting to open non-existent shared memory"""
    pass


class ShmFIFOExistsError(ShmFIFOError):
    """Raised when attempting to create already existing shared memory"""
    pass
