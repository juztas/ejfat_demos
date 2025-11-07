# Code Review: Makefile and Associated Scripts

## Executive Summary

I've reviewed the `ESnetDTN/runs/test2/Makefile` and all scripts invoked by its targets. Overall, the code is well-structured and functional, but there are several opportunities for cleanup, simplification, and improved maintainability.

---

## Major Findings

### 1. **CRITICAL: Hardcoded Path in `generate_tcpdump_commands.sh`**

**Issue:** Lines 139, 186, 189, 202, 205 contain hardcoded path:
```bash
cd ~/ejfat_demos/ESnetDTN/runs/test2/run_output
```

**Impact:** This script is not relocatable and will fail if the Makefile is used in a different directory structure.

**Recommendation:** Use the `REMOTE_WORK_DIR` variable that's already used in the Makefile:
```bash
cd $(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)
```
Pass this as a parameter to the script or calculate it dynamically within the script.

---

### 2. **Redundant Code: Duplicate Overview Logic**

**Issue:** `scripts/reserve` lines 36-42 and 48-53 contain identical code for showing load balancer overview.

**Current:**
```bash
# Lines 36-42 (after validation failure)
echo "" >&2
echo "==========================================================================" >&2
echo "Overview of all load balancers named '$LB_NAME':" >&2
echo "==========================================================================" >&2
lbadm -u "$EJFAT_URI_BETA" $IP_VERSION --overview 2>&1 | grep -A 4 "^LB $LB_NAME " >&2
echo "==========================================================================" >&2

# Lines 48-53 (after new reservation) - IDENTICAL CODE
```

**Recommendation:** Extract to a function:
```bash
show_lb_overview() {
    echo "" >&2
    echo "==========================================================================" >&2
    echo "Overview of all load balancers named '$LB_NAME':" >&2
    echo "==========================================================================" >&2
    lbadm -u "$EJFAT_URI_BETA" $IP_VERSION --overview 2>&1 | grep -A 4 "^LB $LB_NAME " >&2
    echo "==========================================================================" >&2
}

# Then just call it:
show_lb_overview
```

---

### 3. **Inconsistent Error Handling**

**Issue:** Scripts have inconsistent approaches to error handling and exit codes.

**Examples:**
- `scripts/free`: No error handling at all (3 lines total)
- `scripts/reserve`: Some validation but doesn't check lbadm exit codes
- `scripts/send` and `scripts/receive`: `set -e` at top but inconsistent error messages

**Recommendation:** Standardize error handling:
```bash
#!/bin/bash
set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Catch errors in pipes

# Add consistent error reporting
error() {
    echo "ERROR: $*" >&2
    exit 1
}

# Usage
[ -z "$REQUIRED_VAR" ] && error "REQUIRED_VAR not set"
```

---

### 4. **Code Duplication: YAML Parsing Functions**

**Issue:** The `parse_yaml()` function is duplicated in multiple scripts:
- `scripts/send` (line 28)
- `scripts/receive` (line 28)
- `scripts/calculate_sender_duration` (line 14)
- `scripts/generate_tcpdump_commands.sh` (line 35)

Each has slight variations, making maintenance difficult.

**Recommendation:** Create a shared library:

**File: `scripts/lib/common.sh`**
```bash
#!/bin/bash
# Shared library for EJFAT scripts

# Parse YAML value (simple key: value format)
parse_yaml() {
    local yaml_file="$1"
    local key="$2"
    grep "^${key}[[:space:]]*:" "$yaml_file" 2>/dev/null | \
        sed "s/^${key}[[:space:]]*:[[:space:]]*//" | \
        sed "s/[[:space:]]*$//" | \
        sed "s/^['\"]//; s/['\"]$//"
}

# Parse instance-specific YAML with fallback to default
parse_yaml_instance() {
    local yaml_file="$1"
    local key_prefix="$2"
    local instance="$3"

    local instance_key="${key_prefix}_${instance}"
    local value=$(parse_yaml "$yaml_file" "$instance_key")

    if [ -z "$value" ]; then
        value=$(parse_yaml "$yaml_file" "$key_prefix")
    fi

    echo "$value"
}

# Calculate sender duration
calculate_sender_duration() {
    local nframes=$1
    local tx_length=$2
    local tx_rate=$3

    local total_bytes=$(echo "$nframes * $tx_length" | bc)
    local total_bits=$(echo "$total_bytes * 8" | bc)
    local duration=$(echo "scale=2; $total_bits / ($tx_rate * 1000000000)" | bc)

    echo "$duration"
}

# Format duration in human-readable format
format_duration() {
    local total_seconds=$1

    local hours=$(echo "$total_seconds / 3600" | bc)
    local remainder=$(echo "$total_seconds % 3600" | bc)
    local minutes=$(echo "$remainder / 60" | bc)
    local seconds=$(echo "scale=1; $remainder % 60" | bc)

    if [ "$hours" -gt 0 ]; then
        printf "%dh %dm %.1fs" "$hours" "$minutes" "$seconds"
    elif [ "$minutes" -gt 0 ]; then
        printf "%dm %.1fs" "$minutes" "$seconds"
    else
        printf "%.1fs" "$seconds"
    fi
}
```

