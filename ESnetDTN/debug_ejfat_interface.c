/**
 * Standalone program to debug interface detection using EJFAT_URI
 *
 * Compile: gcc -o debug_ejfat_interface debug_ejfat_interface.c
 * Usage: ./debug_ejfat_interface [--ip <source_ip>]
 * Example: ./debug_ejfat_interface --ip 2001:400:7001:1190::3
 *
 * Reads EJFAT_URI from environment variable
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <ifaddrs.h>
#include <netdb.h>

#ifdef __linux__
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#define NETLINK_CAPABLE 1
#endif

/**
 * Parse EJFAT_URI to extract data IP and port
 * Format: ejfat://token@host:port/lb/id?data=ip:port
 * or: ejfat://token@host:port/lb/id?data=[ipv6]:port
 */
int parse_ejfat_uri(const char *uri, char *data_ip, int *data_port) {
    if (uri == NULL || data_ip == NULL || data_port == NULL) {
        return -1;
    }

    // Find "data=" parameter
    const char *data_start = strstr(uri, "data=");
    if (data_start == NULL) {
        fprintf(stderr, "No 'data=' parameter found in EJFAT_URI\n");
        return -1;
    }

    data_start += 5; // Skip "data="

    // Check if IPv6 (starts with [)
    if (*data_start == '[') {
        // IPv6 format: [ipv6]:port
        data_start++; // Skip [
        const char *bracket_end = strchr(data_start, ']');
        if (bracket_end == NULL) {
            fprintf(stderr, "Malformed IPv6 address in EJFAT_URI\n");
            return -1;
        }

        size_t ip_len = bracket_end - data_start;
        if (ip_len >= INET6_ADDRSTRLEN) {
            fprintf(stderr, "IPv6 address too long\n");
            return -1;
        }

        strncpy(data_ip, data_start, ip_len);
        data_ip[ip_len] = '\0';

        // Get port after ]
        const char *port_start = strchr(bracket_end, ':');
        if (port_start != NULL) {
            *data_port = atoi(port_start + 1);
        } else {
            *data_port = 10000; // default
        }
    } else {
        // IPv4 format: ip:port or just ip
        const char *colon = strchr(data_start, ':');
        const char *ampersand = strchr(data_start, '&');
        const char *end = data_start;

        // Find where the IP ends (at : or & or end of string)
        if (colon != NULL && (ampersand == NULL || colon < ampersand)) {
            // Has port
            size_t ip_len = colon - data_start;
            if (ip_len >= INET6_ADDRSTRLEN) {
                fprintf(stderr, "IP address too long\n");
                return -1;
            }
            strncpy(data_ip, data_start, ip_len);
            data_ip[ip_len] = '\0';

            // Extract port
            const char *port_end = ampersand ? ampersand : (data_start + strlen(data_start));
            char port_str[16];
            size_t port_len = port_end - (colon + 1);
            if (port_len >= sizeof(port_str)) {
                port_len = sizeof(port_str) - 1;
            }
            strncpy(port_str, colon + 1, port_len);
            port_str[port_len] = '\0';
            *data_port = atoi(port_str);
        } else {
            // No port, just IP
            end = ampersand ? ampersand : (data_start + strlen(data_start));
            size_t ip_len = end - data_start;
            if (ip_len >= INET6_ADDRSTRLEN) {
                fprintf(stderr, "IP address too long\n");
                return -1;
            }
            strncpy(data_ip, data_start, ip_len);
            data_ip[ip_len] = '\0';
            *data_port = 10000; // default
        }
    }

    return 0;
}

/**
 * Detect if address is IPv4 or IPv6
 */
int detect_ip_version(const char *ip_str) {
    struct in_addr addr4;
    struct in6_addr addr6;

    if (inet_pton(AF_INET, ip_str, &addr4) == 1)
        return AF_INET;
    if (inet_pton(AF_INET6, ip_str, &addr6) == 1)
        return AF_INET6;

    return -1;
}

#ifdef NETLINK_CAPABLE
/**
 * Get the outgoing interface using Netlink (Linux only) - supports IPv4 and IPv6
 */
