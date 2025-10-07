/**
 * @file shm_reader.c
 * @brief Shared Memory FIFO Reader Implementation
 *
 * C implementation of SHM FIFO reader compatible with Python ejfat_shm package.
 */

#include "shm_reader.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <errno.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <semaphore.h>
#include <time.h>

#define MAX_NAME_LEN 256
#define MAX_ERROR_LEN 512
#define HEADER_SIZE sizeof(shm_header_t)

/**
 * Internal reader structure
 */
struct shm_fifo_reader {
    char name[MAX_NAME_LEN];
    char shm_name[MAX_NAME_LEN];
    char sem_name[MAX_NAME_LEN];

    int shm_fd;
    size_t shm_size;
    void *shm_ptr;

    sem_t *data_sem;

    shm_header_t *header;
    uint8_t *entries_base;

    /* Buffer for current read event */
    uint8_t *read_buffer;
    size_t read_buffer_size;

    char error_msg[MAX_ERROR_LEN];
};

/**
 * Set error message
 */
static void set_error(shm_fifo_reader_t *reader, const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    vsnprintf(reader->error_msg, MAX_ERROR_LEN, fmt, args);
    va_end(args);
}

/**
 * Create and open a SHM FIFO reader
 */
shm_fifo_reader_t* shm_fifo_open(const char *name) {
    if (!name) {
        return NULL;
    }

    shm_fifo_reader_t *reader = calloc(1, sizeof(shm_fifo_reader_t));
    if (!reader) {
        return NULL;
    }

    reader->shm_fd = -1;
    reader->data_sem = SEM_FAILED;

    /* Store name and construct SHM/semaphore names */
    snprintf(reader->name, MAX_NAME_LEN, "%s", name);
    snprintf(reader->shm_name, MAX_NAME_LEN, "/ejfat_shm_%s", name);
    snprintf(reader->sem_name, MAX_NAME_LEN, "/ejfat_shm_%s_data", name);

    /* Open existing shared memory */
    reader->shm_fd = shm_open(reader->shm_name, O_RDWR, 0666);
    if (reader->shm_fd < 0) {
        set_error(reader, "Failed to open shared memory '%s': %s",
                  reader->shm_name, strerror(errno));
        goto error;
    }

    /* Get size of shared memory */
    struct stat st;
    if (fstat(reader->shm_fd, &st) < 0) {
        set_error(reader, "Failed to stat shared memory: %s", strerror(errno));
        goto error;
    }
    reader->shm_size = st.st_size;

    /* Map shared memory */
    reader->shm_ptr = mmap(NULL, reader->shm_size, PROT_READ | PROT_WRITE,
                           MAP_SHARED, reader->shm_fd, 0);
    if (reader->shm_ptr == MAP_FAILED) {
        set_error(reader, "Failed to mmap shared memory: %s", strerror(errno));
        goto error;
    }

    /* Set up header and entries pointers */
    reader->header = (shm_header_t *)reader->shm_ptr;
    reader->entries_base = (uint8_t *)reader->shm_ptr + HEADER_SIZE;

    /* Validate header */
    if (reader->header->capacity == 0 || reader->header->entry_size == 0) {
        set_error(reader, "Invalid FIFO header: capacity=%lu, entry_size=%lu",
                  reader->header->capacity, reader->header->entry_size);
        goto error;
    }

    /* Allocate read buffer */
    reader->read_buffer_size = reader->header->entry_size - sizeof(entry_metadata_t);
    reader->read_buffer = malloc(reader->read_buffer_size);
    if (!reader->read_buffer) {
        set_error(reader, "Failed to allocate read buffer");
        goto error;
    }

    /* Open data semaphore */
    reader->data_sem = sem_open(reader->sem_name, 0);
    if (reader->data_sem == SEM_FAILED) {
        set_error(reader, "Failed to open semaphore '%s': %s",
                  reader->sem_name, strerror(errno));
        goto error;
    }

    return reader;

error:
    shm_fifo_close(reader);
    return NULL;
}

/**
 * Read an event from the FIFO
 */
