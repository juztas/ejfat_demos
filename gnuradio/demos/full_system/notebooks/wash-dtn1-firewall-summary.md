# wash-dtn1-mgt.es.net Firewall Configuration Summary

**Date:** 2025-10-18  
**System:** Ubuntu 22.04.5 LTS (Jammy Jellyfish)  
**Firewall:** nftables (table: inet default_rules)  
**Full ruleset:** 7,539 lines

## Overview

The system uses **nftables** for host-based firewalling with a comprehensive ruleset that includes:
- Large IP whitelists for authorized sources
- Default-deny INPUT policy with explicit allow rules
- Default-allow OUTPUT policy with some restrictions on DTN interfaces
- Support for both IPv4 and IPv6

## Key Policies

### INPUT Chain (prerouting)
- **Default Policy:** DROP (deny by default)
- **Type:** filter hook input priority filter

### OUTPUT Chain (output)
- **Default Policy:** ACCEPT (allow by default)
- **Type:** filter hook output priority filter

## Predefined IP Sets

The firewall uses several large IP sets (whitelists):

| Set Name | Type | Purpose | Approximate Size |
|----------|------|---------|------------------|
| `dtnExternal_v4` | IPv4 | Authorized external DTN clients | ~7,200+ networks |
| `dtnExternal_v6` | IPv6 | Authorized external DTN clients (IPv6) | Large |
| `gateways_v4` | IPv4 | ESnet gateway routers | 10 addresses |
| `gateways_v6` | IPv6 | ESnet gateway routers (IPv6) | 10 addresses |
| `ansible_v4` | IPv4 | Ansible management hosts | 10 addresses |
| `ansible_v6` | IPv6 | Ansible management hosts (IPv6) | 10 addresses |
| `moka_v4` | IPv4 | MOKA monitoring systems | 2 networks |
| `moka_v6` | IPv6 | MOKA monitoring systems (IPv6) | 2 networks |

## INPUT Rules (Detailed)

### 1. Connection Tracking
```
ct state invalid → DROP (with counter cnt_invalid)
ct state {established, related} → ACCEPT (with counter cnt_accepted)
```

### 2. ICMP (both IPv4 and IPv6)
Allowed ICMP types:
- echo-reply, destination-unreachable, echo-request, time-exceeded
- ICMPv6: + packet-too-big, nd-router-advert, nd-neighbor-solicit, nd-neighbor-advert

### 3. Loopback
```
iifname "lo" → ACCEPT
```

### 4. DTN Interfaces (dtn1.912, dtn1.916)
Traffic on these interfaces jumps to **jump_dtn1** chain (see below)

### 5. Management Access (Specific IPs)

**SSH and full access from specific hosts:**
- 198.128.14.247 / 2001:400:14:f::1f
- 198.128.155.64 / 2001:400:210:155::40
- 198.124.250.199 / 2001:400:6441::107
- 198.129.250.209 / 2001:400:211::10a
- 198.128.128.99 / 2001:400:211:11::3
- 198.128.128.100 / 2001:400:211:11::4

**Special gRPC access:**
- 2001:400:c003:5::/64 → TCP port 50051
- 2001:400:c203:5::/64 → TCP port 50051

**Restricted host (blocks privileged ports, then allows):**
- 198.128.155.8 / 2001:400:210:155::8
  - BLOCKS: TCP/UDP ports 1-1024
  - ALLOWS: All other ports

### 6. SSH Access (Port 22)
Allowed from:
- @gateways_v4 / @gateways_v6
- @ansible_v4 / @ansible_v6
- 198.129.250.226 / 2001:400:211:82::6
- @moka_v4 / @moka_v6

### 7. SNMP Monitoring (Port 161/UDP)
Allowed from:
- @moka_v4 / @moka_v6

### 8. Application Ports (Specific IPs)
- 198.128.159.138 / 2001:400:210:159::8a → TCP ports 9001, 5050

### 9. Default
```
Everything else → DROP
```

## DTN Interface Rules (jump_dtn1)

For traffic arriving on **dtn1.912** or **dtn1.916**, allow from **@dtnExternal_v4/@dtnExternal_v6**:

### Data Transfer Ports
- TCP/UDP 50000-51000 (GridFTP data channels)
- TCP 2811, 2812 (GridFTP control)
- TCP 61617 (ActiveMQ)

### Performance Testing & Tools
- TCP/UDP 5001-5900 (iperf, iperf3, etc.)
- TCP 861 (?)
- TCP 8760-9960 (various monitoring/testing tools)

### Web & Management
- TCP 80, 443 (HTTP/HTTPS)
- TCP 8000, 8001-8020 (web services)
- TCP 8090, 8096 (perfSONAR/monitoring)

### Control & Signaling
- TCP 3001-3003 (?)
- TCP 7123 (?)

### Network Services
- TCP 53 (DNS)
- TCP 123 (NTP)
- TCP 33434-33634 (traceroute)

**Default for DTN interfaces:** DROP

## OUTPUT Rules (Detailed)

### 1. Connection Tracking
```
ct state invalid → DROP
ct state {established, related} → ACCEPT
```

### 2. ICMP
Same types as INPUT

### 3. DTN Interface Outbound (jump_dtn1-out)
For traffic leaving on **dtn1.912** or **dtn1.916**:
- If source IP in @dtnExternal_v4/@dtnExternal_v6 → ACCEPT
- TCP port 443 (HTTPS) → ACCEPT
- Everything else → DROP

### 4. Default
```
ACCEPT
```

## Statistics Counters

The firewall tracks:
- `cnt_accepted`: Established/related connections (77,008 packets / 24.6 MB)
- `cnt_icmp`: ICMP traffic (599 packets / 38 KB)
- `cnt_invalid`: Invalid packets (42 packets / 1.9 KB)
- `cnt_ipv4`: IPv4 packets (1,288 packets / 112 KB)
- `cnt_ipv6`: IPv6 packets (41,499 packets / 17.2 MB)

## Security Posture

### Strengths
✅ Default-deny INPUT policy  
✅ Explicit whitelisting of authorized sources  
✅ Both IPv4 and IPv6 coverage  
✅ Connection state tracking  
✅ Separate rules for different network interfaces  
✅ Large authorized DTN client list (good for data transfer operations)

### Potential Concerns
⚠️ Very large whitelist (~7,200+ networks in dtnExternal sets) - broad access  
⚠️ Wide port ranges on DTN interfaces (50000-51000, 5001-5900, 8760-9960)  
⚠️ Some undefined application ports (861, 3001-3003, 7123)

### Recommendations
1. **Document all allowed ports** - clarify the purpose of ports 861, 3001-3003, 7123
2. **Audit dtnExternal sets** - review if all ~7,200 networks still need access
3. **Consider port-specific logging** - add counters for sensitive services
4. **Review privileged port block** - the 198.128.155.8 rule seems unusual

## File Locations

- Full ruleset saved to: `/tmp/wash-dtn1-firewall-rules.txt` (7,539 lines)
- This summary: `/tmp/wash-dtn1-firewall-summary.md`

## Useful Commands

```bash
# View current rules
sudo nft list ruleset

# View specific table
sudo nft list table inet default_rules

# View specific chain
sudo nft list chain inet default_rules prerouting

# View counters
sudo nft list counters

# View specific IP set
sudo nft list set inet default_rules dtnExternal_v4
```