int get_interface_via_netlink(const char *dest_ip, int af_family, char *ifname_out, int *mtu_out) {
    struct sockaddr_nl sa = {0};
    struct {
        struct nlmsghdr nlh;
        struct rtmsg rt;
        char buf[1024];
    } req;
    int sock;
    ssize_t len;

    sa.nl_family = AF_NETLINK;

    memset(&req, 0, sizeof(req));
    req.nlh.nlmsg_len = NLMSG_LENGTH(sizeof(struct rtmsg));
    req.nlh.nlmsg_flags = NLM_F_REQUEST;
    req.nlh.nlmsg_type = RTM_GETROUTE;
    req.rt.rtm_family = af_family;

    struct rtattr *rta = (struct rtattr *)(((char *)&req) + NLMSG_ALIGN(req.nlh.nlmsg_len));
    rta->rta_type = RTA_DST;

    if (af_family == AF_INET) {
        rta->rta_len = RTA_LENGTH(sizeof(struct in_addr));
        if (inet_pton(AF_INET, dest_ip, RTA_DATA(rta)) != 1) {
            fprintf(stderr, "Invalid IPv4 address: %s\n", dest_ip);
            return -1;
        }
    } else if (af_family == AF_INET6) {
        rta->rta_len = RTA_LENGTH(sizeof(struct in6_addr));
        if (inet_pton(AF_INET6, dest_ip, RTA_DATA(rta)) != 1) {
            fprintf(stderr, "Invalid IPv6 address: %s\n", dest_ip);
            return -1;
        }
    } else {
        fprintf(stderr, "Unsupported address family\n");
        return -1;
    }

    req.nlh.nlmsg_len = NLMSG_ALIGN(req.nlh.nlmsg_len) + rta->rta_len;

    sock = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    if (sock < 0) {
        perror("socket(AF_NETLINK)");
        return -1;
    }

    if (sendto(sock, &req, req.nlh.nlmsg_len, 0, (struct sockaddr *)&sa, sizeof(sa)) < 0) {
        perror("sendto(netlink)");
        close(sock);
        return -1;
    }

    char buffer[4096];
    len = recv(sock, buffer, sizeof(buffer), 0);
    if (len < 0) {
        perror("recv(netlink)");
        close(sock);
        return -1;
    }

    struct nlmsghdr *nlh = (struct nlmsghdr *)buffer;
    for (; NLMSG_OK(nlh, len); nlh = NLMSG_NEXT(nlh, len)) {
        if (nlh->nlmsg_type == NLMSG_DONE)
            break;

        if (nlh->nlmsg_type == NLMSG_ERROR) {
            fprintf(stderr, "Netlink error\n");
            close(sock);
            return -1;
        }

        struct rtmsg *rtm = (struct rtmsg *)NLMSG_DATA(nlh);
        struct rtattr *rta = RTM_RTA(rtm);
        int rta_len = RTM_PAYLOAD(nlh);

        for (; RTA_OK(rta, rta_len); rta = RTA_NEXT(rta, rta_len)) {
            if (rta->rta_type == RTA_OIF) {
                int ifindex = *(int *)RTA_DATA(rta);
                if_indextoname(ifindex, ifname_out);

                // Get MTU
                int mtu_sock = socket(PF_INET, SOCK_DGRAM, IPPROTO_IP);
                struct ifreq ifr;
                strcpy(ifr.ifr_name, ifname_out);
                if (!ioctl(mtu_sock, SIOCGIFMTU, &ifr)) {
                    *mtu_out = ifr.ifr_mtu;
                } else {
                    *mtu_out = 1500;
                }
                close(mtu_sock);
                close(sock);
                return 0;
            }
        }
    }

    close(sock);
    fprintf(stderr, "Could not determine interface\n");
    return -1;
}
#endif

/**
 * Get interface via connect() method - optionally binding to specific source IP
 */
