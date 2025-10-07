/**
 * @file shm_reader.h
 * @brief Shared Memory FIFO Reader for EJFAT
 *
 * C implementation of SHM FIFO reader compatible with the Python ejfat_shm package.
 * Provides read-only access to shared memory FIFO for event broadcasting.
 */

#ifndef SHM_READER_H
#define SHM_READER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * SHM FIFO Header Layout (64 bytes total)
 * Must match Python implementation in ejfat_shm/fifo.py
 */
typedef struct {
    uint64_t write_index;   /* Atomic counter for writer position */
    uint64_t read_index;    /* Atomic counter for reader position */
    uint64_t capacity;      /* Max number of entries in circular buffer */
    uint64_t entry_size;    /* Max size per entry including metadata */
    uint64_t total_writes;  /* Successful writes counter */
    uint64_t total_reads;   /* Successful reads counter */
    uint64_t total_drops;   /* Failed writes counter */
    uint64_t padding[2];    /* Reserved for future use (16 bytes) */
} __attribute__((packed)) shm_header_t;

/**
 * Entry metadata (16 bytes per entry)
 */
typedef struct {
    uint64_t event_number;  /* Event identifier */
    uint64_t data_size;     /* Actual data size in bytes */
} __attribute__((packed)) entry_metadata_t;

/**
 * SHM FIFO Reader handle
 */
typedef struct shm_fifo_reader shm_fifo_reader_t;

/**
 * Read result status codes
 */
typedef enum {
    SHM_READ_SUCCESS = 0,
    SHM_READ_TIMEOUT = 1,
    SHM_READ_ERROR = 2,
    SHM_READ_EMPTY = 3
} shm_read_status_t;

/**
 * Read result structure
 */
typedef struct {
    shm_read_status_t status;
    uint64_t event_number;
    uint8_t *data;
    size_t data_size;
} shm_read_result_t;

/**
 * Statistics structure
 */
typedef struct {
    uint64_t write_index;
    uint64_t read_index;
    uint64_t capacity;
    uint64_t entry_size;
    uint64_t total_writes;
    uint64_t total_reads;
    uint64_t total_drops;
    uint64_t entries_available;
} shm_stats_t;

/**
 * Create and open a SHM FIFO reader
 *
 * @param name FIFO name (must match the writer's name)
 * @return Reader handle or NULL on error
 */
shm_fifo_reader_t* shm_fifo_open(const char *name);

/**
 * Read an event from the FIFO (blocking)
 *
 * Waits on semaphore until data is available, then reads the next entry.
 * The returned data buffer is valid until the next call to shm_fifo_read()
 * or shm_fifo_close().
 *
 * @param reader Reader handle
 * @param timeout_sec Timeout in seconds (0 = non-blocking, negative = infinite)
 * @param result Output parameter for read result
 * @return 0 on success, -1 on error
 */
int shm_fifo_read(shm_fifo_reader_t *reader, double timeout_sec, shm_read_result_t *result);

/**
 * Get FIFO statistics
 *
 * @param reader Reader handle
 * @param stats Output parameter for statistics
 * @return 0 on success, -1 on error
 */
int shm_fifo_get_stats(shm_fifo_reader_t *reader, shm_stats_t *stats);

/**
 * Close the reader and release resources
 *
 * @param reader Reader handle
 */
void shm_fifo_close(shm_fifo_reader_t *reader);

/**
 * Get last error message
 *
 * @param reader Reader handle
 * @return Error message string (valid until next API call)
 */
const char* shm_fifo_get_error(shm_fifo_reader_t *reader);

#ifdef __cplusplus
}
#endif

#endif /* SHM_READER_H */
