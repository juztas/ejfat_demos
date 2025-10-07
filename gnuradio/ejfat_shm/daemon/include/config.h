/**
 * @file config.h
 * @brief Configuration file parser for EJFAT SHM daemon
 */

#ifndef CONFIG_H
#define CONFIG_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define MAX_PATH_LEN 512
#define MAX_URI_LEN 512

/**
 * Daemon configuration structure
 */
typedef struct {
    /* SHM FIFO settings */
    char fifo_name[256];
    double read_timeout_sec;

    /* EJFAT settings */
    char ejfat_uri[MAX_URI_LEN];
    uint16_t data_id;
    uint32_t event_src_id;

    /* Network settings */
    bool use_ipv6;
    bool use_control_plane;
    uint16_t mtu;
    uint16_t warmup_ms;
    uint16_t sync_period_ms;
    uint16_t sync_periods;

    /* Performance settings */
    size_t num_send_sockets;
    int send_socket_buffer_size;
    float rate_gbps;
    bool smooth_rate;
    bool multi_port;

    /* CPU affinity (optional, -1 = no affinity) */
    int cpu_core;

    /* Daemon settings */
    bool foreground;
    char pid_file[MAX_PATH_LEN];
    char log_file[MAX_PATH_LEN];
    int log_level;  /* 0=error, 1=warn, 2=info, 3=debug */

    /* Statistics reporting */
    uint32_t stats_interval_sec;
} daemon_config_t;

/**
 * Initialize configuration with default values
 *
 * @param config Configuration structure to initialize
 */
void config_init_defaults(daemon_config_t *config);

/**
 * Load configuration from file
 *
 * @param config Configuration structure to populate
 * @param config_file Path to configuration file
 * @return 0 on success, -1 on error
 */
int config_load_from_file(daemon_config_t *config, const char *config_file);

/**
 * Validate configuration
 *
 * @param config Configuration structure to validate
 * @return 0 if valid, -1 if invalid
 */
int config_validate(const daemon_config_t *config);

/**
 * Print configuration (for debugging)
 *
 * @param config Configuration structure to print
 */
void config_print(const daemon_config_t *config);

#ifdef __cplusplus
}
#endif

#endif /* CONFIG_H */
