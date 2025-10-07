/**
 * @file config.c
 * @brief Configuration file parser implementation
 */

#include "config.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>

#define MAX_LINE_LEN 1024

/**
 * Trim whitespace from both ends of a string
 */
static char* trim(char *str) {
    char *end;

    /* Trim leading space */
    while (isspace((unsigned char)*str)) str++;

    if (*str == 0) return str;

    /* Trim trailing space */
    end = str + strlen(str) - 1;
    while (end > str && isspace((unsigned char)*end)) end--;

    end[1] = '\0';
    return str;
}

/**
 * Parse a boolean value
 */
static bool parse_bool(const char *value) {
    return (strcasecmp(value, "true") == 0 ||
            strcasecmp(value, "yes") == 0 ||
            strcasecmp(value, "1") == 0);
}

/**
 * Initialize configuration with default values
 */
void config_init_defaults(daemon_config_t *config) {
    memset(config, 0, sizeof(daemon_config_t));

    /* SHM FIFO defaults */
    strncpy(config->fifo_name, "ejfat_fifo", sizeof(config->fifo_name) - 1);
    config->read_timeout_sec = 5.0;

    /* EJFAT defaults */
    config->data_id = 1;
    config->event_src_id = 0x12345678;

    /* Network defaults (matching E2SAR Segmenter defaults) */
    config->use_ipv6 = false;
    config->use_control_plane = true;
    config->mtu = 1500;
    config->warmup_ms = 1000;
    config->sync_period_ms = 1000;
    config->sync_periods = 2;

    /* Performance defaults */
    config->num_send_sockets = 4;
    config->send_socket_buffer_size = 3 * 1024 * 1024;  /* 3MB */
    config->rate_gbps = -1.0;  /* Unlimited */
    config->smooth_rate = false;
    config->multi_port = false;

    /* CPU affinity */
    config->cpu_core = -1;  /* No affinity */

    /* Daemon defaults */
    config->foreground = false;
    strncpy(config->pid_file, "/var/run/ejfat_shm_daemon.pid",
            sizeof(config->pid_file) - 1);
    strncpy(config->log_file, "/var/log/ejfat_shm_daemon.log",
            sizeof(config->log_file) - 1);
    config->log_level = 2;  /* INFO */

    /* Statistics */
    config->stats_interval_sec = 60;
}

/**
 * Parse a configuration line
 */
static int parse_config_line(daemon_config_t *config, const char *key, const char *value) {
    /* SHM FIFO settings */
    if (strcmp(key, "fifo_name") == 0) {
        strncpy(config->fifo_name, value, sizeof(config->fifo_name) - 1);
    } else if (strcmp(key, "read_timeout") == 0) {
        config->read_timeout_sec = atof(value);
    }
    /* EJFAT settings */
    else if (strcmp(key, "ejfat_uri") == 0) {
        strncpy(config->ejfat_uri, value, sizeof(config->ejfat_uri) - 1);
    } else if (strcmp(key, "data_id") == 0) {
        config->data_id = (uint16_t)strtoul(value, NULL, 0);
    } else if (strcmp(key, "event_src_id") == 0) {
        config->event_src_id = (uint32_t)strtoul(value, NULL, 0);
    }
    /* Network settings */
    else if (strcmp(key, "use_ipv6") == 0) {
        config->use_ipv6 = parse_bool(value);
    } else if (strcmp(key, "use_control_plane") == 0) {
        config->use_control_plane = parse_bool(value);
    } else if (strcmp(key, "mtu") == 0) {
        config->mtu = (uint16_t)atoi(value);
    } else if (strcmp(key, "warmup_ms") == 0) {
        config->warmup_ms = (uint16_t)atoi(value);
    } else if (strcmp(key, "sync_period_ms") == 0) {
        config->sync_period_ms = (uint16_t)atoi(value);
    } else if (strcmp(key, "sync_periods") == 0) {
        config->sync_periods = (uint16_t)atoi(value);
    }
    /* Performance settings */
    else if (strcmp(key, "num_send_sockets") == 0) {
        config->num_send_sockets = (size_t)atoi(value);
    } else if (strcmp(key, "send_socket_buffer_size") == 0) {
        config->send_socket_buffer_size = atoi(value);
    } else if (strcmp(key, "rate_gbps") == 0) {
        config->rate_gbps = atof(value);
    } else if (strcmp(key, "smooth_rate") == 0) {
        config->smooth_rate = parse_bool(value);
    } else if (strcmp(key, "multi_port") == 0) {
        config->multi_port = parse_bool(value);
    }
    /* CPU affinity */
    else if (strcmp(key, "cpu_core") == 0) {
        config->cpu_core = atoi(value);
    }
    /* Daemon settings */
    else if (strcmp(key, "foreground") == 0) {
        config->foreground = parse_bool(value);
    } else if (strcmp(key, "pid_file") == 0) {
        strncpy(config->pid_file, value, sizeof(config->pid_file) - 1);
    } else if (strcmp(key, "log_file") == 0) {
        strncpy(config->log_file, value, sizeof(config->log_file) - 1);
    } else if (strcmp(key, "log_level") == 0) {
        config->log_level = atoi(value);
    }
    /* Statistics */
    else if (strcmp(key, "stats_interval") == 0) {
        config->stats_interval_sec = (uint32_t)atoi(value);
    }
    else {
        fprintf(stderr, "Warning: Unknown configuration key '%s'\n", key);
    }

    return 0;
}

