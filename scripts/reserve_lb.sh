#!/bin/bash

# Script to reserve a load balancer using lbadm via Makefile.local
# This script wraps the Makefile.local reserve target for easier use

# Path to the Makefile.local (in the same directory as this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAKEFILE_PATH="${SCRIPT_DIR}/Makefile.local"

# Display usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Reserve an EJFAT load balancer using lbadm.

OPTIONS:
    -u URI          EJFAT_URI_BETA - Base URI for the load balancer service
                    (required, e.g., ejfat://useless@192.168.100.1:18347/lb/1)
    -d DAYS         Reserve duration in days (default: 5)
    -n NAME         Load balancer name (default: yk_testing)
    -i VERSION      IP version: 4 or 6 (default: 6)
    -f FILE         Output file for INSTANCE_URI (default: INSTANCE_URI)
    -w DIR          Working directory (default: current directory)
    -h              Display this help message

EXAMPLES:
    # Reserve with default settings
    $0 -u ejfat://useless@192.168.100.1:18347/lb/1

    # Reserve for 10 days with custom name
    $0 -u ejfat://useless@192.168.100.1:18347/lb/1 -d 10 -n my_lb_test

    # Reserve with IPv4
    $0 -u ejfat://useless@192.168.100.1:18347/lb/1 -i 4

EOF
    exit 1
}

# Default values (matching Makefile.common defaults)
LB_RESERVE_DURATION=5
LB_NAME="yk_testing"
IP_VERSION=6
INSTANCE_URI_FILE="INSTANCE_URI"
WORK_DIR="."
EJFAT_URI_BETA=""

# Parse command line arguments
while getopts "u:d:n:i:f:w:h" opt; do
    case $opt in
        u) EJFAT_URI_BETA="$OPTARG" ;;
        d) LB_RESERVE_DURATION="$OPTARG" ;;
        n) LB_NAME="$OPTARG" ;;
        i) IP_VERSION="$OPTARG" ;;
        f) INSTANCE_URI_FILE="$OPTARG" ;;
        w) WORK_DIR="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

# Check if EJFAT_URI_BETA is set (required)
if [ -z "$EJFAT_URI_BETA" ]; then
    echo "Error: EJFAT_URI_BETA is required. Use -u option to specify the base URI."
    echo ""
    usage
fi

# Verify Makefile exists
if [ ! -f "$MAKEFILE_PATH" ]; then
    echo "Error: Makefile not found at $MAKEFILE_PATH"
    exit 1
fi

# Change to working directory if specified
if [ "$WORK_DIR" != "." ]; then
    if [ ! -d "$WORK_DIR" ]; then
        echo "Error: Working directory $WORK_DIR does not exist"
        exit 1
    fi
    cd "$WORK_DIR" || exit 1
fi

echo "========================================================================"
echo "Reserving EJFAT Load Balancer"
echo "========================================================================"
echo "EJFAT URI BETA:      $EJFAT_URI_BETA"
echo "LB Name:             $LB_NAME"
echo "Reserve Duration:    $LB_RESERVE_DURATION days"
echo "IP Version:          IPv$IP_VERSION"
echo "Instance URI File:   $INSTANCE_URI_FILE"
echo "Working Directory:   $(pwd)"
echo "========================================================================"
echo ""

# Call make with the reserve target
make -f "$MAKEFILE_PATH" reserve \
    EJFAT_URI_BETA="$EJFAT_URI_BETA" \
    LB_RESERVE_DURATION="$LB_RESERVE_DURATION" \
    LB_NAME="$LB_NAME" \
    IP_VERSION="$IP_VERSION" \
    INSTANCE_URI_FILE="$INSTANCE_URI_FILE" \
    WORK_DIR="$(pwd)"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "Load balancer reservation completed successfully!"
    if [ -f "$INSTANCE_URI_FILE" ]; then
        echo "Instance URI saved to: $INSTANCE_URI_FILE"
        echo ""
        cat "$INSTANCE_URI_FILE"
    fi
    echo "========================================================================"
else
    echo ""
    echo "Error: Load balancer reservation failed"
    exit 1
fi
