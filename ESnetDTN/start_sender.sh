#!/bin/bash
#
# start_sender.sh - Start an EJFAT sender using Makefile
#
# Usage: ./start_sender.sh [--node <nodename>] <config.yaml>
#
# Options:
#   --node <nodename>  Remote node name for SSH execution (uses Makefile.ssh)
#
# Arguments:
#   config.yaml        Path to YAML configuration file
#
# Examples:
#   ./start_sender.sh sender_config.yaml                # Local execution
#   ./start_sender.sh --node nid001234 sender_config.yaml  # Remote execution
#

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to display help
show_help() {
    cat << EOF
Usage: ./start_sender.sh [--node <nodename>] <config.yaml>

Start an EJFAT sender using configuration from a YAML file.

Options:
  --node <nodename>  Remote node name for SSH execution (uses Makefile.ssh)

Arguments:
  config.yaml        Path to YAML configuration file

Examples:
  ./start_sender.sh sender_config.yaml                    # Local execution
  ./start_sender.sh --node nid001234 sender_config.yaml   # Remote execution

See sender_config.yaml.example for configuration options.
EOF
    exit 0
}

# Function to parse YAML and extract value
parse_yaml() {
    local yaml_file="$1"
    local key="$2"
    # Simple YAML parser for key: value format
    grep "^${key}:" "$yaml_file" 2>/dev/null | sed "s/^${key}:[[:space:]]*//" | sed "s/[[:space:]]*$//" | sed "s/^['\"]//; s/['\"]$//"
}

# Check for help flag
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_help
fi

# Parse command line arguments
NODE=""
CONFIG_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --node)
            NODE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            CONFIG_FILE="$1"
            shift
            ;;
    esac
done

# Check if config file is provided
if [[ -z "$CONFIG_FILE" ]]; then
    echo "Error: Configuration file required"
    echo "Usage: ./start_sender.sh [--node <nodename>] <config.yaml>"
    echo "Use -h or --help for more information"
    exit 1
fi

# Check if config file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Determine which Makefile to use
# Use absolute path relative to this script's location
if [[ -n "$NODE" ]]; then
    MAKEFILE="$(dirname "$SCRIPT_DIR")/scripts/Makefile.ssh"
    EXEC_MODE="Remote SSH"
else
    MAKEFILE="$(dirname "$SCRIPT_DIR")/scripts/Makefile.local"
    EXEC_MODE="Local"
fi

# Parse configuration from YAML
INSTANCE_URI_FILE=$(parse_yaml "$CONFIG_FILE" "instance_uri_file")
IP_VERSION=$(parse_yaml "$CONFIG_FILE" "ip_version")
TX_RATE=$(parse_yaml "$CONFIG_FILE" "tx_rate")
TX_LENGTH=$(parse_yaml "$CONFIG_FILE" "tx_length")
NFRAMES=$(parse_yaml "$CONFIG_FILE" "nframes")
SEND_SOCKETS=$(parse_yaml "$CONFIG_FILE" "send_sockets")
DATA_ID=$(parse_yaml "$CONFIG_FILE" "data_id")

# Parse segmenter configuration from YAML
USE_CP=$(parse_yaml "$CONFIG_FILE" "use_cp")
WARMUP_MS=$(parse_yaml "$CONFIG_FILE" "warmup_ms")
SYNC_PERIOD_MS=$(parse_yaml "$CONFIG_FILE" "sync_period_ms")
SYNC_PERIODS=$(parse_yaml "$CONFIG_FILE" "sync_periods")
CONNECTED_SOCKET=$(parse_yaml "$CONFIG_FILE" "connected_socket")
MTU=$(parse_yaml "$CONFIG_FILE" "mtu")
SND_SOCKET_BUFSIZE=$(parse_yaml "$CONFIG_FILE" "snd_socket_bufsize")
SMOOTH=$(parse_yaml "$CONFIG_FILE" "smooth")
MULTI_PORT=$(parse_yaml "$CONFIG_FILE" "multi_port")