**Then in each script:**
```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# Now use the functions...
```

---

### 5. **Makefile: Excessive Verbosity in Targets**

**Issue:** The `receive` and `send` targets (lines 238-309, 311-387) have very long loops with repetitive echo statements.

**Current Structure:**
```makefile
receive:
    @echo "========================================================================"
    @echo "Starting Receivers on DTN Nodes"
    @echo "========================================================================"
    @echo "Receiver Nodes:      $(RECEIVERS_LIST)"
    @echo "Receiver Config:     $(RECEIVER_CONFIG)"
    # ... 15 more echo statements
    @i=0; \
    for node in $(RECEIVERS_LIST); do \
        echo "------------------------------------------------------------------------"; \
        echo "Starting receiver $$i on $$node..."; \
        # ... 10+ more lines per iteration
    done
```

**Recommendation:** Extract deployment logic to dedicated scripts:

**File: `scripts/deploy_receiver.sh`**
```bash
#!/bin/bash
# Deploy a single receiver instance

NODE=$1
RX_INDEX=$2
REMOTE_WORK_DIR=$3
RECEIVER_CONFIG=$4
SKIP_UPLOADS=$5

hostname=$(echo $NODE | cut -d'-' -f1)

echo "Starting receiver $RX_INDEX on $NODE..."
echo "  Creating remote directories..."
ssh $NODE "mkdir -p $REMOTE_WORK_DIR/run_output"

if [ "$SKIP_UPLOADS" != "true" ]; then
    echo "  Copying config files..."
    # ... upload logic
fi

echo "  Starting receiver..."
ssh -t $NODE bash -i -c "..."
```

**Simplified Makefile:**
```makefile
receive:
    @echo "========================================================================"
    @echo "Starting Receivers"
    @echo "========================================================================"
    @i=0; \
    for node in $(RECEIVERS_LIST); do \
        $(SCRIPT_DIR)/deploy_receiver.sh $$node $$i $(REMOTE_WORK_DIR) $(RECEIVER_CONFIG) $(SKIP_UPLOADS); \
        i=$$((i+1)); \
    done
```

---

### 6. **IP Detection: Duplicated Logic**

**Issue:** Both `send` and `receive` scripts have nearly identical IP detection logic (send lines 308-321, receive lines 392-408).

**Current (duplicated in both):**
```bash
if [ -z "$MY_IP" ]; then
    if [ "$IP_VERSION" = "4" ]; then
        LB_IP=$(dig +short ejfat-lb.es.net A | tail -1)
    else
        LB_IP=$(dig +short ejfat-lb.es.net AAAA | tail -1)
    fi
    MY_IP=$(ip route get $LB_IP | head -1 | sed 's/^.*src//' | awk '{ print $1 }')
fi
```

