# ESnet DTN Node Survey

## Summary Table (Ordered by IPv6 Descending)

| Hostname | IPv6 Address | CPU Family | Cores | NUMA Config |
|----------|--------------|------------|-------|-------------|
| wash | 2001:400:7001:1190::3 | Intel Xeon Gold 6246 @ 3.30GHz | 48 | 2 nodes: N0(0-23), N1(24-47) |
| hous | 2001:400:4a01:1190::3 | AMD EPYC 73F3 16-Core | 32 | 2 nodes: N0(0-15), N1(16-31) |
| denv | 2001:400:d01:1190::3 | AMD EPYC 73F3 16-Core | 32 | 8 nodes: N0(0-3), N1(4-7), N2(8-11), N3(12-15), N4(16-19), N5(20-23), N6(24-27), N7(28-31) |
| star | 2001:400:2001:119c::3 | Intel Xeon Gold 6246 @ 3.30GHz | 48 | 2 nodes: N0(0-23), N1(24-47) |
| sunn | 2001:400:201:1190::3 | AMD EPYC 73F3 16-Core | 32 | 2 nodes: N0(0-15), N1(16-31) |
| cern773 | 2001:400:be01:1190::3 | AMD EPYC 73F3 16-Core | 32 | 2 nodes: N0(0-15), N1(16-31) |

## Detailed NUMA Topology

### wash (Intel Xeon Gold 6246)
- **Total Cores:** 48 (24 physical, hyperthreading enabled)
- **NUMA Nodes:** 2
  - Node 0: CPUs 0-23
  - Node 1: CPUs 24-47

### hous (AMD EPYC 73F3)
- **Total Cores:** 32 (16 physical, hyperthreading enabled)
- **NUMA Nodes:** 2
  - Node 0: CPUs 0-15
  - Node 1: CPUs 16-31

### denv (AMD EPYC 73F3 with NPS4)
- **Total Cores:** 32 (16 physical, hyperthreading enabled)
- **NUMA Nodes:** 8 (NPS4 mode - NUMA Per Socket = 4)
  - Node 0: CPUs 0-3
  - Node 1: CPUs 4-7
  - Node 2: CPUs 8-11
  - Node 3: CPUs 12-15
  - Node 4: CPUs 16-19
  - Node 5: CPUs 20-23
  - Node 6: CPUs 24-27
  - Node 7: CPUs 28-31

### star (Intel Xeon Gold 6246)
- **Total Cores:** 48 (24 physical, hyperthreading enabled)
- **NUMA Nodes:** 2
  - Node 0: CPUs 0-23
  - Node 1: CPUs 24-47

### sunn (AMD EPYC 73F3)
- **Total Cores:** 32 (16 physical, hyperthreading enabled)
- **NUMA Nodes:** 2
  - Node 0: CPUs 0-15
  - Node 1: CPUs 16-31

### cern773 (AMD EPYC 73F3)
- **Total Cores:** 32 (16 physical, hyperthreading enabled)
- **NUMA Nodes:** 2
  - Node 0: CPUs 0-15
  - Node 1: CPUs 16-31

## Mellanox NIC NUMA Affinity

| Hostname | PCI Device | NIC NUMA Node | Local CPUs | Recommended Cores |
|----------|------------|---------------|------------|-------------------|
| wash | 0000:5e:00.0 | Node 0 | 0-23 | 0-23 |
| hous | 0000:81:00.0 | Node 1 | 16-31 | 16-31 |
| denv | 0000:81:00.0 | Node 7 | 28-31 | 28-31 |
| star | 0000:5e:00.0 | Node 0 | 0-23 | 0-23 |
| sunn | 0000:81:00.0 | Node 1 | 16-31 | 16-31 |
| cern773 | 0000:81:00.0 | Node 1 | 16-31 | 16-31 |

## Key Findings

### CPU Distribution
- **Intel Xeon Gold 6246:** 2 nodes (star, wash) - 96 total cores
- **AMD EPYC 73F3:** 4 nodes (cern773, denv, hous, sunn) - 128 total cores
- **Total:** 224 cores across all 6 nodes

### NUMA Patterns
- **Standard 2-NUMA:** 5 nodes
  - Intel: NIC on NUMA 0 (CPUs 0-23)
  - AMD: NIC on NUMA 1 (CPUs 16-31)
- **NPS4 8-NUMA:** 1 node (denv)
  - NIC on NUMA 7 (CPUs 28-31) - **ONLY 4 cores!**

### Performance Implications
1. **NUMA Locality is Critical**
   - Cross-NUMA penalty: 20-40% performance loss
   - Additional latency: ~150ns per access

2. **denv Configuration Issue**
   - Only 4 cores co-located with NIC
   - Will have 1/4 the performance of other AMD nodes
   - Consider excluding from high-performance tests

3. **Optimal Core Pinning**
   - Intel nodes (wash, star): Use cores 0-23
   - AMD standard (cern773, hous, sunn): Use cores 16-31
   - AMD NPS4 (denv): Use cores 28-31 ONLY

## Network Configuration
- All nodes use Mellanox ConnectX interface **dtn1.916**
- All nodes are 100G capable
- IPv6 addresses are on 2001:400::/32 network