# Set defaults if not specified in YAML
INSTANCE_URI_FILE="${INSTANCE_URI_FILE:-INSTANCE_URI}"
IP_VERSION="${IP_VERSION:-6}"

# Set segmenter defaults
USE_CP="${USE_CP:-true}"
WARMUP_MS="${WARMUP_MS:-1000}"
SYNC_PERIOD_MS="${SYNC_PERIOD_MS:-1000}"
SYNC_PERIODS="${SYNC_PERIODS:-2}"
CONNECTED_SOCKET="${CONNECTED_SOCKET:-true}"
MTU="${MTU:-0}"
SND_SOCKET_BUFSIZE="${SND_SOCKET_BUFSIZE:-3145728}"
SMOOTH="${SMOOTH:-false}"
MULTI_PORT="${MULTI_PORT:-false}"

# Build make command with only specified variables
MAKE_VARS=""

# Add NODE variable if specified (for Makefile.ssh)
[ -n "$NODE" ] && MAKE_VARS="$MAKE_VARS NODE=$NODE"

# INSTANCE_URI_FILE is always set (has a default)
MAKE_VARS="$MAKE_VARS INSTANCE_URI_FILE=$INSTANCE_URI_FILE"

# Add IP_VERSION with proper format
MAKE_VARS="$MAKE_VARS IP_VERSION=-$IP_VERSION"

# Add other variables only if they were specified
[ -n "$TX_RATE" ] && MAKE_VARS="$MAKE_VARS TX_RATE=$TX_RATE"
[ -n "$TX_LENGTH" ] && MAKE_VARS="$MAKE_VARS TX_LENGTH=$TX_LENGTH"
[ -n "$NFRAMES" ] && MAKE_VARS="$MAKE_VARS NFRAMES=$NFRAMES"
[ -n "$SEND_SOCKETS" ] && MAKE_VARS="$MAKE_VARS SEND_SOCKETS=$SEND_SOCKETS"
[ -n "$DATA_ID" ] && MAKE_VARS="$MAKE_VARS DATA_ID=$DATA_ID"

# Add segmenter configuration variables (always set with defaults)
MAKE_VARS="$MAKE_VARS USE_CP=$USE_CP"
MAKE_VARS="$MAKE_VARS WARMUP_MS=$WARMUP_MS"
MAKE_VARS="$MAKE_VARS SYNC_PERIOD_MS=$SYNC_PERIOD_MS"
MAKE_VARS="$MAKE_VARS SYNC_PERIODS=$SYNC_PERIODS"
MAKE_VARS="$MAKE_VARS CONNECTED_SOCKET=$CONNECTED_SOCKET"
MAKE_VARS="$MAKE_VARS MTU=$MTU"
MAKE_VARS="$MAKE_VARS SND_SOCKET_BUFSIZE=$SND_SOCKET_BUFSIZE"
MAKE_VARS="$MAKE_VARS SMOOTH=$SMOOTH"
MAKE_VARS="$MAKE_VARS MULTI_PORT=$MULTI_PORT"

# Generate segmenter_config.ini
INI_FILE="$SCRIPT_DIR/segmenter_config.ini"

# Determine rate value (-1.0 for full rate, or specified value)
if [[ -n "$TX_RATE" ]]; then
    RATE_GBPS="$TX_RATE"
else
    RATE_GBPS="-1.0"
fi

# Determine number of send sockets
if [[ -n "$SEND_SOCKETS" ]]; then
    NUM_SOCKETS="$SEND_SOCKETS"
else
    NUM_SOCKETS="4"
fi

# Use IPv6 preference based on IP_VERSION
if [[ "$IP_VERSION" == "6" ]]; then
    DPV6="true"
else
    DPV6="false"
fi

cat > "$INI_FILE" << EOF
[general]
; enable control plane to send Sync packets
useCP = $USE_CP

