#!/bin/bash
#
# start_monitoring.sh - Start tcpdump monitoring on DTN node
#
# This script starts tcpdump on the specified DTN node to monitor EJFAT traffic
#
# Usage: ./start_monitoring.sh [node] [duration]
#

set -e

NODE=${1:-wash-dtn1-mgt.es.net}
DURATION=${2:-180}  # Default 180 seconds (3 minutes)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "========================================================================="
log "Starting packet monitoring on ${NODE}"
log "Duration: ${DURATION} seconds"
log "========================================================================="

# Read INSTANCE_URI to extract IPs for filtering
if [ ! -f "run_output/INSTANCE_URI" ]; then
    log "ERROR: INSTANCE_URI file not found. Please run reserve first."
    exit 1
fi

# Source the INSTANCE_URI to get the EJFAT_URI
source run_output/INSTANCE_URI

# Extract load balancer info
LB_HOST=$(echo "${EJFAT_URI}" | sed -n 's/.*@\([^:]*\):.*/\1/p')
LB_PORT=$(echo "${EJFAT_URI}" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

log "Monitoring traffic to/from: ${LB_HOST}:${LB_PORT}"

# Create remote monitoring script
REMOTE_SCRIPT=$(cat <<'EOF'
#!/bin/bash

LB_HOST="$1"
LB_PORT="$2"
DURATION="$3"

CAPTURE_FILE="/tmp/ejfat_capture_$(date +%Y%m%d_%H%M%S).pcap"
LOG_FILE="/tmp/ejfat_tcpdump.log"

echo "[$(date)] Starting tcpdump monitoring..." | tee ${LOG_FILE}
echo "[$(date)] Load Balancer: ${LB_HOST}:${LB_PORT}" | tee -a ${LOG_FILE}
echo "[$(date)] Capture file: ${CAPTURE_FILE}" | tee -a ${LOG_FILE}

# Resolve LB hostname - filter out CNAME records (lines ending with .)
LB_IPV4=$(dig +short ${LB_HOST} A | grep -v '\.$' | head -1)
LB_IPV6=$(dig +short ${LB_HOST} AAAA | grep -v '\.$' | head -1)

echo "[$(date)] LB IPv4: ${LB_IPV4}" | tee -a ${LOG_FILE}
echo "[$(date)] LB IPv6: ${LB_IPV6}" | tee -a ${LOG_FILE}

# Build filter for load balancer traffic
if [ -n "${LB_IPV6}" ]; then
    FILTER="host ${LB_IPV6} and udp"
    INTERFACE=$(ip -6 route get ${LB_IPV6} 2>/dev/null | grep -oP 'dev \K\S+' | head -1)
    if [ -z "${INTERFACE}" ]; then
        INTERFACE="any"
    fi
elif [ -n "${LB_IPV4}" ]; then
    FILTER="host ${LB_IPV4} and udp"
    INTERFACE=$(ip route get ${LB_IPV4} 2>/dev/null | grep -oP 'dev \K\S+' | head -1)
    if [ -z "${INTERFACE}" ]; then
        INTERFACE="any"
    fi
else
    # Fallback: just filter by port on all interfaces
    FILTER="udp port ${LB_PORT}"
    INTERFACE="any"
fi

echo "[$(date)] Interface: ${INTERFACE}" | tee -a ${LOG_FILE}
echo "[$(date)] Filter: ${FILTER}" | tee -a ${LOG_FILE}
echo "[$(date)] Starting capture for ${DURATION} seconds..." | tee -a ${LOG_FILE}

# Run tcpdump
sudo timeout ${DURATION} tcpdump -i ${INTERFACE} -nn -v -s 0 -w ${CAPTURE_FILE} "${FILTER}" 2>&1 | tee -a ${LOG_FILE} &
TCPDUMP_PID=$!

echo "[$(date)] tcpdump PID: ${TCPDUMP_PID}" | tee -a ${LOG_FILE}
echo "[$(date)] Monitoring in progress..." | tee -a ${LOG_FILE}
echo "[$(date)] Log file: ${LOG_FILE}" | tee -a ${LOG_FILE}
echo "[$(date)] Capture file: ${CAPTURE_FILE}" | tee -a ${LOG_FILE}
EOF
)

# Start monitoring on remote node
log "Starting tcpdump on ${NODE}..."
ssh -t "${NODE}" "bash -s" -- "${LB_HOST}" "${LB_PORT}" "${DURATION}" <<< "${REMOTE_SCRIPT}" &

MONITOR_PID=$!
log "Monitoring started in background (local PID: ${MONITOR_PID})"
log "Tcpdump will run for ${DURATION} seconds on ${NODE}"
log "========================================================================="

# Save PID for later reference
echo ${MONITOR_PID} > run_output/monitor_pid.txt
log "Monitor PID saved to run_output/monitor_pid.txt"
