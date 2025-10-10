#!/bin/bash
#
# Check E2SAR Configuration
#
# This script verifies the control plane configuration in E2SAR test flowgraphs
#

echo "================================================================"
echo "E2SAR Configuration Checker"
echo "================================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "test_e2sar_loopback.grc" ]; then
    echo -e "${RED}Error: Please run this script from the demos directory${NC}"
    echo "Current directory: $(pwd)"
    echo "Expected files: test_e2sar_loopback.grc, test_e2sar_simple.py"
    exit 1
fi

echo -e "${BLUE}Checking Control Plane Configuration...${NC}"
echo ""

# Function to check use_cp status
check_use_cp() {
    local file=$1
    local block_name=$2

    if [ ! -f "$file" ]; then
        echo -e "${RED}  ✗ File not found: $file${NC}"
        return 1
    fi

    # Extract use_cp values
    use_cp_values=$(grep "use_cp" "$file" | grep -v "^#" | grep -v "comment")

    if [ -z "$use_cp_values" ]; then
        echo -e "${YELLOW}  ⚠ No use_cp configuration found in $file${NC}"
        return 1
    fi

    echo -e "${GREEN}  ✓ Found in $file:${NC}"
    echo "$use_cp_values" | while read line; do
        echo "    $line"
    done
    echo ""
}

# Check GRC flowgraph
echo "1. GNU Radio Companion Flowgraph (test_e2sar_loopback.grc)"
echo "   -------------------------------------------------------"
check_use_cp "test_e2sar_loopback.grc" "GRC"

# Check Python script
echo "2. Simple Python Script (test_e2sar_simple.py)"
echo "   --------------------------------------------"
check_use_cp "test_e2sar_simple.py" "Python"

# Check example script
if [ -f "../../gr-ejfat/examples/test_e2sar_blocks.py" ]; then
    echo "3. Example TX/RX Script (test_e2sar_blocks.py)"
    echo "   -------------------------------------------"
    check_use_cp "../../gr-ejfat/examples/test_e2sar_blocks.py" "Example"
fi

echo ""
echo -e "${BLUE}URI Configuration:${NC}"
echo "   ---------------"

# Extract URI from GRC file
grc_uri=$(grep -A 2 "id: ejfat_uri" test_e2sar_loopback.grc | grep "value:" | sed 's/.*value: //' | sed 's/^ *"//' | sed 's/" *$//')
if [ -n "$grc_uri" ]; then
    echo -e "${GREEN}  GRC URI:${NC}"
    echo "    $grc_uri"
fi

# Extract URI from Python file
python_uri=$(grep "EJFAT_URI" test_e2sar_simple.py | head -1 | sed 's/.*= //' | sed 's/f"//' | sed 's/"$//')
if [ -n "$python_uri" ]; then
    echo -e "${GREEN}  Python URI:${NC}"
    echo "    $python_uri"
fi

echo ""
echo -e "${BLUE}Configuration Summary:${NC}"
echo "   --------------------"

# Count False vs True
false_count=$(grep "use_cp" test_e2sar_loopback.grc test_e2sar_simple.py 2>/dev/null | grep -i "false" | wc -l | tr -d ' ')
true_count=$(grep "use_cp" test_e2sar_loopback.grc test_e2sar_simple.py 2>/dev/null | grep -i "true" | grep -v "False" | wc -l | tr -d ' ')

if [ "$false_count" -gt 0 ] && [ "$true_count" -eq 0 ]; then
    echo -e "${GREEN}  ✓ Control Plane: DISABLED${NC}"
    echo "    Mode: Standalone / No Control Plane"
    echo "    Status: Configured for local testing"
    echo "    Requirements: None (no external services needed)"
elif [ "$true_count" -gt 0 ]; then
    echo -e "${YELLOW}  ⚠ Control Plane: ENABLED${NC}"
    echo "    Mode: With Control Plane"
    echo "    Status: Requires control plane server"
    echo "    Requirements: gRPC server, valid URIs, TLS certs"
else
    echo -e "${RED}  ✗ Control Plane: UNKNOWN${NC}"
    echo "    Could not determine configuration"
fi

echo ""
echo -e "${BLUE}Key Parameters:${NC}"
echo "   --------------"

# Extract key parameters from GRC
data_ip=$(grep -A 2 "id: data_ip" test_e2sar_loopback.grc | grep "value:" | sed 's/.*value: //' | tr -d '"' | tr -d ' ')
data_port=$(grep -A 2 "id: data_port" test_e2sar_loopback.grc | grep "value:" | sed 's/.*value: //' | tr -d ' ')
vector_size=$(grep -A 2 "id: vector_size" test_e2sar_loopback.grc | grep "value:" | sed 's/.*value: //' | tr -d ' ')

echo "  Data IP:     ${data_ip:-127.0.0.1}"
echo "  Data Port:   ${data_port:-19522}"
echo "  Vector Size: ${vector_size:-1024}"

echo ""
echo -e "${BLUE}Recommendations:${NC}"
echo "   ---------------"

if [ "$false_count" -gt 0 ] && [ "$true_count" -eq 0 ]; then
    echo -e "${GREEN}  ✓ Configuration is optimal for local testing${NC}"
    echo "    • No external dependencies required"
    echo "    • Can run immediately with: ./test_e2sar_simple.py"
    echo "    • Or open in GRC: gnuradio-companion test_e2sar_loopback.grc"
else
    echo -e "${YELLOW}  ⚠ Control plane is enabled - ensure:${NC}"
    echo "    • Control plane server is running"
    echo "    • URI points to valid services"
    echo "    • gRPC and TLS are properly configured"
fi

echo ""
echo "================================================================"
echo "For more details, see: E2SAR_CONFIGURATION.md"
echo "================================================================"
echo ""
