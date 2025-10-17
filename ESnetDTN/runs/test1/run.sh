#!/bin/bash
#
# run.sh - EJFAT DTN Test Runner
#
# This script manages EJFAT load balancer reservation and testing across DTN nodes.
# It reserves a load balancer on the first DTN node in the list.
#
# Usage:
#   ./run.sh
#
# Configuration:
#   Edit the DTN_NODES array below to specify the DTN nodes to use.
#

set -e

#------------------------------------------------------------------------------------------------
# CONFIGURATION
#------------------------------------------------------------------------------------------------

# List of DTN nodes to use for testing
# The first node in the list will be used to reserve the load balancer
DTN_NODES=(
    "wash-dtn1-mgt.es.net"
    "star-dtn1-mgt.es.net"
    "sunn-dtn1-mgt.es.net"
)

# Array to store receiver process PIDs
RECEIVER_PIDS=()

# Path to Makefile.ssh
MAKEFILE_SSH="../../../scripts/Makefile.ssh"

# Get Linux username
LINUX_USER=$(whoami)

# Get test directory name (the parent directory of this script)
TEST_DIR_NAME=$(basename "$(dirname "$(realpath "$0")")")

# Build load balancer name: <username>_<test_directory_name>
LB_NAME="${LINUX_USER}_${TEST_DIR_NAME}"

# Load balancer configuration (override defaults from Makefile.common)
EJFAT_URI_BETA=${EJFAT_URI_BETA:-"ejfat://beta.es.net"}  # EJFAT admin URI for reservation
LB_RESERVE_DURATION=${LB_RESERVE_DURATION:-5}  # hours

# IP version: 4 or 6
IP_VERSION=${IP_VERSION:-6}

# Sender configuration (from sender_config.yaml defaults)
TX_RATE=${TX_RATE:-0.1}          # Transmission rate in Gbps
TX_LENGTH=${TX_LENGTH:-2097152}  # Transmission length (packet size in bytes)
NFRAMES=${NFRAMES:-10000}        # Number of frames to send
SEND_SOCKETS=${SEND_SOCKETS:-8}  # Number of send sockets

# Sender node - by default use the first DTN node
SENDER_NODE=${SENDER_NODE:-}

#------------------------------------------------------------------------------------------------
# FUNCTIONS
#------------------------------------------------------------------------------------------------

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
    exit 1
}

