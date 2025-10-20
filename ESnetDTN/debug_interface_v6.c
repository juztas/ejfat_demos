/**
 * Standalone program to debug interface detection for IPv4 and IPv6 destinations
 *
 * Compile: gcc -o debug_interface_v6 debug_interface_v6.c
 * Usage: ./debug_interface_v6 <destination_ip> [port]
 * Example: ./debug_interface_v6 2001:400:7001:1190::3 10000
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
 * Get interface via connect() method (works on macOS and Linux, supports IPv4 and IPv6)
 */
int get_interface_via_connect(const char *dest_ip, int dest_port, int af_family,
                               char *ifname_out, char *local_ip_out) {
    int sock;
    struct sockaddr_storage dest_addr, local_addr;
    socklen_t addr_len;

    sock = socket(af_family, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("socket");
        return -1;
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

/**
 * Test binding to any address
 */
void test_bind_any(const char *dest_ip, int dest_port, int af_family) {
    int sock;
    struct sockaddr_storage local_addr, dest_addr, bound_addr;
    socklen_t addr_len;

    printf("\n--- Testing bind to ANY address ---\n");

    sock = socket(af_family, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("socket");
        return;
    }

    memset(&local_addr, 0, sizeof(local_addr));

    if (af_family == AF_INET) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *)&local_addr;
        addr4->sin_family = AF_INET;
        addr4->sin_addr.s_addr = INADDR_ANY;
        addr4->sin_port = 0;
        addr_len = sizeof(struct sockaddr_in);
    } else {
        struct sockaddr_in6 *addr6 = (struct sockaddr_in6 *)&local_addr;
        addr6->sin6_family = AF_INET6;
        addr6->sin6_addr = in6addr_any;
        addr6->sin6_port = 0;
        addr_len = sizeof(struct sockaddr_in6);
    }

    if (bind(sock, (struct sockaddr *)&local_addr, addr_len) < 0) {
        perror("bind");
        close(sock);
        return;
    }

    // Connect to destination
    memset(&dest_addr, 0, sizeof(dest_addr));

    if (af_family == AF_INET) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *)&dest_addr;
        addr4->sin_family = AF_INET;
        addr4->sin_port = htons(dest_port);
        inet_pton(AF_INET, dest_ip, &addr4->sin_addr);
    } else {
        struct sockaddr_in6 *addr6 = (struct sockaddr_in6 *)&dest_addr;
        addr6->sin6_family = AF_INET6;
        addr6->sin6_port = htons(dest_port);
        inet_pton(AF_INET6, dest_ip, &addr6->sin6_addr);
    }

    if (connect(sock, (struct sockaddr *)&dest_addr, addr_len) < 0) {
        perror("connect");
        close(sock);
        return;
    }

    // Check what local address was assigned
    socklen_t bound_len = sizeof(bound_addr);
    if (getsockname(sock, (struct sockaddr *)&bound_addr, &bound_len) < 0) {
        perror("getsockname");
        close(sock);
        return;
    }

    char local_ip[INET6_ADDRSTRLEN];
    int port;

    if (af_family == AF_INET) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *)&bound_addr;
        inet_ntop(AF_INET, &addr4->sin_addr, local_ip, INET_ADDRSTRLEN);
        port = ntohs(addr4->sin_port);
    } else {
        struct sockaddr_in6 *addr6 = (struct sockaddr_in6 *)&bound_addr;
        inet_ntop(AF_INET6, &addr6->sin6_addr, local_ip, INET6_ADDRSTRLEN);
        port = ntohs(addr6->sin6_port);
    }

    printf("Bound to: %s:%d\n", local_ip, port);

    close(sock);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <destination_ip> [destination_port]\n", argv[0]);
        fprintf(stderr, "Example: %s 192.168.1.100 10000\n", argv[0]);
        fprintf(stderr, "Example: %s 2001:400:7001:1190::3 10000\n", argv[0]);
        return 1;
    }

    const char *dest_ip = argv[1];
    int dest_port = (argc > 2) ? atoi(argv[2]) : 10000;

    // Detect IP version
    int af_family = detect_ip_version(dest_ip);
    if (af_family < 0) {
        fprintf(stderr, "Invalid IP address: %s\n", dest_ip);
        return 1;
    }

    const char *ip_version = (af_family == AF_INET) ? "IPv4" : "IPv6";

    printf("Debugging interface selection for destination: %s:%d (%s)\n",
           dest_ip, dest_port, ip_version);
    printf("========================================================\n\n");

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

    // Method 2: Connect method (works on all platforms)
    printf("--- Method 2: Connect/getsockname Method ---\n");
    char ifname_connect[IFNAMSIZ] = {0};
    char local_ip[INET6_ADDRSTRLEN] = {0};

    if (get_interface_via_connect(dest_ip, dest_port, af_family, ifname_connect, local_ip) == 0) {
        printf("Interface: %s\n", ifname_connect);
        printf("Local IP: %s\n", local_ip);
    } else {
        printf("Failed to get interface via connect\n");
    }

    // Method 3: Test ANY address behavior
    test_bind_any(dest_ip, dest_port, af_family);

    printf("\n========================================================\n");
    printf("Summary:\n");
    printf("  Destination: %s:%d (%s)\n", dest_ip, dest_port, ip_version);
#ifdef NETLINK_CAPABLE
    printf("  Netlink says: interface=%s, MTU=%d\n", ifname_netlink, mtu);
#endif
    printf("  Connect says: interface=%s, local_ip=%s\n", ifname_connect, local_ip);

    if (strcmp(ifname_connect, "lo") == 0 || strcmp(ifname_connect, "lo0") == 0) {
        printf("\n⚠️  WARNING: Loopback interface detected!\n");
        printf("   This means the destination IP is treated as local.\n");
        printf("   Check your EJFAT_URI data= parameter.\n");
    }

    return 0;
}