int get_interface_via_connect(const char *dest_ip, int dest_port, int af_family,
                               const char *source_ip,
                               char *ifname_out, char *local_ip_out) {
    int sock;
    struct sockaddr_storage dest_addr, local_addr, bind_addr;
    socklen_t addr_len;

    sock = socket(af_family, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("socket");
        return -1;
    }

    // If source IP specified, bind to it
    if (source_ip != NULL && strlen(source_ip) > 0) {
        memset(&bind_addr, 0, sizeof(bind_addr));

        if (af_family == AF_INET) {
            struct sockaddr_in *addr4 = (struct sockaddr_in *)&bind_addr;
            addr4->sin_family = AF_INET;
            addr4->sin_port = 0; // Let kernel choose port
            if (inet_pton(AF_INET, source_ip, &addr4->sin_addr) != 1) {
                fprintf(stderr, "Invalid source IPv4 address: %s\n", source_ip);
                close(sock);
                return -1;
            }
            addr_len = sizeof(struct sockaddr_in);
        } else {
            struct sockaddr_in6 *addr6 = (struct sockaddr_in6 *)&bind_addr;
            addr6->sin6_family = AF_INET6;
            addr6->sin6_port = 0; // Let kernel choose port
            if (inet_pton(AF_INET6, source_ip, &addr6->sin6_addr) != 1) {
                fprintf(stderr, "Invalid source IPv6 address: %s\n", source_ip);
                close(sock);
                return -1;
            }
            addr_len = sizeof(struct sockaddr_in6);
        }

        if (bind(sock, (struct sockaddr *)&bind_addr, addr_len) < 0) {
            perror("bind to source IP");
            close(sock);
            return -1;
        }
    }

    memset(&dest_addr, 0, sizeof(dest_addr));

    if (af_family == AF_INET) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *)&dest_addr;
        addr4->sin_family = AF_INET;
        addr4->sin_port = htons(dest_port);
        if (inet_pton(AF_INET, dest_ip, &addr4->sin_addr) != 1) {
            fprintf(stderr, "Invalid IPv4 address: %s\n", dest_ip);
            close(sock);
            return -1;
        }
        addr_len = sizeof(struct sockaddr_in);
    } else if (af_family == AF_INET6) {
        struct sockaddr_in6 *addr6 = (struct sockaddr_in6 *)&dest_addr;
        addr6->sin6_family = AF_INET6;
        addr6->sin6_port = htons(dest_port);
        if (inet_pton(AF_INET6, dest_ip, &addr6->sin6_addr) != 1) {
            fprintf(stderr, "Invalid IPv6 address: %s\n", dest_ip);
            close(sock);
            return -1;
        }
        addr_len = sizeof(struct sockaddr_in6);
    } else {
        fprintf(stderr, "Unsupported address family\n");
        close(sock);
        return -1;
    }

    // Connect to determine which interface would be used
    if (connect(sock, (struct sockaddr *)&dest_addr, addr_len) < 0) {
        perror("connect");
        close(sock);
        return -1;
    }

    // Get the local address assigned by connect
    socklen_t local_len = sizeof(local_addr);
    if (getsockname(sock, (struct sockaddr *)&local_addr, &local_len) < 0) {
        perror("getsockname");
        close(sock);
        return -1;
    }

    if (af_family == AF_INET) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *)&local_addr;
        inet_ntop(AF_INET, &addr4->sin_addr, local_ip_out, INET_ADDRSTRLEN);
    } else {
        struct sockaddr_in6 *addr6 = (struct sockaddr_in6 *)&local_addr;
        inet_ntop(AF_INET6, &addr6->sin6_addr, local_ip_out, INET6_ADDRSTRLEN);
    }

    // Now find which interface has this IP
    struct ifaddrs *ifaddr, *ifa;
    if (getifaddrs(&ifaddr) == -1) {
        perror("getifaddrs");
        close(sock);
        return -1;
    }

    for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
        if (ifa->ifa_addr == NULL)
            continue;

        if (ifa->ifa_addr->sa_family == af_family) {
            char ip_str[INET6_ADDRSTRLEN];

            if (af_family == AF_INET) {
                struct sockaddr_in *addr = (struct sockaddr_in *)ifa->ifa_addr;
                inet_ntop(AF_INET, &addr->sin_addr, ip_str, INET_ADDRSTRLEN);
            } else {
                struct sockaddr_in6 *addr = (struct sockaddr_in6 *)ifa->ifa_addr;
                inet_ntop(AF_INET6, &addr->sin6_addr, ip_str, INET6_ADDRSTRLEN);
            }

            if (strcmp(ip_str, local_ip_out) == 0) {
                strcpy(ifname_out, ifa->ifa_name);
                freeifaddrs(ifaddr);
                close(sock);
                return 0;
            }
        }
    }

    freeifaddrs(ifaddr);
    close(sock);
    strcpy(ifname_out, "unknown");
    return 0;
}