# Obfuscate token in EJFAT URI for logging
# Format: ejfat[s]://<token>@ejfat-lb.es.net...
# Shows first 4 and last 4 characters of token
obfuscate_uri() {
    local uri="$1"
    if [[ "$uri" =~ ://([^@]+)@ejfat-lb\.es\.net ]]; then
        local token="${BASH_REMATCH[1]}"
        local token_len=${#token}
        if [ "$token_len" -gt 8 ]; then
            local first4="${token:0:4}"
            local last4="${token: -4}"
            echo "${uri/$token/$first4-------$last4}"
        else
            echo "$uri"
        fi
    else
        echo "$uri"
    fi
}

#------------------------------------------------------------------------------------------------
# MAIN SCRIPT
#------------------------------------------------------------------------------------------------

# Validate DTN_NODES is not empty
if [ ${#DTN_NODES[@]} -eq 0 ]; then
    error "DTN_NODES array is empty. Please configure at least one DTN node."
fi

# Get the first DTN node for load balancer reservation
FIRST_NODE="${DTN_NODES[0]}"

log "========================================================================="
log "EJFAT DTN Test Runner"
log "========================================================================="
log "DTN Nodes configured: ${DTN_NODES[*]}"
log "Load balancer node: ${FIRST_NODE}"
log "EJFAT URI BETA: $(obfuscate_uri "${EJFAT_URI_BETA}")"
log "Reservation duration: ${LB_RESERVE_DURATION} hours"
log "Load balancer name: ${LB_NAME}"
log "IP version: ${IP_VERSION}"
log "========================================================================="

# Ensure run_output directory exists
mkdir -p run_output

# Check if a load balancer with this name already exists
log "Checking if load balancer '${LB_NAME}' already exists on ${FIRST_NODE}..."

# Check if the load balancer exists by running check_lb_exists on the remote node
if ssh "${FIRST_NODE}" "bash -i -c 'conda activate e2sar && cd ~/ejfat_demos/perlmutter && ./check_lb_exists \"${LB_NAME}\" \"${IP_VERSION}\"'"; then
    log "Load balancer '${LB_NAME}' already exists! Skipping reservation."
    log "Retrieving existing INSTANCE_URI..."

    # Get the existing INSTANCE_URI by running a query command
    # We'll use lbadm to get the status and extract the URI for this specific load balancer
    ssh "${FIRST_NODE}" "bash -i -c 'conda activate e2sar && cd ~/ejfat_demos/perlmutter && lbadm ${IP_VERSION} --status | grep -A 5 \"name=${LB_NAME}\" | grep \"EJFAT_URI\" > INSTANCE_URI'" || error "Failed to retrieve INSTANCE_URI for existing load balancer"

    # Copy the INSTANCE_URI file back from the remote node
    scp "${FIRST_NODE}:~/ejfat_demos/perlmutter/INSTANCE_URI" ./run_output/INSTANCE_URI || error "Failed to copy INSTANCE_URI from ${FIRST_NODE}"

    if [ ! -f run_output/INSTANCE_URI ]; then
        error "Failed to retrieve INSTANCE_URI from ${FIRST_NODE}"
    fi

    log "Using existing load balancer!"
    log "INSTANCE_URI contents:"
    cat run_output/INSTANCE_URI
else
    log "Load balancer '${LB_NAME}' does not exist. Reserving new load balancer on ${FIRST_NODE}..."

    # Use Makefile.ssh to reserve the load balancer
    # Note: We need to SSH to the node and run the reserve target from Makefile.local
    ssh -t "${FIRST_NODE}" "bash -i -c 'conda activate e2sar && cd ~/ejfat_demos/perlmutter && make -f ../scripts/Makefile.local reserve EJFAT_URI_BETA=\"${EJFAT_URI_BETA}\" IP_VERSION=\"${IP_VERSION}\" LB_RESERVE_DURATION=\"${LB_RESERVE_DURATION}\" LB_NAME=\"${LB_NAME}\"'"

    # Copy the INSTANCE_URI file back from the remote node
    log "Copying INSTANCE_URI from ${FIRST_NODE}..."
    scp "${FIRST_NODE}:~/ejfat_demos/perlmutter/INSTANCE_URI" ./run_output/INSTANCE_URI

    if [ ! -f run_output/INSTANCE_URI ]; then
        error "Failed to retrieve INSTANCE_URI from ${FIRST_NODE}"
    fi

    log "Load balancer reserved successfully!"
    log "INSTANCE_URI contents:"
    cat run_output/INSTANCE_URI
fi

# Wait 1 second after reserving the load balancer
log "Waiting 1 second after load balancer reservation..."
sleep 1

# Copy INSTANCE_URI to current directory for Makefile.ssh
cp run_output/INSTANCE_URI ./INSTANCE_URI

log "========================================================================="
log "Starting receivers on DTN nodes..."
log "========================================================================="

# Start receiver on each DTN node
for NODE in "${DTN_NODES[@]}"; do
    log "Starting receiver on ${NODE}..."
    ../../start_receiver.sh --node "${NODE}" receiver_config.yaml &

    # Store the background process PID
    RECEIVER_PIDS+=($!)
done

log "All receivers started in background"
log "Receiver PIDs: ${RECEIVER_PIDS[*]}"

# Wait 5 seconds for receivers to fully initialize
log "Waiting 5 seconds for receivers to initialize..."
sleep 5

log "========================================================================="
log "Starting sender..."
log "========================================================================="

# Use first DTN node as sender if not specified
if [ -z "${SENDER_NODE}" ]; then
    SENDER_NODE="${FIRST_NODE}"
fi

log "Sender node: ${SENDER_NODE}"
log "TX rate: ${TX_RATE} Gbps"
log "TX length: ${TX_LENGTH} bytes"
log "Number of frames: ${NFRAMES}"
log "Send sockets: ${SEND_SOCKETS}"

# Start sender
../../start_sender.sh --node "${SENDER_NODE}" sender_config.yaml &

SENDER_PID=$!
log "Sender started in background (PID: ${SENDER_PID})"

log "========================================================================="
log "Setup complete!"
log "INSTANCE_URI saved to: run_output/INSTANCE_URI"
log "Receivers running on all DTN nodes: ${DTN_NODES[*]}"
log "Sender running on: ${SENDER_NODE}"
log "Receiver PIDs: ${RECEIVER_PIDS[*]}"
log "Sender PID: ${SENDER_PID}"
log "========================================================================="