/**
 * Load configuration from file
 */
int config_load_from_file(daemon_config_t *config, const char *config_file) {
    FILE *fp;
    char line[MAX_LINE_LEN];
    int line_num = 0;

    if (!config || !config_file) {
        return -1;
    }

    fp = fopen(config_file, "r");
    if (!fp) {
        fprintf(stderr, "Failed to open config file '%s': %s\n",
                config_file, strerror(errno));
        return -1;
    }

    while (fgets(line, sizeof(line), fp)) {
        line_num++;

        char *trimmed = trim(line);

        /* Skip empty lines and comments */
        if (trimmed[0] == '\0' || trimmed[0] == '#' || trimmed[0] == ';') {
            continue;
        }

        /* Skip section headers [section] */
        if (trimmed[0] == '[') {
            continue;
        }

        /* Parse key=value */
        char *eq = strchr(trimmed, '=');
        if (!eq) {
            fprintf(stderr, "Warning: Invalid line %d in config file: %s\n",
                    line_num, trimmed);
            continue;
        }

        *eq = '\0';
        char *key = trim(trimmed);
        char *value = trim(eq + 1);

        parse_config_line(config, key, value);
    }

    fclose(fp);
    return 0;
}

/**
 * Validate configuration
 */
int config_validate(const daemon_config_t *config) {
    if (!config) {
        return -1;
    }

    /* Check required fields */
    if (strlen(config->fifo_name) == 0) {
        fprintf(stderr, "Error: fifo_name is required\n");
        return -1;
    }

    if (strlen(config->ejfat_uri) == 0) {
        fprintf(stderr, "Error: ejfat_uri is required\n");
        return -1;
    }

    /* Validate ranges */
    if (config->mtu < 64 || config->mtu > 9000) {
        fprintf(stderr, "Error: MTU must be between 64 and 9000\n");
        return -1;
    }

    if (config->num_send_sockets == 0 || config->num_send_sockets > 128) {
        fprintf(stderr, "Error: num_send_sockets must be between 1 and 128\n");
        return -1;
    }

    if (config->log_level < 0 || config->log_level > 3) {
        fprintf(stderr, "Error: log_level must be between 0 and 3\n");
        return -1;
    }

    return 0;
}

/**
 * Print configuration (for debugging)
 */
void config_print(const daemon_config_t *config) {
    if (!config) {
        return;
    }

    printf("=== EJFAT SHM Daemon Configuration ===\n");
    printf("[SHM FIFO]\n");
    printf("  fifo_name: %s\n", config->fifo_name);
    printf("  read_timeout: %.2f sec\n", config->read_timeout_sec);

    printf("\n[EJFAT]\n");
    printf("  ejfat_uri: %s\n", config->ejfat_uri);
    printf("  data_id: 0x%04x\n", config->data_id);
    printf("  event_src_id: 0x%08x\n", config->event_src_id);

    printf("\n[Network]\n");
    printf("  use_ipv6: %s\n", config->use_ipv6 ? "true" : "false");
    printf("  use_control_plane: %s\n", config->use_control_plane ? "true" : "false");
    printf("  mtu: %u\n", config->mtu);
    printf("  warmup_ms: %u\n", config->warmup_ms);
    printf("  sync_period_ms: %u\n", config->sync_period_ms);
    printf("  sync_periods: %u\n", config->sync_periods);

    printf("\n[Performance]\n");
    printf("  num_send_sockets: %zu\n", config->num_send_sockets);
    printf("  send_socket_buffer_size: %d\n", config->send_socket_buffer_size);
    printf("  rate_gbps: %.2f\n", config->rate_gbps);
    printf("  smooth_rate: %s\n", config->smooth_rate ? "true" : "false");
    printf("  multi_port: %s\n", config->multi_port ? "true" : "false");

    printf("\n[System]\n");
    printf("  cpu_core: %d\n", config->cpu_core);
    printf("  foreground: %s\n", config->foreground ? "true" : "false");
    printf("  pid_file: %s\n", config->pid_file);
    printf("  log_file: %s\n", config->log_file);
    printf("  log_level: %d\n", config->log_level);

    printf("\n[Statistics]\n");
    printf("  stats_interval: %u sec\n", config->stats_interval_sec);
    printf("=====================================\n");
}