**Recommendation:** Add to `lib/common.sh`:
```bash
# Auto-detect IP address based on route to load balancer
detect_my_ip() {
    local ip_version=$1  # "4" or "6"

    if [ "$ip_version" = "4" ]; then
        local lb_ip=$(dig +short ejfat-lb.es.net A | tail -1)
        ip -4 route get $lb_ip | head -1 | sed 's/^.*src//' | awk '{ print $1 }'
    else
        local lb_ip=$(dig +short ejfat-lb.es.net AAAA | tail -1)
        ip -6 route get $lb_ip | head -1 | sed 's/^.*src//' | awk '{ print $1 }'
    fi
}

# Auto-detect network interface
detect_my_interface() {
    local ip_version=$1

    if [ "$ip_version" = "4" ]; then
        local lb_ip=$(dig +short ejfat-lb.es.net A | tail -1)
        ip route get $lb_ip | head -1 | sed 's/^.*dev//' | awk '{ print $1 }'
    else
        local lb_ip=$(dig +short ejfat-lb.es.net AAAA | tail -1)
        ip route get $lb_ip | head -1 | sed 's/^.*dev//' | awk '{ print $1 }'
    fi
}
```

---

### 7. **Makefile: Date Command Portability Issues**

**Issue:** Lines 399-403, 410 have macOS/Linux compatibility workarounds that are complex.

**Current:**
```makefile
if BASE_TIME=$$(date -u -d "$$RUN_ID" +"%s" 2>/dev/null); then \
    RX_START_TIME=$$((BASE_TIME + $(START_OFFSET_MINUTES) * 60)); \
else \
    BASE_TIME=$$(date -u -j -f "%Y%m%d_%H%M%S" "$$RUN_ID" +%s 2>/dev/null); \
    RX_START_TIME=$$((BASE_TIME + $(START_OFFSET_MINUTES) * 60)); \
fi; \
```

**Recommendation:** Use a more portable approach or create a helper script:

**File: `scripts/lib/date_utils.sh`**
```bash
#!/bin/bash
# Portable date parsing

parse_timestamp() {
    local timestamp=$1  # Format: YYYYMMDD_HHMMSS

    # Try GNU date first
    if date -u -d "$timestamp" +"%s" 2>/dev/null; then
        return 0
    fi

    # Try BSD date (macOS)
    if date -u -j -f "%Y%m%d_%H%M%S" "$timestamp" +%s 2>/dev/null; then
        return 0
    fi

    # Fallback: use Python
    python3 -c "from datetime import datetime; print(int(datetime.strptime('$timestamp', '%Y%m%d_%H%M%S').timestamp()))"
}
```

---

### 8. **Configuration: Magic Numbers**

**Issue:** Several magic numbers scattered throughout:

- Makefile line 60: `SENDER_START_DELAY_SECONDS ?= 10`
- receive script line 289: `RX_TIMEOUT="${RX_TIMEOUT:-7000}"`
- send script line 325: `sleep 1` (after registration)
- send script line 528: `sleep 10` (pipeline flush)

**Recommendation:** Consolidate magic numbers into configuration section:

**In Makefile:**
```makefile
# Timing Configuration (all values in seconds unless specified)
START_OFFSET_MINUTES ?= 0
SENDER_START_DELAY_SECONDS ?= 10
POST_REGISTRATION_DELAY ?= 1     # Wait after lbadm --addsenders
PIPELINE_FLUSH_DELAY ?= 10       # Wait before deregistering
RESERVATION_BUFFER_TIME ?= 5     # Wait between reserve and receive
RECEIVER_INIT_TIME ?= 5          # Wait between receive and send
```

---

### 9. **Send Script: Unnecessary Core Detection Complexity**

**Issue:** Lines 198-240 in `send` script have extremely complex logic for core detection with multiple fallback priorities.

**Current:**
```bash
# Priority 1: hostname + ordinal (or index if ordinal not set)
TX_CORES=$(parse_yaml "$CONFIG_FILE" "tx_cores_${SHORT_HOSTNAME}_${LOOKUP_INDEX}")
if [ -n "$TX_CORES" ]; then
    if [ -n "$TX_ORDINAL" ]; then
        TX_CORES_SOURCE="hostname+ordinal (tx_cores_${SHORT_HOSTNAME}_${TX_ORDINAL}, ordinal=$TX_ORDINAL for TX_INDEX=$TX_INDEX)"
    else
        TX_CORES_SOURCE="hostname+instance (tx_cores_${SHORT_HOSTNAME}_${TX_INDEX})"
    fi
else
    # Priority 2: hostname only
    TX_CORES=$(parse_yaml "$CONFIG_FILE" "tx_cores_${SHORT_HOSTNAME}")
    # ... and more
fi
```

