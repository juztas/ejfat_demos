# E2SAR Test Files - Index

## Quick Start

**To run the test right now:**

```bash
conda activate gnuradio
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/e2sar_test
./test_e2sar_simple.py
```

**To verify configuration:**

```bash
./check_e2sar_config.sh
```

## Files Overview

### 🚀 Executable Test Scripts

| File | Description | Usage |
|------|-------------|-------|
| **test_e2sar_simple.py** | Simple loopback test | `./test_e2sar_simple.py` |
| **check_e2sar_config.sh** | Verify configuration | `./check_e2sar_config.sh` |

### 📊 GNU Radio Flowgraphs

| File | Description | Usage |
|------|-------------|-------|
| **test_e2sar_loopback.grc** | Visual flowgraph with displays | `gnuradio-companion test_e2sar_loopback.grc` |

### 📖 Documentation

| File | Purpose | Read When... |
|------|---------|-------------|
| **NO_CONTROL_PLANE_CONFIG.md** | Quick reference for current setup | You want quick info about no-CP mode |
| **E2SAR_CONFIGURATION.md** | Complete configuration guide | You need to understand or change CP settings |
| **E2SAR_TEST_README.md** | Full testing guide | You need detailed test instructions |

### 📁 Related Files

| Location | Description |
|----------|-------------|
| `../../gr-ejfat/examples/test_e2sar_blocks.py` | Separate TX/RX test script |
| `../../custom/segmenter_api.md` | Segmenter API documentation |
| `../../custom/reassembler_api.md` | Reassembler API documentation |

## Configuration Status

```
✓ Control Plane: DISABLED (Standalone Mode)
✓ Mode: Local loopback testing
✓ Data IP: 127.0.0.1
✓ Data Port: 19522
✓ Ready to run: Yes
```

## What Each File Does

### 1. test_e2sar_simple.py ⭐ START HERE

**What it is:** Standalone Python script that tests E2SAR in loopback mode

**What it does:**
- Generates a 10 kHz test tone
- Sends via E2SAR segmenter
- Receives via E2SAR reassembler
- Runs for 30 seconds
- Shows status updates

**When to use:**
- First time testing E2SAR
- Quick validation
- Command-line testing
- Automated testing

**Output:**
```
E2SAR Segmenter/Reassembler Loopback Test
✓ E2SAR Python bindings found
Starting flowgraph...
Running... (5/30 seconds)
Test completed successfully!
```

### 2. test_e2sar_loopback.grc

**What it is:** GNU Radio Companion visual flowgraph

**What it does:**
- Same as simple.py but with GUI
- Shows frequency spectrum
- Shows time domain waveform
- Interactive controls

**When to use:**
- Want to see signal visually
- Need to modify flowgraph
- Learning GNU Radio
- Debugging signal issues

**Output:**
- Two plot windows showing spectrum and waveform
- Visual confirmation of 10 kHz tone

### 3. check_e2sar_config.sh

**What it is:** Configuration verification script

**What it does:**
- Checks use_cp settings in all files
- Shows URI configuration
- Displays key parameters
- Provides recommendations

**When to use:**
- Before running tests
- After modifying configuration
- Troubleshooting
- Confirming no-CP mode

**Output:**
```
✓ Control Plane: DISABLED
  Configuration is optimal for local testing
```

### 4. NO_CONTROL_PLANE_CONFIG.md

**What it is:** Quick reference card

**Contains:**
- Current configuration summary
- Block parameter reference
- What's ignored in no-CP mode
- Troubleshooting tips
- When to use no-CP

**When to read:**
- Quick configuration lookup
- Understanding no-CP mode
- Parameter reference

### 5. E2SAR_CONFIGURATION.md

**What it is:** Comprehensive configuration guide

**Contains:**
- Control plane vs. no control plane comparison
- All parameter descriptions
- URI format explanation
- How to switch modes
- Detailed troubleshooting

**When to read:**
- Need to enable control plane
- Understanding all options
- Deep configuration questions
- Production setup planning

### 6. E2SAR_TEST_README.md

**What it is:** Complete testing guide

**Contains:**
- All available tests
- Prerequisites
- Signal flow diagrams
- Expected results
- Performance tips
- Network testing guide

**When to read:**
- First time setup
- Need testing instructions
- Performance optimization
- Network testing

## File Relationships

