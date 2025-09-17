#!/usr/bin/env bash
#
#  EJFAT load balancer script (container edition on remote hosts, no shared fs)
#  Wraps the helper binaries in /opt/ejfat_demos/remote
#
set -euo pipefail
BASE_DIR="/opt/ejfat_demos/remote"

# ----------------------
# Default variables
# ----------------------
export IP_VERSION="${IP_VERSION:--6}"
export RX_DURATION="${RX_DURATION:-120}"
export RX_THREADS="${RX_THREADS:-4}"
export TX_RATE="${TX_RATE:-0.1}"
export NFRAMES="${NFRAMES:-20000}"
export DATA_ID="${DATA_ID:-$(( RANDOM % 1000 + 1 ))}"
export EJFAT_LB="ejfat-lb.es.net"
export EJFAT_URI="${EJFAT_URI:-}"

# These below are for file transfer
export RECEIVE_PATH="${RECEIVE_PATH:-/data}"
export RECEIVE_EXTENSION="${RECEIVE_EXTENSION:-root}"
export RECEIVE_PREFIX="${RECEIVE_PREFIX:-test}"
export RECEIVE_TIMEOUT="${RECEIVE_TIMEOUT:-7000}"
export RECEIVE_THREADS="${RECEIVE_THREADS:-4}"

# These below are for sender
# These below are for file transfer
export SEND_PATH="${SEND_PATH:-/data}"
export SEND_EXTENSION="${SEND_EXTENSION:-root}"
export SEND_SOCKETS="${SEND_SOCKETS:-4}"
export SEND_RATE="${SEND_RATE:-1}"


# These are mainly for reservation
export EJFAT_URI_BETA="${EJFAT_URI_BETA:-ejfat://beta.es.net}"
export RESERVER_NAME="${RESERVE_NAME:-my_test_$(( RANDOM % 1000 + 1 ))}"
export RESERVE_TIME="${RESERVE_TIME:-2}" # hours

# Sender configuration
export SEGMENTER_CONF="${SEGMENTER_CONF:-/opt/ejfat_demos/remote/segmenter_config.ini}" 

# Full debug model
if [[ "${DEBUG:-0}" -ne 0 ]]; then
  set -x
fi

# IP resolution
if [[ "$IP_VERSION" == "-4" ]]; then
  LB_IP=$(dig +short $EJFAT_LB A | tail -1)
else
  LB_IP=$(dig +short $EJFAT_LB AAAA | tail -1)
fi
export MY_IP=$(ip route get "$LB_IP" | head -1 | sed 's/^.*src//' | awk '{print $1}')

# ----------------------
# Commands
# ----------------------
cmd_help() { "$BASE_DIR/help"; echo " Good Luck "; } 
cmd_reserve() { "$BASE_DIR/reserve" | grep "EJFAT_URI" > ./INSTANCE_URI; }
cmd_receive() { "$BASE_DIR/receive"; }
cmd_send() { "$BASE_DIR/send"; }
cmd_receive_file() { "$BASE_DIR/receive_file"; }
cmd_send_file() { "$BASE_DIR/send_file"; }
cmd_monitor() { "$BASE_DIR/monitor"; }
cmd_free()    { "$BASE_DIR/free"; }

cmd_test() {
  echo "MY_IP = $MY_IP"
  echo "SCRATCH = ${SCRATCH:-unset}"
}

# ----------------------
# Dispatch
# ----------------------
case "${1:-}" in
  help) cmd_help ;;
  reserve) cmd_reserve ;;
  receive) cmd_receive ;;
  send) cmd_send ;;
  receive_file) cmd_receive_file ;;
  send_file) cmd_send_file ;;
  monitor) cmd_monitor ;;
  free) cmd_free ;;
  test) cmd_test ;;
  ""|-h|--help)
    echo "Usage: $0 {help|reserve|receive|send|receive_file|send_file|monitor|free|test}"
    ;;
  *)
    echo "Unknown command: $1"
    exit 1
    ;;
esac
