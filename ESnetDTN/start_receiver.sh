#!/bin/bash
#
# start_receiver.sh - Start an EJFAT receiver using Makefile
#
# Usage: ./start_receiver.sh [--node <nodename>] <config.yaml>
#
# Options:
#   --node <nodename>  Remote node name for SSH execution (uses Makefile.ssh)
#
# Arguments:
#   config.yaml        Path to YAML configuration file
#
# Examples:
#   ./start_receiver.sh receiver_config.yaml                # Local execution
#   ./start_receiver.sh --node nid001234 receiver_config.yaml  # Remote execution
#

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to display help
show_help() {
    cat << EOF
Usage: ./start_receiver.sh [--node <nodename>] [--log-file <logfile>] <config.yaml>

Start an EJFAT receiver using configuration from a YAML file.

Options:
  --node <nodename>      Remote node name for SSH execution (uses Makefile.ssh)
  --log-file <logfile>   Log file name for e2sar_perf output (placed in run_output/)

Arguments:
  config.yaml            Path to YAML configuration file

Examples:
  ./start_receiver.sh receiver_config.yaml                    # Local execution
  ./start_receiver.sh --node nid001234 receiver_config.yaml   # Remote execution
  ./start_receiver.sh --node nid001234 --log-file rx_0.log receiver_config.yaml

See receiver_config.yaml.example for configuration options.
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
LOG_FILE=""
CONFIG_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --node)
            NODE="$2"
            shift 2
            ;;
        --log-file)
            LOG_FILE="$2"
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
    echo "Usage: ./start_receiver.sh [--node <nodename>] <config.yaml>"
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
RX_DURATION=$(parse_yaml "$CONFIG_FILE" "rx_duration")
RX_BUFSIZE=$(parse_yaml "$CONFIG_FILE" "rx_bufsize")
RX_TIMEOUT=$(parse_yaml "$CONFIG_FILE" "rx_timeout")
RX_CORES=$(parse_yaml "$CONFIG_FILE" "rx_cores")
RX_DEQ=$(parse_yaml "$CONFIG_FILE" "rx_dequeue")
LOG_DIR=$(parse_yaml "$CONFIG_FILE" "log_dir")
MY_INTERFACE=$(parse_yaml "$CONFIG_FILE" "interface")
MONITOR_PORTS=$(parse_yaml "$CONFIG_FILE" "monitor_ports")
MONITOR_INTERVAL=$(parse_yaml "$CONFIG_FILE" "monitor_interval")

# Parse reassembler configuration from YAML
REASSEM_USE_CP=$(parse_yaml "$CONFIG_FILE" "reassem_use_cp")
REASSEM_VALIDATE_CERT=$(parse_yaml "$CONFIG_FILE" "reassem_validate_cert")
REASSEM_USE_HOST_ADDRESS=$(parse_yaml "$CONFIG_FILE" "reassem_use_host_address")
REASSEM_PORT_RANGE=$(parse_yaml "$CONFIG_FILE" "reassem_port_range")
REASSEM_WITH_LB_HEADER=$(parse_yaml "$CONFIG_FILE" "reassem_with_lb_header")
REASSEM_EVENT_TIMEOUT_MS=$(parse_yaml "$CONFIG_FILE" "reassem_event_timeout_ms")
REASSEM_RCV_SOCKET_BUFSIZE=$(parse_yaml "$CONFIG_FILE" "reassem_rcv_socket_bufsize")
REASSEM_EPOCH_MS=$(parse_yaml "$CONFIG_FILE" "reassem_epoch_ms")
REASSEM_PERIOD_MS=$(parse_yaml "$CONFIG_FILE" "reassem_period_ms")
REASSEM_PID_SETPOINT=$(parse_yaml "$CONFIG_FILE" "reassem_pid_setpoint")
REASSEM_PID_KI=$(parse_yaml "$CONFIG_FILE" "reassem_pid_ki")
REASSEM_PID_KP=$(parse_yaml "$CONFIG_FILE" "reassem_pid_kp")
REASSEM_PID_KD=$(parse_yaml "$CONFIG_FILE" "reassem_pid_kd")
REASSEM_PID_WEIGHT=$(parse_yaml "$CONFIG_FILE" "reassem_pid_weight")
REASSEM_PID_MIN_FACTOR=$(parse_yaml "$CONFIG_FILE" "reassem_pid_min_factor")
REASSEM_PID_MAX_FACTOR=$(parse_yaml "$CONFIG_FILE" "reassem_pid_max_factor")

# Set defaults if not specified in YAML
INSTANCE_URI_FILE="${INSTANCE_URI_FILE:-INSTANCE_URI}"
IP_VERSION="${IP_VERSION:-6}"