[control-plane]
; warm up period between sync thread starting and data allowed to be sent
warmUpMS = $WARMUP_MS
; sync thread period in milliseconds
syncPeriodMS = $SYNC_PERIOD_MS
; number of sync periods to use for averaging reported send rate
syncPeriods = $SYNC_PERIODS

[data-plane]
; prefer V6 dataplane if the URI specifies both data=<ipv4>&data=<ipv6> addresses
dpV6 = $DPV6
; use connected sockets
connectedSocket = $CONNECTED_SOCKET
; size of the MTU to attempt to fit the segmented data in (must accommodate IP, UDP
; and LBRE headers). Value of 0 means auto-detect based on MTU of outgoing interface
; (Linux only)
mtu = $MTU
; number of sockets/source ports we will be sending data from.
; The more, the more randomness the LAG will see in delivering to different FPGA ports
numSendSockets = $NUM_SOCKETS
; socket buffer size for sending set via SO_SNDBUF setsockopt.
; Note that this requires systemwide max set via sysctl (net.core.wmem_max) to be higher
sndSocketBufSize = $SND_SOCKET_BUFSIZE
; send rate in Gbps (can be fractions). Negative value means send full rate
rateGbps = $RATE_GBPS
; smooth out the rate per-frame rather than per event (for low rate values)
smooth = $SMOOTH
; use numSendSockets consecutive destination ports starting from EjfatURI data port,
; rather than a single port; source ports are still randomized
; (incompatible with a load balancer, only useful in back-to-back testing)
multiPort = $MULTI_PORT
EOF

# If executing remotely, upload config files to remote node
if [[ -n "$NODE" ]]; then
    # Determine test directory name (e.g., test1, test2, etc.)
    # Use the current directory name if running from runs/testX, otherwise use 'default'
    CURRENT_DIR=$(basename "$PWD")
    if [[ "$PWD" =~ /runs/([^/]+)$ ]]; then
        TEST_NAME="${BASH_REMATCH[1]}"
    else
        TEST_NAME="default"
    fi

    # Remote work directory for this test
    # Get the home directory on the remote node and use absolute paths
    REMOTE_HOME=$(ssh "${NODE}" 'echo $HOME')
    REMOTE_WORK_DIR="${REMOTE_HOME}/ejfat_demos/runs/${TEST_NAME}/run_output"
    # Script directory is always relative to the ejfat_demos directory
    REMOTE_SCRIPT_DIR="${REMOTE_HOME}/ejfat_demos/scripts"

    echo "Creating remote work directory: ${REMOTE_WORK_DIR} on ${NODE}..."
    ssh "${NODE}" "mkdir -p ${REMOTE_WORK_DIR}"

    echo "Uploading segmenter_config.ini to ${NODE}:${REMOTE_WORK_DIR}..."
    scp "${INI_FILE}" "${NODE}:${REMOTE_WORK_DIR}/segmenter_config.ini"

    # Add REMOTE_WORK_DIR, REMOTE_SCRIPT_DIR, and WORK_DIR to make variables
    MAKE_VARS="$MAKE_VARS REMOTE_WORK_DIR=${REMOTE_WORK_DIR}"
    MAKE_VARS="$MAKE_VARS REMOTE_SCRIPT_DIR=${REMOTE_SCRIPT_DIR}"
    MAKE_VARS="$MAKE_VARS WORK_DIR=${REMOTE_WORK_DIR}"
fi

# Display configuration
echo "========================================================================"
echo "Starting EJFAT Sender - $EXEC_MODE Execution"
echo "========================================================================"
[ -n "$NODE" ] && echo "Remote Node:  $NODE"
[ -n "$NODE" ] && echo "Remote Dir:   $REMOTE_WORK_DIR"
echo "Config File:  $CONFIG_FILE"
echo "INI File:     $INI_FILE"
echo "Makefile:     $MAKEFILE"
echo "Command:      make -f $MAKEFILE send $MAKE_VARS"
echo "========================================================================"
echo ""

# Execute make send
make -f "$MAKEFILE" send $MAKE_VARS