```
START HERE
    ↓
check_e2sar_config.sh ──→ Confirms: NO CONTROL PLANE
    ↓
Choose your test:
    ├─→ test_e2sar_simple.py (Command line)
    └─→ test_e2sar_loopback.grc (Visual GUI)

Need help?
    ├─→ NO_CONTROL_PLANE_CONFIG.md (Quick ref)
    ├─→ E2SAR_CONFIGURATION.md (Full config guide)
    └─→ E2SAR_TEST_README.md (Testing guide)
```

## Common Workflows

### Workflow 1: First Time Testing

```bash
# 1. Verify configuration
./check_e2sar_config.sh

# 2. Run simple test
./test_e2sar_simple.py

# 3. If successful, try visual version
gnuradio-companion test_e2sar_loopback.grc
```

### Workflow 2: Troubleshooting

```bash
# 1. Check configuration
./check_e2sar_config.sh

# 2. Read troubleshooting section
cat NO_CONTROL_PLANE_CONFIG.md | grep -A 20 "Troubleshooting"

# 3. Check detailed guide
cat E2SAR_TEST_README.md | grep -A 50 "Troubleshooting"
```

### Workflow 3: Enabling Control Plane

```bash
# 1. Read the configuration guide
less E2SAR_CONFIGURATION.md

# 2. Follow "Switching Between Modes" section

# 3. Update test files as needed

# 4. Verify changes
./check_e2sar_config.sh
```

## Prerequisites Checklist

Before running tests, ensure:

- [ ] GNU Radio environment activated: `conda activate gnuradio`
- [ ] E2SAR Python bindings installed: `python -c "import e2sar_py"`
- [ ] gr-ejfat module installed: `python -c "from gnuradio import ejfat"`
- [ ] In demos directory: `cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos`

**Check all at once:**

```bash
conda activate gnuradio
python -c "
import sys
try:
    import e2sar_py
    print('✓ E2SAR found')
except ImportError:
    print('✗ E2SAR not found')
    sys.exit(1)

try:
    from gnuradio import ejfat
    print('✓ gr-ejfat found')
except ImportError:
    print('✗ gr-ejfat not found')
    sys.exit(1)

print('✓ All prerequisites met!')
"
```

## Quick Reference

### Run Tests

```bash
# Simple script (recommended)
./test_e2sar_simple.py

# Visual flowgraph
gnuradio-companion test_e2sar_loopback.grc
```

### Check Configuration

```bash
# Automated check
./check_e2sar_config.sh

# Manual check
grep use_cp test_e2sar_simple.py
grep use_cp test_e2sar_loopback.grc
```

### View Documentation

```bash
# Quick reference
less NO_CONTROL_PLANE_CONFIG.md

# Full configuration guide
less E2SAR_CONFIGURATION.md

# Testing guide
less E2SAR_TEST_README.md
```

## Configuration Summary

All test files use these settings:

| Parameter | Value | Why |
|-----------|-------|-----|
| `use_cp` | `False` | Standalone mode, no external services |
| Data IP | `127.0.0.1` | Loopback testing |
| Data Port | `19522` | Standard E2SAR port |
| Vector Size | `1024` | Optimal for testing |
| Signal | 10 kHz tone | Easy to verify |
| Sample Rate | 1 MSps | Standard rate |

## Support

If you encounter issues:

1. **Check configuration:** `./check_e2sar_config.sh`
2. **Read troubleshooting:** `NO_CONTROL_PLANE_CONFIG.md` → Troubleshooting section
3. **Check prerequisites:** Verify E2SAR and gr-ejfat are installed
4. **Test UDP loopback:** Use `nc -u -l 19522` test from docs

## Next Steps

After successful testing:

- [ ] Try modifying signal frequency
- [ ] Change vector size
- [ ] Record to file
- [ ] Test over network (not loopback)
- [ ] Enable control plane (if needed)
- [ ] Integrate with your application

## Summary

```
┌────────────────────────────────────────────────────┐
│  E2SAR Test Suite                                  │
├────────────────────────────────────────────────────┤
│  Status: Ready for testing                         │
│  Mode: No control plane (standalone)               │
│  Quick Start: ./test_e2sar_simple.py               │
│  Verify: ./check_e2sar_config.sh                   │
└────────────────────────────────────────────────────┘
```

**You're all set! Start with `./test_e2sar_simple.py`**