int shm_fifo_read(shm_fifo_reader_t *reader, double timeout_sec, shm_read_result_t *result) {
    if (!reader || !result) {
        return -1;
    }

    memset(result, 0, sizeof(shm_read_result_t));

    /* Wait on semaphore */
    int sem_ret;
    if (timeout_sec < 0) {
        /* Infinite timeout */
        sem_ret = sem_wait(reader->data_sem);
    } else if (timeout_sec == 0) {
        /* Non-blocking */
        sem_ret = sem_trywait(reader->data_sem);
    } else {
        /* Timed wait */
        struct timespec ts;
        if (clock_gettime(CLOCK_REALTIME, &ts) < 0) {
            set_error(reader, "clock_gettime failed: %s", strerror(errno));
            result->status = SHM_READ_ERROR;
            return -1;
        }

        /* Add timeout */
        long nsec = ts.tv_nsec + (long)((timeout_sec - (long)timeout_sec) * 1e9);
        ts.tv_sec += (long)timeout_sec + nsec / 1000000000L;
        ts.tv_nsec = nsec % 1000000000L;

        sem_ret = sem_timedwait(reader->data_sem, &ts);
    }

    if (sem_ret < 0) {
        if (errno == ETIMEDOUT || errno == EAGAIN) {
            result->status = SHM_READ_TIMEOUT;
            return 0;
        } else {
            set_error(reader, "sem_wait failed: %s", strerror(errno));
            result->status = SHM_READ_ERROR;
            return -1;
        }
    }

    /* Read from circular buffer */
    uint64_t read_idx = __sync_fetch_and_add(&reader->header->read_index, 0);
    uint64_t write_idx = __sync_fetch_and_add(&reader->header->write_index, 0);

    /* Check if data available (should be, since semaphore was posted) */
    if (read_idx >= write_idx) {
        result->status = SHM_READ_EMPTY;
        return 0;
    }

    /* Calculate position in circular buffer */
    uint64_t pos = read_idx % reader->header->capacity;
    uint64_t entry_offset = pos * reader->header->entry_size;
    uint8_t *entry_ptr = reader->entries_base + entry_offset;

    /* Read metadata */
    entry_metadata_t *meta = (entry_metadata_t *)entry_ptr;
    uint64_t event_number = meta->event_number;
    uint64_t data_size = meta->data_size;

    /* Validate data size */
    if (data_size > reader->read_buffer_size) {
        set_error(reader, "Data size %lu exceeds buffer size %lu",
                  data_size, reader->read_buffer_size);
        result->status = SHM_READ_ERROR;
        return -1;
    }

    /* Copy data to read buffer */
    memcpy(reader->read_buffer, entry_ptr + sizeof(entry_metadata_t), data_size);

    /* Atomically increment read index */
    __sync_fetch_and_add(&reader->header->read_index, 1);

    /* Return result */
    result->status = SHM_READ_SUCCESS;
    result->event_number = event_number;
    result->data = reader->read_buffer;
    result->data_size = data_size;

    return 0;
}

/**
 * Get FIFO statistics
 */
int shm_fifo_get_stats(shm_fifo_reader_t *reader, shm_stats_t *stats) {
    if (!reader || !stats) {
        return -1;
    }

    memset(stats, 0, sizeof(shm_stats_t));

    stats->write_index = __sync_fetch_and_add(&reader->header->write_index, 0);
    stats->read_index = __sync_fetch_and_add(&reader->header->read_index, 0);
    stats->capacity = reader->header->capacity;
    stats->entry_size = reader->header->entry_size;
    stats->total_writes = __sync_fetch_and_add(&reader->header->total_writes, 0);
    stats->total_reads = __sync_fetch_and_add(&reader->header->total_reads, 0);
    stats->total_drops = __sync_fetch_and_add(&reader->header->total_drops, 0);
    stats->entries_available = (stats->write_index > stats->read_index) ?
                               (stats->write_index - stats->read_index) : 0;

    return 0;
}

/**
 * Close the reader
 */
void shm_fifo_close(shm_fifo_reader_t *reader) {
    if (!reader) {
        return;
    }

    if (reader->read_buffer) {
        free(reader->read_buffer);
    }

    if (reader->data_sem != SEM_FAILED) {
        sem_close(reader->data_sem);
    }

    if (reader->shm_ptr != NULL && reader->shm_ptr != MAP_FAILED) {
        munmap(reader->shm_ptr, reader->shm_size);
    }

    if (reader->shm_fd >= 0) {
        close(reader->shm_fd);
    }

    free(reader);
}

/**
 * Get last error message
 */
const char* shm_fifo_get_error(shm_fifo_reader_t *reader) {
    if (!reader) {
        return "Invalid reader handle";
    }
    return reader->error_msg;
}
