#!/bin/bash
#
# monitor_sockets.sh - Monitor socket bindings during test
#
# Usage: ./monitor_sockets.sh <node>

NODE="$1"

if [ -z "$NODE" ]; then
    echo "Usage: $0 <node>"
    exit 1
fi

echo "========================================================================"
echo "Socket Binding Diagnostic - $NODE"
echo "Time: $(date)"
echo "========================================================================"
echo ""

# Wait for receivers to start
echo "Waiting 10 seconds for receivers to start..."
sleep 10

echo "========================================================================"
echo "1. All UDP sockets listening"
echo "========================================================================"
ssh "$NODE" "ss -ulanp 2>/dev/null | head -50"
echo ""

echo "========================================================================"
echo "2. Sockets on port 10000"
echo "========================================================================"
ssh "$NODE" "ss -ulanp 2>/dev/null | grep ':10000'"
echo ""

echo "========================================================================"
echo "3. e2sar_perf processes"
echo "========================================================================"
ssh "$NODE" "ps aux | grep e2sar_perf | grep -v grep"
echo ""

echo "========================================================================"
echo "4. IPv6 addresses on dtn1.916"
echo "========================================================================"
ssh "$NODE" "ip -6 addr show dtn1.916"
echo ""

echo "========================================================================"
echo "5. Routing table for data plane subnet"
echo "========================================================================"
ssh "$NODE" "ip -6 route | grep 2001:400:a300"
echo ""

echo "========================================================================"
echo "6. Check if packets are arriving on interface"
echo "========================================================================"
BEFORE=$(ssh "$NODE" "ip -s link show dtn1.916 | grep 'RX:' -A1 | tail -1 | awk '{print \$1}'")
echo "RX bytes before: $BEFORE"
sleep 5
AFTER=$(ssh "$NODE" "ip -s link show dtn1.916 | grep 'RX:' -A1 | tail -1 | awk '{print \$1}'")
echo "RX bytes after: $AFTER"
DIFF=$((AFTER - BEFORE))
echo "Bytes received in 5 seconds: $DIFF"
echo ""

echo "========================================================================"
echo "7. UDP statistics"
echo "========================================================================"
ssh "$NODE" "netstat -su 2>/dev/null | grep -i udp -A 10 || ss -su"
echo ""

echo "Diagnostic complete at $(date)"
