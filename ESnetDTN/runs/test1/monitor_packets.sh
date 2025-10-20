#!/bin/bash
#
# monitor_packets.sh - Monitor EJFAT packet traffic during testing
#
# This script uses tcpdump to capture packets flowing between:
# - Sender and load balancer
# - Load balancer and receivers
#
# Usage: ./monitor_packets.sh [duration_seconds]
#

set -e

# Configuration
DURATION=${1:-180}  # Default 180 seconds (3 minutes)
CAPTURE_FILE="run_output/packet_capture_$(date +%Y%m%d_%H%M%S).pcap"
LOG_FILE="run_output/tcpdump_monitor.log"

# Create run_output directory if it doesn't exist
mkdir -p run_output

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

log "========================================================================="
log "EJFAT Packet Monitor"
log "========================================================================="

# Read INSTANCE_URI to extract load balancer and data IPs
if [ ! -f "run_output/INSTANCE_URI" ]; then
    log "ERROR: INSTANCE_URI file not found. Please run reserve first."
    exit 1
fi

# Source the INSTANCE_URI to get the EJFAT_URI
source run_output/INSTANCE_URI

log "EJFAT_URI: ${EJFAT_URI}"

# Extract load balancer hostname and port
LB_HOST=$(echo "${EJFAT_URI}" | sed -n 's/.*@\([^:]*\):.*/\1/p')
LB_PORT=$(echo "${EJFAT_URI}" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

log "Load Balancer: ${LB_HOST}:${LB_PORT}"

# Resolve load balancer hostname to IP addresses
log "Resolving load balancer hostname..."
LB_IPV4=$(dig +short ${LB_HOST} A | head -1)
LB_IPV6=$(dig +short ${LB_HOST} AAAA | head -1)

if [ -n "${LB_IPV4}" ]; then
    log "Load Balancer IPv4: ${LB_IPV4}"
fi
if [ -n "${LB_IPV6}" ]; then
    log "Load Balancer IPv6: ${LB_IPV6}"
fi

# Extract data IPs from EJFAT_URI
DATA_IPV4=$(echo "${EJFAT_URI}" | grep -o 'data=[0-9.]*' | cut -d= -f2)
DATA_IPV6=$(echo "${EJFAT_URI}" | grep -o 'data=\[[0-9a-f:]*\]' | sed 's/data=\[\(.*\)\]/\1/')

if [ -n "${DATA_IPV4}" ]; then
    log "Data IPv4: ${DATA_IPV4}"
fi
if [ -n "${DATA_IPV6}" ]; then
    log "Data IPv6: ${DATA_IPV6}"
fi

# Build tcpdump filter
# We want to capture:
# 1. Traffic to/from the load balancer (both IPv4 and IPv6)
# 2. Traffic to/from the data IPs
# 3. UDP traffic on relevant ports

FILTER_PARTS=()

if [ -n "${LB_IPV4}" ]; then
    FILTER_PARTS+=("(host ${LB_IPV4})")
fi

if [ -n "${LB_IPV6}" ]; then
    FILTER_PARTS+=("(host ${LB_IPV6})")
fi

if [ -n "${DATA_IPV4}" ]; then
    FILTER_PARTS+=("(host ${DATA_IPV4})")
fi

if [ -n "${DATA_IPV6}" ]; then
    FILTER_PARTS+=("(host ${DATA_IPV6})")
fi

# Join filter parts with OR
FILTER=$(IFS=" or "; echo "${FILTER_PARTS[*]}")

log "Capture file: ${CAPTURE_FILE}"
log "Monitoring duration: ${DURATION} seconds"
log "Filter: ${FILTER}"
log "========================================================================="

# Determine network interface
# Try to find the interface with a route to the load balancer
if [ -n "${LB_IPV6}" ]; then
    INTERFACE=$(ip -6 route get ${LB_IPV6} 2>/dev/null | grep -oP 'dev \K\S+' | head -1)
elif [ -n "${LB_IPV4}" ]; then
    INTERFACE=$(ip route get ${LB_IPV4} 2>/dev/null | grep -oP 'dev \K\S+' | head -1)
fi

if [ -z "${INTERFACE}" ]; then
    log "Could not auto-detect network interface. Using 'any'..."
    INTERFACE="any"
else
    log "Detected network interface: ${INTERFACE}"
fi

log "Starting packet capture..."
log "Press Ctrl+C to stop early, or it will run for ${DURATION} seconds"

# Run tcpdump with timeout
# -i: interface
# -nn: don't resolve hostnames or ports
# -v: verbose
# -s: snaplen (capture full packets)
# -w: write to file
# -G: rotate files every N seconds (we use this for duration)
# -W: number of files to keep (we use 1)

sudo tcpdump -i "${INTERFACE}" -nn -v -s 0 -w "${CAPTURE_FILE}" -G "${DURATION}" -W 1 "${FILTER}" 2>&1 | tee -a "${LOG_FILE}" &

TCPDUMP_PID=$!
log "tcpdump started with PID: ${TCPDUMP_PID}"

# Wait for tcpdump to finish or be interrupted
wait ${TCPDUMP_PID} 2>/dev/null || true

log "========================================================================="
log "Packet capture complete!"
log "Capture file: ${CAPTURE_FILE}"
log "You can analyze it with: tcpdump -r ${CAPTURE_FILE}"
log "Or: tcpdump -r ${CAPTURE_FILE} -nn -v"
log "========================================================================="
