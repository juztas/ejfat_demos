# E2SAR Segmenter/Reassembler Test Suite

This directory contains test flowgraphs and documentation for testing the E2SAR segmenter and reassembler GNU Radio blocks.

## Quick Start

```bash
conda activate gnuradio
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/e2sar_test

# Verify configuration
./check_e2sar_config.sh

# Run the test
./test_e2sar_simple.py
```

## Files in This Directory

### 🚀 Test Programs

- **test_e2sar_simple.py** - Simple command-line loopback test
- **test_e2sar_loopback.grc** - GNU Radio Companion visual flowgraph
- **check_e2sar_config.sh** - Configuration verification script

### 📖 Documentation

- **README.md** (this file) - Quick overview
- **E2SAR_INDEX.md** - Complete file index and navigation guide ⭐ START HERE
- **NO_CONTROL_PLANE_CONFIG.md** - Quick reference for current configuration
- **E2SAR_CONFIGURATION.md** - Complete configuration guide
- **E2SAR_TEST_README.md** - Full testing guide

## Configuration Status

✓ **Control Plane: DISABLED** (Standalone Mode)
✓ **Mode:** Local loopback testing
✓ **Data IP:** 127.0.0.1
✓ **Data Port:** 19522
✓ **Ready to run:** Yes

## What These Tests Do

The tests demonstrate E2SAR functionality in a simple loopback configuration:

1. **Transmitter:** Generates a 10 kHz test tone
2. **Segmenter:** Breaks signal into events and sends via EJFAT
3. **Reassembler:** Receives events and reconstructs signal
4. **Display:** Shows received signal (in GRC version)

No control plane server needed - perfect for local testing!

## First Time Here?

1. **Read:** `E2SAR_INDEX.md` - Master guide to all files
2. **Verify:** `./check_e2sar_config.sh` - Check configuration
3. **Run:** `./test_e2sar_simple.py` - Run the test
4. **Explore:** `gnuradio-companion test_e2sar_loopback.grc` - Visual version

## Documentation Guide

```
For...                          Read...
────────────────────────────    ─────────────────────────────
Quick overview                  README.md (this file)
Complete file guide             E2SAR_INDEX.md ⭐
Current configuration           NO_CONTROL_PLANE_CONFIG.md
Configuration options           E2SAR_CONFIGURATION.md
Testing instructions            E2SAR_TEST_README.md
```

## Prerequisites

- GNU Radio environment: `conda activate gnuradio`
- E2SAR Python bindings: `python -c "import e2sar_py"`
- gr-ejfat module: `python -c "from gnuradio import ejfat"`

## Support

For issues, see the Troubleshooting sections in:
- `NO_CONTROL_PLANE_CONFIG.md`
- `E2SAR_TEST_README.md`

## See Also

- E2SAR example scripts: `../../gr-ejfat/examples/`
- API documentation: `../../custom/segmenter_api.md`, `../../custom/reassembler_api.md`
- E2SAR repository: https://github.com/JeffersonLab/E2SAR
