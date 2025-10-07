"""Constants for shared memory FIFO implementation"""

# Header section is 64 bytes
HEADER_SIZE = 64

# Header field offsets (in bytes)
WRITE_INDEX_OFFSET = 0      # 8 bytes - atomic counter for writer position
READ_INDEX_OFFSET = 8        # 8 bytes - atomic counter for reader position
CAPACITY_OFFSET = 16         # 8 bytes - max number of entries
ENTRY_SIZE_OFFSET = 24       # 8 bytes - max size per entry including metadata
TOTAL_WRITES_OFFSET = 32     # 8 bytes - successful writes counter
TOTAL_READS_OFFSET = 40      # 8 bytes - successful reads counter
TOTAL_DROPS_OFFSET = 48      # 8 bytes - failed writes counter
PADDING_OFFSET = 56          # 16 bytes - reserved for future use

# Entry metadata size (event_number + data_size)
ENTRY_METADATA_SIZE = 16     # 8 bytes event_number + 8 bytes data_size

# Struct format for header fields (all unsigned 64-bit integers)
HEADER_FIELD_FORMAT = 'Q'    # unsigned long long (8 bytes)

# Default values
DEFAULT_CAPACITY = 1024
DEFAULT_ENTRY_SIZE = 4096
