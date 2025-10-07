/**
 * @file ejfat_shm_daemon.cpp
 * @brief EJFAT SHM to Network Bridge Daemon
 *
 * Reads events from shared memory FIFO and broadcasts them using EJFAT protocol.
 */

#include <iostream>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <cstdarg>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <syslog.h>
#include <pthread.h>
#include <atomic>

/* E2SAR includes */
#include "e2sar.hpp"

/* Local includes */
extern "C" {
#include "shm_reader.h"
#include "config.h"
}

/* Global state */
static std::atomic<bool> g_running{true};
static daemon_config_t g_config;
static shm_fifo_reader_t *g_reader = nullptr;
static e2sar::Segmenter *g_segmenter = nullptr;

/**
 * Logging helper
 */
#define LOG_ERROR   0
#define LOG_WARN    1
#define LOG_INFO    2
#define LOG_DEBUG   3

static void log_message(int level, const char *fmt, ...) {
    if (level > g_config.log_level) {
        return;
    }

    va_list args;
    va_start(args, fmt);

    if (g_config.foreground) {
        const char *prefix[] = {"ERROR", "WARN", "INFO", "DEBUG"};
        fprintf(stderr, "[%s] ", prefix[level]);
        vfprintf(stderr, fmt, args);
        fprintf(stderr, "\n");
    } else {
        int priority[] = {LOG_ERR, LOG_WARNING, LOG_INFO, LOG_DEBUG};
        vsyslog(priority[level], fmt, args);
    }

    va_end(args);
}

/**
 * Signal handler
 */
static void signal_handler(int signum) {
    log_message(LOG_INFO, "Received signal %d, shutting down...", signum);
    g_running = false;
}

/**
 * Setup signal handlers
 */
static void setup_signals() {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;

    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGHUP, &sa, NULL);

    /* Ignore SIGPIPE */
    signal(SIGPIPE, SIG_IGN);
}

/**
 * Daemonize process
 */
static int daemonize() {
    pid_t pid;

    /* Fork and exit parent */
    pid = fork();
    if (pid < 0) {
        return -1;
    }
    if (pid > 0) {
        exit(EXIT_SUCCESS);
    }

    /* Create new session */
    if (setsid() < 0) {
        return -1;
    }

    /* Fork again to prevent acquiring controlling terminal */
    pid = fork();
    if (pid < 0) {
        return -1;
    }
    if (pid > 0) {
        exit(EXIT_SUCCESS);
    }

    /* Change working directory to root */
    if (chdir("/") < 0) {
        return -1;
    }

    /* Close standard file descriptors */
    close(STDIN_FILENO);
    close(STDOUT_FILENO);
    close(STDERR_FILENO);

    /* Redirect to /dev/null */
    open("/dev/null", O_RDONLY);
    open("/dev/null", O_WRONLY);
    open("/dev/null", O_WRONLY);

    return 0;
}

/**
 * Write PID file
 */
static int write_pid_file(const char *pid_file) {
    FILE *fp = fopen(pid_file, "w");
    if (!fp) {
        return -1;
    }
    fprintf(fp, "%d\n", getpid());
    fclose(fp);
    return 0;
}

/**
 * Remove PID file
 */
static void remove_pid_file(const char *pid_file) {
    unlink(pid_file);
}

/**
 * Set CPU affinity (if configured)
 */
static void set_cpu_affinity() {
    if (g_config.cpu_core < 0) {
        return;
    }

#ifdef __linux__
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(g_config.cpu_core, &cpuset);

    pthread_t thread = pthread_self();
    int ret = pthread_setaffinity_np(thread, sizeof(cpu_set_t), &cpuset);
    if (ret != 0) {
        log_message(LOG_WARN, "Failed to set CPU affinity to core %d: %s",
                    g_config.cpu_core, strerror(ret));
    } else {
        log_message(LOG_INFO, "Set CPU affinity to core %d", g_config.cpu_core);
    }
#else
    log_message(LOG_WARN, "CPU affinity not supported on this platform");
#endif
}

/**
 * Initialize EJFAT Segmenter
 */
