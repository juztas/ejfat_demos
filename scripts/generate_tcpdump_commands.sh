#!/bin/bash
#
# generate_tcpdump_commands.sh - Generate tcpdump commands for manual execution
#
# This script generates the tcpdump commands needed for packet capture on each
# receiver node, including proper filters and durations.
#
# Usage: generate_tcpdump_commands.sh <receiver_config.yaml> <INSTANCE_URI_file> <remote_work_dir> <log_dir> <node1> <node2> ...
#

set -e

#------------------------------------------------------------------------------------------------
# ARGUMENT PARSING
#------------------------------------------------------------------------------------------------

if [ $# -lt 5 ]; then
    echo "Usage: $0 <receiver_config.yaml> <INSTANCE_URI_file> <remote_work_dir> <log_dir> <node1> [node2] [node3] ..."
    echo ""
    echo "Arguments:"
    echo "  receiver_config.yaml   Path to receiver configuration file"
    echo "  INSTANCE_URI_file      Path to INSTANCE_URI file"
    echo "  remote_work_dir        Remote working directory (e.g., ~/ejfat_demos/ESnetDTN/runs/test2)"
    echo "  log_dir                Log directory name (e.g., run_output)"
    echo "  node1 [node2...]       List of receiver nodes"
    echo ""
    echo "Example:"
    echo "  $0 receiver_config.yaml INSTANCE_URI ~/ejfat_demos/ESnetDTN/runs/test2 run_output wash-dtn1-mgt.es.net sunn-dtn1-mgt.es.net"
    exit 1
fi

RECEIVER_CONFIG="$1"
INSTANCE_URI_FILE="$2"
REMOTE_WORK_DIR="$3"
LOG_DIR="$4"
shift 4
RECEIVER_NODES=("$@")

#------------------------------------------------------------------------------------------------
# CONFIGURATION
#------------------------------------------------------------------------------------------------

# Parse YAML value
parse_yaml() {
    local file="$1"
    local key="$2"
    grep "^${key}:" "$file" 2>/dev/null | sed "s/^${key}://" | tr -d ' ' | tr -d '"' | tr -d "'"
}

# Extract hostname from EJFAT URI
extract_lb_hostname() {
    local uri="$1"
    echo "$uri" | sed -E 's|^ejfats?://[^@]+@([^:]+):.*|\1|'
}

#------------------------------------------------------------------------------------------------
# LOAD CONFIGURATION
#------------------------------------------------------------------------------------------------

if [ ! -f "$RECEIVER_CONFIG" ]; then
    echo "Error: $RECEIVER_CONFIG not found"
    exit 1
fi

if [ ! -f "$INSTANCE_URI_FILE" ]; then
    echo "Error: $INSTANCE_URI_FILE not found"
    exit 1
fi

# Load EJFAT_URI
source "$INSTANCE_URI_FILE"

if [ -z "$EJFAT_URI" ]; then
    echo "Error: EJFAT_URI not set in $INSTANCE_URI_FILE"
    exit 1
fi

# Parse receiver configuration
RX_DURATION=$(parse_yaml "$RECEIVER_CONFIG" "rx_duration")
RX_DURATION="${RX_DURATION:-120}"

IP_VERSION=$(parse_yaml "$RECEIVER_CONFIG" "ip_version")
IP_VERSION="${IP_VERSION:-6}"

#------------------------------------------------------------------------------------------------
# RESOLVE LOAD BALANCER ADDRESSES
#------------------------------------------------------------------------------------------------

LB_HOSTNAME=$(extract_lb_hostname "$EJFAT_URI")
if [ -z "$LB_HOSTNAME" ]; then
    echo "Error: Failed to extract load balancer hostname from URI"
    exit 1
fi

# Resolve load balancer to both IPv4 and IPv6 addresses
LB_IPV4=$(dig +short "$LB_HOSTNAME" A | tail -1)
LB_IPV6=$(dig +short "$LB_HOSTNAME" AAAA | tail -1)

# Build tcpdump filter for source address
TCPDUMP_FILTER=""
if [ -n "$LB_IPV4" ] && [ -n "$LB_IPV6" ]; then
    TCPDUMP_FILTER="src host $LB_IPV4 or src host $LB_IPV6"
elif [ -n "$LB_IPV4" ]; then
    TCPDUMP_FILTER="src host $LB_IPV4"
elif [ -n "$LB_IPV6" ]; then
    TCPDUMP_FILTER="src host $LB_IPV6"
else
    echo "Error: Failed to resolve load balancer to any IP address"
    exit 1
fi

# Calculate tcpdump duration (rx_duration + 30 seconds)
TCPDUMP_DURATION=$((RX_DURATION + 30))

#------------------------------------------------------------------------------------------------
# GENERATE COMMANDS FOR EACH NODE
#------------------------------------------------------------------------------------------------

echo "========================================================================"
echo "tcpdump Commands for Manual Execution"
echo "========================================================================"
echo ""
echo "Configuration:"
echo "  Load Balancer:     $LB_HOSTNAME"
echo "  LB IPv4:           ${LB_IPV4:-none}"
echo "  LB IPv6:           ${LB_IPV6:-none}"
echo "  Filter:            $TCPDUMP_FILTER"
echo "  RX Duration:       $RX_DURATION seconds"
echo "  tcpdump Duration:  $TCPDUMP_DURATION seconds"
echo "  IP Version:        IPv$IP_VERSION"
echo "  Receiver Nodes:    ${RECEIVER_NODES[*]}"
echo ""
echo "========================================================================"
echo ""

# Generate commands for each receiver node
index=0
for node in "${RECEIVER_NODES[@]}"; do

    echo "------------------------------------------------------------------------"
    echo "Receiver $index: $node"
    echo "------------------------------------------------------------------------"
    echo ""
    echo "1. SSH into the node:"
    echo "   ssh $node"
    echo ""
    echo "2. Change to the working directory:"
    echo "   cd $REMOTE_WORK_DIR/$LOG_DIR"
    echo ""
    echo "3. Detect the network interface (if needed):"
    if [ "$IP_VERSION" = "4" ]; then
        echo "   IFACE=\$(ip route get $LB_IPV4 | head -1 | sed 's/^.*dev//' | awk '{ print \$1 }')"
    else
        echo "   IFACE=\$(ip route get $LB_IPV6 | head -1 | sed 's/^.*dev//' | awk '{ print \$1 }')"
    fi
    echo "   echo \"Interface: \$IFACE\""
    echo ""
    echo "4. Start tcpdump (runs in foreground with verbose output):"
    echo "   sudo timeout $TCPDUMP_DURATION tcpdump -i \$IFACE -w rx_${index}.pcap '$TCPDUMP_FILTER' -s 0 -v"
    echo ""
    echo "   Or with hardcoded interface (usually dtn1.916):"
    echo "   sudo timeout $TCPDUMP_DURATION tcpdump -i dtn1.916 -w rx_${index}.pcap '$TCPDUMP_FILTER' -s 0 -v"
    echo ""
    echo "   This will save to rx_${index}.pcap AND show packet summaries on screen"
    echo ""
    echo "   Alternative - show detailed packets without saving:"
    echo "   sudo timeout $TCPDUMP_DURATION tcpdump -i dtn1.916 '$TCPDUMP_FILTER' -s 0 -vvv"
    echo ""

    index=$((index + 1))
done

echo "========================================================================"
echo "Notes:"
echo "========================================================================"
echo "- Start tcpdump BEFORE starting the receiver"
echo "- tcpdump will run for $TCPDUMP_DURATION seconds and stop automatically"
echo "- The receiver runs for $RX_DURATION seconds"
echo "- This gives 30 seconds of extra capture time after the receiver stops"
echo "- PCAP files will be saved as: rx_0.pcap, rx_1.pcap, rx_2.pcap"
echo "- Commands run in FOREGROUND - you'll see packet summaries in real-time"
echo "- Open separate terminal windows for each node"
echo "- Make sure you have sudo privileges on each node"
echo "========================================================================"
echo ""
echo "Quick command for each node (copy/paste ready):"
echo "========================================================================"
echo ""
echo "OPTION 1: Save to file AND show packet summaries (recommended)"
echo "------------------------------------------------------------------------"

index=0
for node in "${RECEIVER_NODES[@]}"; do
    echo "# $node (receiver $index) - Open in separate terminal"
    if [ "$IP_VERSION" = "4" ]; then
        echo "ssh -t $node 'cd $REMOTE_WORK_DIR/$LOG_DIR && IFACE=\$(ip route get $LB_IPV4 | head -1 | sed \"s/^.*dev//\" | awk \"{ print \\\$1 }\") && sudo timeout $TCPDUMP_DURATION tcpdump -i \$IFACE -w rx_${index}.pcap \"$TCPDUMP_FILTER\" -s 0 -v'"
    else
        echo "ssh -t $node 'cd $REMOTE_WORK_DIR/$LOG_DIR && IFACE=\$(ip route get $LB_IPV6 | head -1 | sed \"s/^.*dev//\" | awk \"{ print \\\$1 }\") && sudo timeout $TCPDUMP_DURATION tcpdump -i \$IFACE -w rx_${index}.pcap \"$TCPDUMP_FILTER\" -s 0 -v'"
    fi
    echo ""
    index=$((index + 1))
done

echo ""
echo "OPTION 2: Show detailed packets only (no file saved)"
echo "------------------------------------------------------------------------"

index=0
for node in "${RECEIVER_NODES[@]}"; do
    echo "# $node (receiver $index) - Open in separate terminal"
    if [ "$IP_VERSION" = "4" ]; then
        echo "ssh -t $node 'cd $REMOTE_WORK_DIR/$LOG_DIR && IFACE=\$(ip route get $LB_IPV4 | head -1 | sed \"s/^.*dev//\" | awk \"{ print \\\$1 }\") && sudo timeout $TCPDUMP_DURATION tcpdump -i \$IFACE \"$TCPDUMP_FILTER\" -s 0 -vvv'"
    else
        echo "ssh -t $node 'cd $REMOTE_WORK_DIR/$LOG_DIR && IFACE=\$(ip route get $LB_IPV6 | head -1 | sed \"s/^.*dev//\" | awk \"{ print \\\$1 }\") && sudo timeout $TCPDUMP_DURATION tcpdump -i \$IFACE \"$TCPDUMP_FILTER\" -s 0 -vvv'"
    fi
    echo ""
    index=$((index + 1))
done

echo "========================================================================"