**Recommendation:** Simplify to 2-level priority:
```bash
# Try instance-specific cores first, then fall back to default
TX_CORES=$(parse_yaml_instance "$CONFIG_FILE" "tx_cores" "$TX_INDEX")
TX_CORES="${TX_CORES:-1}"  # Default to 1 if not found
```

The hostname-based lookup adds complexity without clear benefit. If per-host configuration is needed, it should be handled in the YAML file itself or via separate config files per host.

---

### 10. **Receive Script: Unused Monitor Code**

**Issue:** Lines 537-539 have disabled UDP socket monitor code that's never enabled.

**Current:**
```bash
# Disabled UDP socket monitor
# udp-socket-monitor.sh -p $MONITOR_PORTS -t $MONITOR_INTERVAL -o $LOG_DIR/rx_${RX_INDEX}_csvfile.csv &
# MONITOR_PID=$!

# ... later ...

# Kill the UDP socket monitor (disabled)
# echo "Stopping UDP socket monitor..."
# kill -15 $MONITOR_PID 2>/dev/null || true
```

**Recommendation:** Either:
1. **Remove it entirely** if it's no longer needed
2. **Make it configurable** if it might be useful:
```bash
ENABLE_SOCKET_MONITOR=$(parse_yaml "$CONFIG_FILE" "enable_socket_monitor")
if [ "$ENABLE_SOCKET_MONITOR" = "true" ]; then
    udp-socket-monitor.sh -p $MONITOR_PORTS -t $MONITOR_INTERVAL -o $LOG_DIR/rx_${RX_INDEX}_csvfile.csv &
    MONITOR_PID=$!
fi
```

---

### 11. **Makefile: Rsync Pattern Inconsistency**

**Issue:** Lines 504-520 (receivers) and 528-540 (senders) use complex rsync patterns with many includes/excludes.

**Current:**
```makefile
rsync -avz --progress --stats --human-readable \
    --partial --partial-dir=.rsync-partial \
    --itemize-changes \
    --exclude="[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]/" \
    --include="RUN_ID" \
    --include="rx_$$i.log" \
    --include="rx_$$i.pcap" \
    --include="rx_*_csvfile.csv" \
    --include="*_$$hostname.yaml" \
    --include="reassembler_config_rx_*.ini" \
    --exclude="*" \
    ...
```

**Recommendation:** Use rsync filter files for better maintainability:

**File: `rsync-filters/receiver.rules`**
```
# Include specific files
+ RUN_ID
+ rx_*.log
+ rx_*.pcap
+ rx_*_csvfile.csv
+ *_*.yaml
+ reassembler_config_rx_*.ini

# Exclude timestamped directories
- [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]/

# Exclude everything else
- *
```

**Makefile:**
```makefile
rsync -avz --filter="merge rsync-filters/receiver.rules" \
    $$node:$(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/ \
    ./$(RECEIVER_LOG_DIR)/
```

---

### 12. **Scripts: Inconsistent Shebang and Options**

**Issue:** Some scripts use `#!/bin/bash` with `set -e`, others don't.

**Current inconsistency:**
- `send`: Has `set -e` (line 18)
- `receive`: Has `set -e` (line 18)
- `reserve`: No `set -e`
- `free`: No `set -e`, ultra-minimal
- `overview`: No `set -e`

**Recommendation:** Standardize all scripts:
```bash
#!/bin/bash
set -e          # Exit on error
set -u          # Exit on undefined variable
set -o pipefail # Catch errors in pipes
```

---

## Minor Issues

### 13. **Logging Inconsistency**

- Some scripts use `>&2` for informational messages (reserve)
- Others use regular stdout (send, receive)
- Makes it hard to separate output from errors

**Recommendation:** Standardize logging:
```bash
log_info() {
    echo "[INFO] $*" >&2
}

log_error() {
    echo "[ERROR] $*" >&2
}

log_debug() {
    if [ "${DEBUG:-false}" = "true" ]; then
        echo "[DEBUG] $*" >&2
    fi
}
```

### 14. **Variable Naming**

Some variable names are unclear:
- `RX_DEQ` (line 294 in receive) - not obvious what "dequeue" means
- `REASSEM_USE_CP` - CP means "Control Plane" but not immediately clear