int main(int argc, char *argv[]) {
    const char *ejfat_uri = getenv("EJFAT_URI");
    const char *source_ip = NULL;

    // Parse command line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--ip") == 0 && i + 1 < argc) {
            source_ip = argv[i + 1];
            i++;
        } else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            printf("Usage: %s [--ip <source_ip>]\n", argv[0]);
            printf("Reads EJFAT_URI from environment variable\n");
            printf("Examples:\n");
            printf("  %s\n", argv[0]);
            printf("  %s --ip 2001:400:7001:1190::3\n", argv[0]);
            return 0;
        }
    }

    if (ejfat_uri == NULL) {
        fprintf(stderr, "EJFAT_URI environment variable not set\n");
        fprintf(stderr, "Usage: %s [--ip <source_ip>]\n", argv[0]);
        return 1;
    }

    printf("EJFAT_URI: %s\n", ejfat_uri);
    if (source_ip) {
        printf("Source IP: %s (--ip parameter)\n", source_ip);
    } else {
        printf("Source IP: <any> (no --ip parameter, will use INADDR_ANY/in6addr_any)\n");
    }
    printf("\n");

    // Parse EJFAT_URI
    char dest_ip[INET6_ADDRSTRLEN] = {0};
    int dest_port = 0;

    if (parse_ejfat_uri(ejfat_uri, dest_ip, &dest_port) != 0) {
        fprintf(stderr, "Failed to parse EJFAT_URI\n");
        return 1;
    }

    // Detect IP version
    int af_family = detect_ip_version(dest_ip);
    if (af_family < 0) {
        fprintf(stderr, "Invalid IP address extracted from EJFAT_URI: %s\n", dest_ip);
        return 1;
    }

    const char *ip_version = (af_family == AF_INET) ? "IPv4" : "IPv6";

    printf("Extracted from EJFAT_URI:\n");
    printf("  Destination IP: %s\n", dest_ip);
    printf("  Destination Port: %d\n", dest_port);
    printf("  IP Version: %s\n", ip_version);
    printf("\n========================================================\n\n");

#ifdef NETLINK_CAPABLE
    // Method 1: Netlink (Linux only - what E2SAR uses on Linux)
    printf("--- Method 1: Netlink Query (E2SAR method on Linux) ---\n");
    char ifname_netlink[IFNAMSIZ] = {0};
    int mtu = 0;

    if (get_interface_via_netlink(dest_ip, af_family, ifname_netlink, &mtu) == 0) {
        printf("Interface: %s\n", ifname_netlink);
        printf("MTU: %d\n", mtu);
    } else {
        printf("Failed to get interface via netlink\n");
    }
    printf("\n");
#else
    printf("--- Netlink method not available (not Linux) ---\n");
    printf("E2SAR would fail to auto-detect MTU on this platform.\n\n");
#endif

    // Method 2: Connect method without source IP (E2SAR without --ip)
    printf("--- Method 2: Connect without source IP (E2SAR without --ip) ---\n");
    char ifname_connect_any[IFNAMSIZ] = {0};
    char local_ip_any[INET6_ADDRSTRLEN] = {0};

    if (get_interface_via_connect(dest_ip, dest_port, af_family, NULL,
                                   ifname_connect_any, local_ip_any) == 0) {
        printf("Interface: %s\n", ifname_connect_any);
        printf("Local IP: %s\n", local_ip_any);
    } else {
        printf("Failed to get interface via connect\n");
    }
    printf("\n");

    // Method 3: Connect method WITH source IP (if provided)
    if (source_ip != NULL) {
        printf("--- Method 3: Connect with source IP (E2SAR with --ip) ---\n");
        char ifname_connect_src[IFNAMSIZ] = {0};
        char local_ip_src[INET6_ADDRSTRLEN] = {0};

        if (get_interface_via_connect(dest_ip, dest_port, af_family, source_ip,
                                       ifname_connect_src, local_ip_src) == 0) {
            printf("Interface: %s\n", ifname_connect_src);
            printf("Local IP: %s\n", local_ip_src);
        } else {
            printf("Failed to get interface via connect with source IP\n");
        }
        printf("\n");
    }

    printf("========================================================\n");
    printf("Summary:\n");
    printf("  EJFAT_URI data destination: %s:%d (%s)\n", dest_ip, dest_port, ip_version);
    printf("  Source IP (--ip): %s\n", source_ip ? source_ip : "<not specified>");
#ifdef NETLINK_CAPABLE
    printf("  Netlink says: interface=%s, MTU=%d\n", ifname_netlink, mtu);
#endif
    printf("  Connect (any) says: interface=%s, local_ip=%s\n",
           ifname_connect_any, local_ip_any);

    if (strcmp(ifname_connect_any, "lo") == 0 || strcmp(ifname_connect_any, "lo0") == 0) {
        printf("\n⚠️  WARNING: Loopback interface detected!\n");
        printf("   The destination IP in EJFAT_URI data= is treated as local.\n");
        printf("   This usually means you're sending to the same host.\n");
    }

    return 0;
}