static int init_ejfat() {
    try {
        log_message(LOG_INFO, "Initializing EJFAT Segmenter with URI: %s",
                    g_config.ejfat_uri);

        /* Parse EJFAT URI */
        e2sar::EjfatURI uri(g_config.ejfat_uri);

        /* Setup segmenter flags */
        e2sar::Segmenter::SegmenterFlags sflags;
        sflags.dpV6 = g_config.use_ipv6;
        sflags.useCP = g_config.use_control_plane;
        sflags.mtu = g_config.mtu;
        sflags.warmUpMs = g_config.warmup_ms;
        sflags.syncPeriodMs = g_config.sync_period_ms;
        sflags.syncPeriods = g_config.sync_periods;
        sflags.numSendSockets = g_config.num_send_sockets;
        sflags.sndSocketBufSize = g_config.send_socket_buffer_size;
        sflags.rateGbps = g_config.rate_gbps;
        sflags.smooth = g_config.smooth_rate;
        sflags.multiPort = g_config.multi_port;

        /* Create segmenter */
        g_segmenter = new e2sar::Segmenter(uri, g_config.data_id,
                                           g_config.event_src_id, sflags);

        /* Open and start */
        auto res = g_segmenter->openAndStart();
        if (res.has_error()) {
            log_message(LOG_ERROR, "Failed to open and start segmenter: %s",
                        res.error().message().c_str());
            delete g_segmenter;
            g_segmenter = nullptr;
            return -1;
        }

        log_message(LOG_INFO, "EJFAT Segmenter initialized successfully");
        return 0;

    } catch (const std::exception &e) {
        log_message(LOG_ERROR, "Exception initializing EJFAT: %s", e.what());
        return -1;
    }
}

/**
 * Initialize SHM reader
 */
static int init_shm() {
    log_message(LOG_INFO, "Opening SHM FIFO: %s", g_config.fifo_name);

    g_reader = shm_fifo_open(g_config.fifo_name);
    if (!g_reader) {
        log_message(LOG_ERROR, "Failed to open SHM FIFO");
        return -1;
    }

    /* Get initial statistics */
    shm_stats_t stats;
    if (shm_fifo_get_stats(g_reader, &stats) == 0) {
        log_message(LOG_INFO, "SHM FIFO opened: capacity=%lu, entry_size=%lu",
                    stats.capacity, stats.entry_size);
    }

    return 0;
}

/**
 * Main event loop
 */
static void event_loop() {
    uint64_t events_sent = 0;
    uint64_t events_failed = 0;
    uint64_t last_stats_time = 0;

    log_message(LOG_INFO, "Starting event loop...");

    while (g_running) {
        /* Read event from SHM */
        shm_read_result_t result;
        int ret = shm_fifo_read(g_reader, g_config.read_timeout_sec, &result);

        if (ret < 0) {
            log_message(LOG_ERROR, "SHM read error: %s",
                        shm_fifo_get_error(g_reader));
            events_failed++;
            continue;
        }

        if (result.status == SHM_READ_TIMEOUT) {
            /* Timeout - print periodic stats if configured */
            time_t now = time(NULL);
            if (g_config.stats_interval_sec > 0 &&
                (now - last_stats_time) >= g_config.stats_interval_sec) {

                shm_stats_t shm_stats;
                shm_fifo_get_stats(g_reader, &shm_stats);

                auto send_stats = g_segmenter->getSendStats();
                auto sync_stats = g_segmenter->getSyncStats();

                log_message(LOG_INFO,
                    "Stats: Events sent=%lu, failed=%lu, "
                    "SHM(writes=%lu, reads=%lu, drops=%lu, avail=%lu), "
                    "Send(msgs=%lu, bytes=%lu, errs=%lu), "
                    "Sync(msgs=%lu, errs=%lu)",
                    events_sent, events_failed,
                    shm_stats.total_writes, shm_stats.total_reads,
                    shm_stats.total_drops, shm_stats.entries_available,
                    send_stats.msgCnt, send_stats.byteCnt, send_stats.errCnt,
                    sync_stats.msgCnt, sync_stats.errCnt);

                last_stats_time = now;
            }
            continue;
        }

        if (result.status == SHM_READ_EMPTY) {
            /* Empty - shouldn't happen after semaphore wait, but handle it */
            log_message(LOG_DEBUG, "SHM read returned empty");
            continue;
        }

        if (result.status == SHM_READ_SUCCESS) {
            /* Send event via EJFAT */
            log_message(LOG_DEBUG, "Sending event %lu, size %zu",
                        result.event_number, result.data_size);

            auto send_res = g_segmenter->addToSendQueue(
                result.data,
                result.data_size,
                result.event_number,
                g_config.data_id,
                0  /* entropy - let segmenter generate */
            );

            if (send_res.has_error()) {
                log_message(LOG_ERROR, "Failed to send event %lu: %s",
                            result.event_number,
                            send_res.error().message().c_str());
                events_failed++;
            } else {
                events_sent++;
            }
        }
    }

    log_message(LOG_INFO, "Event loop finished. Total events sent: %lu, failed: %lu",
                events_sent, events_failed);
}