# Set reassembler defaults
REASSEM_USE_CP="${REASSEM_USE_CP:-true}"
REASSEM_VALIDATE_CERT="${REASSEM_VALIDATE_CERT:-true}"
REASSEM_USE_HOST_ADDRESS="${REASSEM_USE_HOST_ADDRESS:-false}"
REASSEM_PORT_RANGE="${REASSEM_PORT_RANGE:--1}"
REASSEM_WITH_LB_HEADER="${REASSEM_WITH_LB_HEADER:-false}"
REASSEM_EVENT_TIMEOUT_MS="${REASSEM_EVENT_TIMEOUT_MS:-500}"
REASSEM_RCV_SOCKET_BUFSIZE="${REASSEM_RCV_SOCKET_BUFSIZE:-3145728}"
REASSEM_EPOCH_MS="${REASSEM_EPOCH_MS:-1000}"
REASSEM_PERIOD_MS="${REASSEM_PERIOD_MS:-100}"
REASSEM_PID_SETPOINT="${REASSEM_PID_SETPOINT:-0.0}"
REASSEM_PID_KI="${REASSEM_PID_KI:-0.0}"
REASSEM_PID_KP="${REASSEM_PID_KP:-0.0}"
REASSEM_PID_KD="${REASSEM_PID_KD:-0.0}"
REASSEM_PID_WEIGHT="${REASSEM_PID_WEIGHT:-1.0}"
REASSEM_PID_MIN_FACTOR="${REASSEM_PID_MIN_FACTOR:-0.5}"
REASSEM_PID_MAX_FACTOR="${REASSEM_PID_MAX_FACTOR:-2.0}"

# Build make command with only specified variables
MAKE_VARS=""

# Add NODE variable if specified (for Makefile.ssh)
[ -n "$NODE" ] && MAKE_VARS="$MAKE_VARS NODE=$NODE"

# Add LOG_FILE variable if specified
[ -n "$LOG_FILE" ] && MAKE_VARS="$MAKE_VARS PERF_LOG_FILE=$LOG_FILE"

# INSTANCE_URI_FILE is always set (has a default)
MAKE_VARS="$MAKE_VARS INSTANCE_URI_FILE=$INSTANCE_URI_FILE"

# Add IP_VERSION with proper format
MAKE_VARS="$MAKE_VARS IP_VERSION=-$IP_VERSION"

# Add other variables only if they were specified
[ -n "$RX_DURATION" ] && MAKE_VARS="$MAKE_VARS RX_DURATION=$RX_DURATION"
[ -n "$RX_BUFSIZE" ] && MAKE_VARS="$MAKE_VARS RX_BUFSIZE=$RX_BUFSIZE"
[ -n "$RX_TIMEOUT" ] && MAKE_VARS="$MAKE_VARS RX_TIMEOUT=$RX_TIMEOUT"
[ -n "$RX_CORES" ] && MAKE_VARS="$MAKE_VARS RX_CORES=$RX_CORES"
[ -n "$RX_DEQ" ] && MAKE_VARS="$MAKE_VARS RX_DEQ=$RX_DEQ"
[ -n "$LOG_DIR" ] && MAKE_VARS="$MAKE_VARS LOG_DIR=$LOG_DIR"
[ -n "$MY_INTERFACE" ] && MAKE_VARS="$MAKE_VARS MY_INTERFACE=$MY_INTERFACE"
[ -n "$MONITOR_PORTS" ] && MAKE_VARS="$MAKE_VARS MONITOR_PORTS=$MONITOR_PORTS"
[ -n "$MONITOR_INTERVAL" ] && MAKE_VARS="$MAKE_VARS MONITOR_INTERVAL=$MONITOR_INTERVAL"

# Add reassembler configuration variables (always set with defaults)
MAKE_VARS="$MAKE_VARS REASSEM_USE_CP=$REASSEM_USE_CP"
MAKE_VARS="$MAKE_VARS REASSEM_VALIDATE_CERT=$REASSEM_VALIDATE_CERT"
MAKE_VARS="$MAKE_VARS REASSEM_USE_HOST_ADDRESS=$REASSEM_USE_HOST_ADDRESS"
MAKE_VARS="$MAKE_VARS REASSEM_PORT_RANGE=$REASSEM_PORT_RANGE"
MAKE_VARS="$MAKE_VARS REASSEM_WITH_LB_HEADER=$REASSEM_WITH_LB_HEADER"
MAKE_VARS="$MAKE_VARS REASSEM_EVENT_TIMEOUT_MS=$REASSEM_EVENT_TIMEOUT_MS"
MAKE_VARS="$MAKE_VARS REASSEM_RCV_SOCKET_BUFSIZE=$REASSEM_RCV_SOCKET_BUFSIZE"
MAKE_VARS="$MAKE_VARS REASSEM_EPOCH_MS=$REASSEM_EPOCH_MS"
MAKE_VARS="$MAKE_VARS REASSEM_PERIOD_MS=$REASSEM_PERIOD_MS"
MAKE_VARS="$MAKE_VARS REASSEM_PID_SETPOINT=$REASSEM_PID_SETPOINT"
MAKE_VARS="$MAKE_VARS REASSEM_PID_KI=$REASSEM_PID_KI"
MAKE_VARS="$MAKE_VARS REASSEM_PID_KP=$REASSEM_PID_KP"
MAKE_VARS="$MAKE_VARS REASSEM_PID_KD=$REASSEM_PID_KD"
MAKE_VARS="$MAKE_VARS REASSEM_PID_WEIGHT=$REASSEM_PID_WEIGHT"
MAKE_VARS="$MAKE_VARS REASSEM_PID_MIN_FACTOR=$REASSEM_PID_MIN_FACTOR"
MAKE_VARS="$MAKE_VARS REASSEM_PID_MAX_FACTOR=$REASSEM_PID_MAX_FACTOR"

