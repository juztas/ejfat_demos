#!/bin/bash
#
# collect_logs.sh - Collect log files from remote DTN nodes
#
# Usage: ./collect_logs.sh
#

set -e

# DTN nodes to collect from
DTN_NODES=(
    "wash-dtn1-mgt.es.net"
    "star-dtn1-mgt.es.net"
    "sunn-dtn1-mgt.es.net"
)

# Get test directory name
TEST_NAME=$(basename "$(pwd)")

# Local output directory
LOCAL_OUTPUT_DIR="run_output"

# Remote base directory (will be expanded on remote node)
REMOTE_BASE_DIR="~/ejfat_demos/runs/${TEST_NAME}/run_output"

echo "========================================================================="
echo "Collecting logs from remote nodes to: ${LOCAL_OUTPUT_DIR}"
echo "========================================================================="

# Create local output directory if it doesn't exist
mkdir -p "${LOCAL_OUTPUT_DIR}"

# Collect logs from each node
for NODE in "${DTN_NODES[@]}"; do
    echo "Collecting logs from ${NODE}..."

    # Download all CSV files
    scp "${NODE}:${REMOTE_BASE_DIR}/*.csv" "${LOCAL_OUTPUT_DIR}/" 2>/dev/null || echo "  No CSV files found on ${NODE}"

    # Download rx_*.log and tx_*.log files (e2sar_perf output logs)
    scp "${NODE}:${REMOTE_BASE_DIR}/rx_*.log" "${LOCAL_OUTPUT_DIR}/" 2>/dev/null || echo "  No rx_*.log files found on ${NODE}"
    scp "${NODE}:${REMOTE_BASE_DIR}/tx_*.log" "${LOCAL_OUTPUT_DIR}/" 2>/dev/null || echo "  No tx_*.log files found on ${NODE}"

    # Download any other log files
    scp "${NODE}:${REMOTE_BASE_DIR}/*.log" "${LOCAL_OUTPUT_DIR}/" 2>/dev/null || echo "  No other log files found on ${NODE}"

    echo "  Done."
done

echo "========================================================================="
echo "Log collection complete!"
echo "Logs are in: ${LOCAL_OUTPUT_DIR}"
echo "========================================================================="
ls -lh "${LOCAL_OUTPUT_DIR}"