/**
 * Cleanup resources
 */
static void cleanup() {
    log_message(LOG_INFO, "Cleaning up...");

    if (g_segmenter) {
        delete g_segmenter;
        g_segmenter = nullptr;
    }

    if (g_reader) {
        shm_fifo_close(g_reader);
        g_reader = nullptr;
    }

    if (!g_config.foreground) {
        remove_pid_file(g_config.pid_file);
        closelog();
    }
}

/**
 * Print usage
 */
static void print_usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s [options]\n"
        "Options:\n"
        "  -c <file>    Configuration file (required)\n"
        "  -f           Run in foreground (don't daemonize)\n"
        "  -h           Show this help message\n"
        "  -v           Print version and exit\n",
        prog);
}

/**
 * Main function
 */
int main(int argc, char *argv[]) {
    const char *config_file = nullptr;
    bool foreground_override = false;
    int opt;

    /* Parse command line arguments */
    while ((opt = getopt(argc, argv, "c:fhv")) != -1) {
        switch (opt) {
            case 'c':
                config_file = optarg;
                break;
            case 'f':
                foreground_override = true;
                break;
            case 'v':
                printf("ejfat_shm_daemon version 1.0.0\n");
                return 0;
            case 'h':
            default:
                print_usage(argv[0]);
                return (opt == 'h') ? 0 : 1;
        }
    }

    /* Require config file */
    if (!config_file) {
        fprintf(stderr, "Error: Configuration file required (-c option)\n");
        print_usage(argv[0]);
        return 1;
    }

    /* Load configuration */
    config_init_defaults(&g_config);
    if (config_load_from_file(&g_config, config_file) < 0) {
        fprintf(stderr, "Error: Failed to load configuration\n");
        return 1;
    }

    /* Override foreground setting if specified on command line */
    if (foreground_override) {
        g_config.foreground = true;
    }

    /* Validate configuration */
    if (config_validate(&g_config) < 0) {
        fprintf(stderr, "Error: Invalid configuration\n");
        return 1;
    }

    /* Print configuration in foreground mode */
    if (g_config.foreground) {
        config_print(&g_config);
    }

    /* Daemonize if not in foreground mode */
    if (!g_config.foreground) {
        if (daemonize() < 0) {
            fprintf(stderr, "Error: Failed to daemonize\n");
            return 1;
        }
        openlog("ejfat_shm_daemon", LOG_PID, LOG_DAEMON);
    }

    /* Write PID file */
    if (write_pid_file(g_config.pid_file) < 0) {
        log_message(LOG_WARN, "Failed to write PID file: %s", g_config.pid_file);
    }

    /* Setup signal handlers */
    setup_signals();

    /* Set CPU affinity if configured */
    set_cpu_affinity();

    /* Initialize SHM reader */
    if (init_shm() < 0) {
        log_message(LOG_ERROR, "Failed to initialize SHM reader");
        cleanup();
        return 1;
    }

    /* Initialize EJFAT segmenter */
    if (init_ejfat() < 0) {
        log_message(LOG_ERROR, "Failed to initialize EJFAT segmenter");
        cleanup();
        return 1;
    }

    log_message(LOG_INFO, "Daemon initialized successfully");

    /* Run main event loop */
    event_loop();

    /* Cleanup and exit */
    cleanup();
    log_message(LOG_INFO, "Daemon exited");

    return 0;
}
