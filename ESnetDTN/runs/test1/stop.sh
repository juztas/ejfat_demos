#!/bin/bash
#
# stop.sh - EJFAT DTN Test Cleanup
#
# This script frees the load balancer reservation using the INSTANCE_URI
# from the run_output directory.
#
# Usage:
#   ./stop.sh
#

set -e

#------------------------------------------------------------------------------------------------
# CONFIGURATION
#------------------------------------------------------------------------------------------------

# List of DTN nodes (same as run.sh)
# The first node in the list will be used to free the load balancer
DTN_NODES=(
    "wash-dtn1-mgt.es.net"
    "star-dtn1-mgt.es.net"
    "sunn-dtn1-mgt.es.net"
)

# Path to INSTANCE_URI file
INSTANCE_URI_FILE="run_output/INSTANCE_URI"

# IP version: 4 or 6
IP_VERSION=${IP_VERSION:-6}

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

#------------------------------------------------------------------------------------------------
# MAIN SCRIPT
#------------------------------------------------------------------------------------------------

log "========================================================================="
log "EJFAT DTN Test Cleanup - Freeing Load Balancer"
log "========================================================================="

# Check if INSTANCE_URI file exists
if [ ! -f "$INSTANCE_URI_FILE" ]; then
    error "INSTANCE_URI file not found at: $INSTANCE_URI_FILE"
fi

log "Found INSTANCE_URI file at: $INSTANCE_URI_FILE"
log "INSTANCE_URI contents:"
cat "$INSTANCE_URI_FILE"

# Validate DTN_NODES is not empty
if [ ${#DTN_NODES[@]} -eq 0 ]; then
    error "DTN_NODES array is empty. Please configure at least one DTN node."
fi

# Get the first DTN node for load balancer operations
FIRST_NODE="${DTN_NODES[0]}"

log "========================================================================="
log "Using node: ${FIRST_NODE}"
log "IP version: ${IP_VERSION}"
log "========================================================================="

# Copy INSTANCE_URI to the remote node
log "Copying INSTANCE_URI to ${FIRST_NODE}..."
scp "$INSTANCE_URI_FILE" "${FIRST_NODE}:~/ejfat_demos/perlmutter/INSTANCE_URI"

# Free the load balancer on the first DTN node
log "Freeing load balancer on ${FIRST_NODE}..."

# Use SSH to run the free target from Makefile.local
ssh -t "${FIRST_NODE}" "bash -i -c 'conda activate e2sar && cd ~/ejfat_demos/perlmutter && make -f ../scripts/Makefile.local free IP_VERSION=\"${IP_VERSION}\"'"

log "========================================================================="
log "Load balancer freed successfully!"
log "========================================================================="