**Recommendation:** Add comments or use more descriptive names.

### 15. **Comments and Documentation**

Most scripts have good headers, but:
- `free` has no header documentation
- Inline comments are sparse in complex sections
- No documentation of expected YAML structure

**Recommendation:** Add comprehensive header documentation to all scripts.

---

## Specific Recommendations by File

### **Makefile**
1. ✅ Extract deployment loops to separate scripts (`deploy_receiver.sh`, `deploy_sender.sh`)
2. ✅ Create rsync filter files instead of inline patterns
3. ✅ Use helper script for portable date parsing
4. ✅ Consolidate timing constants into configuration section
5. ⚠️ Consider splitting into multiple Makefiles (e.g., `Makefile.deploy`, `Makefile.logs`) and including them

### **scripts/send**
1. ✅ Source `lib/common.sh` for shared functions
2. ✅ Simplify core detection logic (remove complex hostname+ordinal fallbacks)
3. ✅ Extract IP detection to shared function
4. ✅ Make sleep delays configurable
5. ⚠️ Consider extracting INI generation to separate script

### **scripts/receive**
1. ✅ Source `lib/common.sh` for shared functions
2. ✅ Extract IP detection to shared function
3. ✅ Remove or make configurable the disabled monitor code
4. ✅ Consolidate magic numbers
5. ⚠️ Consider extracting INI generation to separate script

### **scripts/reserve**
1. ✅ Extract duplicate overview display to function
2. ✅ Add error handling (`set -e`, check lbadm exit codes)
3. ✅ Standardize logging with `>&2` or helpers

### **scripts/free**
1. ✅ Add error handling
2. ✅ Add header documentation
3. ✅ Verify EJFAT_URI is sourced before running

### **scripts/overview**
1. ✅ Already well-structured, minimal changes needed

### **scripts/generate_tcpdump_commands.sh**
1. 🔴 **CRITICAL:** Remove hardcoded paths, use parameters
2. ✅ Source `lib/common.sh` for parse_yaml
3. ✅ Consider making this output machine-readable (JSON?) for automation

### **scripts/calculate_sender_duration**
1. ✅ Source `lib/common.sh` for shared functions
2. ✅ Already well-documented, minimal changes needed

---

## Implementation Priority

### **High Priority (Do First)**
1. 🔴 Fix hardcoded path in `generate_tcpdump_commands.sh`
2. 🟡 Create `scripts/lib/common.sh` with shared functions
3. 🟡 Update all scripts to source `lib/common.sh`
4. 🟡 Standardize error handling across all scripts

### **Medium Priority (Do Next)**
5. 🟢 Extract duplicate overview logic in `reserve`
6. 🟢 Remove or make configurable the disabled monitor code in `receive`
7. 🟢 Simplify core detection in `send`
8. 🟢 Create rsync filter files

### **Low Priority (Nice to Have)**
9. ⚪ Extract deployment loops to separate scripts
10. ⚪ Create portable date parsing helper
11. ⚪ Standardize logging with helper functions
12. ⚪ Add comprehensive inline comments

---

## Estimated Impact

| Change | Lines Saved | Maintainability | Risk |
|--------|-------------|-----------------|------|
| Create lib/common.sh | ~200 | +++++ | Low |
| Fix hardcoded paths | ~10 | +++++ | Low |
| Extract deployment scripts | ~100 | ++++ | Medium |
| Rsync filter files | ~30 | +++ | Low |
| Simplify core detection | ~40 | ++++ | Low |
| Remove disabled code | ~10 | ++ | Low |

**Total potential line reduction:** ~390 lines (~10% of total codebase)
**Maintainability improvement:** Significant
**Risk level:** Low to Medium

---

## Conclusion

The codebase is functional and well-intentioned, but has accumulated complexity through organic growth. The main issues are:

1. **Code duplication** (YAML parsing, IP detection, duration calculation)
2. **Hardcoded values** (paths, magic numbers)
3. **Inconsistent patterns** (error handling, logging, documentation)
4. **Dead code** (disabled monitor, overly complex fallbacks)

Implementing the shared library (`lib/common.sh`) would be the single highest-impact change, eliminating duplication and establishing patterns for future development.