# Generate reassembler_config.ini
INI_FILE="$SCRIPT_DIR/reassembler_config.ini"

cat > "$INI_FILE" << EOF
[general]
; whether to use the control plane (gRPC sendState, registerWorker)
useCP = $REASSEM_USE_CP

[control-plane]
; validate control plane TLS certificate in gRPC communications
validateCert = $REASSEM_VALIDATE_CERT
; force using address (v4 or v6) even if hostname specified in the URI
useHostAddress = $REASSEM_USE_HOST_ADDRESS

[data-plane]
; 2^portRange (0<=portRange<=14) listening ports will be open starting from dataPort.
; If -1, then the number of ports matches either the number of CPU cores or the number of threads. Normally
; this value is calculated based on the number of cores or threads requested, but
; it can be overridden here. Use with caution.
portRange = $REASSEM_PORT_RANGE
; expect LB header to be included (mainly for testing when withCP==false,
; as normally LB strips it off in normal operation)
withLBHeader = $REASSEM_WITH_LB_HEADER
; how long (in ms) we allow events to remain in assembly before we give up
eventTimeoutMS = $REASSEM_EVENT_TIMEOUT_MS
; socket buffer size for receiving set via SO_RCVBUF setsockopt. Note
; that this requires systemwide max set via sysctl (net.core.rmem_max) to be higher.
rcvSocketBufSize = $REASSEM_RCV_SOCKET_BUFSIZE
; period of one epoch in milliseconds
epochMS = $REASSEM_EPOCH_MS
; period of the send state thread in milliseconds
periodMS = $REASSEM_PERIOD_MS

[pid]
; setPoint queue occupied percentage to which to drive the PID controller
setPoint = $REASSEM_PID_SETPOINT
; PID gains (integral, proportional and derivative)
Ki = $REASSEM_PID_KI
Kp = $REASSEM_PID_KP
Kd = $REASSEM_PID_KD
; schedule weight parameters
weight = $REASSEM_PID_WEIGHT
; multiplied with the number of slots that would be assigned evenly to determine min number of slots
; for example, 4 nodes with a minFactor of 0.5 = (512 slots / 4) * 0.5 = min 64 slots
min_factor = $REASSEM_PID_MIN_FACTOR
; multiplied with the number of slots that would be assigned evenly to determine max number of slots
; for example, 4 nodes with a maxFactor of 2 = (512 slots / 4) * 2 = max 256 slots set to 0 to specify no maximum
max_factor = $REASSEM_PID_MAX_FACTOR
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

    echo "Uploading reassembler_config.ini to ${NODE}:${REMOTE_WORK_DIR}..."
    scp "${INI_FILE}" "${NODE}:${REMOTE_WORK_DIR}/reassembler_config.ini"

    # Add REMOTE_WORK_DIR, REMOTE_SCRIPT_DIR, and WORK_DIR to make variables
    MAKE_VARS="$MAKE_VARS REMOTE_WORK_DIR=${REMOTE_WORK_DIR}"
    MAKE_VARS="$MAKE_VARS REMOTE_SCRIPT_DIR=${REMOTE_SCRIPT_DIR}"
    MAKE_VARS="$MAKE_VARS WORK_DIR=${REMOTE_WORK_DIR}"
fi

# Display configuration
echo "========================================================================"
echo "Starting EJFAT Receiver - $EXEC_MODE Execution"
echo "========================================================================"
[ -n "$NODE" ] && echo "Remote Node:  $NODE"
[ -n "$NODE" ] && echo "Remote Dir:   $REMOTE_WORK_DIR"
echo "Config File:  $CONFIG_FILE"
echo "INI File:     $INI_FILE"
echo "Makefile:     $MAKEFILE"
echo "Command:      make -f $MAKEFILE receive $MAKE_VARS"
echo "========================================================================"
echo ""

# Execute make receive
make -f "$MAKEFILE" receive $MAKE_VARS
