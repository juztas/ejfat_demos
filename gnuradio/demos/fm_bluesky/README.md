# FM Radio Bluesky Automated Testing

This directory contains automated test scripts for FM radio reception using Bluesky experiment control.

## Overview

These scripts automate the testing of FM radio reception by:
1. Launching GNU Radio FM transmitter and receiver flowgraphs
2. Using Bluesky to control frequency changes
3. Scanning through real Ottawa FM radio stations
4. Collecting data and posting results to Bluesky social network

## Files

- **run_ottawa_fm_test.py** - Full automated Ottawa FM station scanner
- **run_ottawa_fm_quick_test.py** - Quick test of a few stations
- **fm_bluesky_control.py** - Bluesky control module for FM demos
- **FM_BLUESKY_README.md** - Detailed documentation

## Purpose

### Automated Testing
- Test FM radio reception across multiple stations
- Validate GNU Radio flowgraphs automatically
- Ensure consistent operation

### Bluesky Integration
- Control GNU Radio via XML-RPC from Bluesky
- Collect experiment data in standardized format
- Post results to Bluesky social network

### Real-World Validation
- Tests with actual Ottawa FM radio stations
- Validates reception quality
- Demonstrates practical use cases

## Ottawa FM Radio Stations

The test scripts scan these Ottawa stations:

| Frequency | Station | Format |
|-----------|---------|--------|
| 88.5 MHz | CILV Live 88.5 | Adult Contemporary |
| 89.1 MHz | CHUO | Campus/Community |
| 89.9 MHz | CIHT Hot 89.9 | Top 40 |
| 90.7 MHz | CBOF ICI Première | CBC French |
| 91.5 MHz | CBO CBC Radio One | CBC English |
| 93.9 MHz | CJOT | Classic Hits |
| 94.5 MHz | CIII | Country |
| 96.9 MHz | CKOI | Pop/Rock |
| 99.7 MHz | CHEZ | Classic Rock |
| 101.1 MHz | CFRA | News/Talk |
| 102.5 MHz | BOB FM | Adult Hits |
| 105.3 MHz | The Bear | Rock |
| 106.1 MHz | CKBY | Country |

## Quick Start

### Full Automated Test

Tests all Ottawa FM stations (takes ~13 minutes):

```bash
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/fm_bluesky
conda activate gnuradio
./run_ottawa_fm_test.py
```

### Quick Test

Tests just a few stations (takes ~2 minutes):

```bash
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/fm_bluesky
conda activate gnuradio
./run_ottawa_fm_quick_test.py
```

### Custom Test

```bash
# Test specific stations
./run_ottawa_fm_test.py --stations 88.5 98.5 106.1

# Adjust dwell time per station
./run_ottawa_fm_test.py --dwell-time 10

# Skip Bluesky posting
./run_ottawa_fm_test.py --no-bluesky
```

## Prerequisites

### Required:
- GNU Radio environment: `conda activate gnuradio`
- FM receiver flowgraph in `../fm/`
- RTL-SDR or other SDR hardware
- Antenna for FM reception

### Optional (for Bluesky features):
- Bluesky account credentials
- Bluesky Python SDK: `pip install atproto`
- Ophyd and Bluesky: `pip install ophyd bluesky`

## How It Works

### 1. Flowgraph Startup
```
Script launches:
  - FM transmitter (../fm/fm_transmitter_shm.py)
  - FM receiver (../fm/fm_receiver_shm.py)
Both include XML-RPC servers for remote control
```

### 2. Frequency Control
```
Bluesky scan plan:
  For each station:
    - Set frequency via XML-RPC
    - Wait for stabilization (dwell time)
    - Monitor audio output
    - Collect metrics
```

### 3. Data Collection
```
Each station scan records:
  - Frequency
  - Station name
  - Reception quality
  - Audio presence
  - Timestamp
```

### 4. Results Posting (optional)
```
Post to Bluesky:
  - Summary of stations tested
  - Reception quality report
  - Timestamp and system info
```

## Architecture

```
┌─────────────────────────────────────────────┐
│  Automation Script (run_ottawa_fm_test.py) │
└──────────────┬──────────────────────────────┘
               │
               ├──→ Launch FM Transmitter
               ├──→ Launch FM Receiver
               │
               ↓
┌──────────────────────────────────────────────┐
│           Bluesky Control Layer              │
│  (fm_bluesky_control.py)                     │
└──────────────┬───────────────────────────────┘
               │
               ↓ XML-RPC (port 8080)
┌──────────────────────────────────────────────┐
│      GNU Radio Flowgraphs                    │
│  ┌──────────────┐    ┌──────────────┐       │
│  │ Transmitter  │    │  Receiver    │       │
│  │ (FM TX)      │    │  (FM RX)     │       │
│  └──────────────┘    └──────────────┘       │
└──────────────┬───────────────┬───────────────┘
               │               │
               ↓               ↓
         RTL-SDR           Audio Out
```

## Configuration

### Station List
Edit `run_ottawa_fm_test.py` to modify the station list:

```python
OTTAWA_FM_STATIONS = [
    {"freq": 88.5, "name": "CILV Live 88.5", "format": "Adult Contemporary"},
    # Add or remove stations here
]
```

### Dwell Time
How long to listen to each station (default: 5 seconds):

```bash
./run_ottawa_fm_test.py --dwell-time 10
```

### Bluesky Credentials
Set environment variables:

```bash
export BLUESKY_USERNAME="your.username.bsky.social"
export BLUESKY_PASSWORD="your-app-password"
./run_ottawa_fm_test.py
```

## Expected Results

### Console Output
```
Ottawa FM Radio Station Test
============================================================
Starting flowgraphs...
Waiting for XML-RPC servers to be ready...
✓ Transmitter ready
✓ Receiver ready

Testing station 1/13: CILV Live 88.5 (88.5 MHz)
  Tuning to 88.5 MHz...
  Listening for 5 seconds...
  ✓ Station received

Testing station 2/13: CHUO (89.1 MHz)
...
```

### Bluesky Post (if enabled)
```
Ottawa FM Radio Test Results 📻

Tested 13 stations
✓ All stations received successfully
Test duration: 13:25

System: GNU Radio 3.10 + RTL-SDR
Location: Ottawa, ON
```

## Differences from Manual FM Demos

| Feature | Manual FM Demos | Automated Tests |
|---------|-----------------|-----------------|
| Location | `../fm/` | `fm_bluesky/` |
| Purpose | Interactive testing | Automated validation |
| Control | Manual (GUI sliders) | Automated (Bluesky) |
| Data Collection | Visual observation | Automated logging |
| Station Scanning | Manual tuning | Automated scanning |

## Troubleshooting

### "Flowgraph failed to start"

Check that FM flowgraphs exist:
```bash
ls -l ../fm/fm_receiver_shm.py
ls -l ../fm/fm_transmitter_shm.py
```

### "XML-RPC connection failed"

- Flowgraphs may not have started properly
- Check port 8080 is not already in use: `lsof -i :8080`
- Increase startup wait time in script

### "No audio / No stations received"

- Check RTL-SDR is connected: `rtl_test`
- Verify antenna is connected
- Check if you're in an area with FM reception
- Try increasing dwell time for weaker signals

### "Bluesky posting failed"

- Check credentials are set
- Verify Bluesky SDK is installed: `pip list | grep atproto`
- Run with `--no-bluesky` flag to skip posting

## Related Demos

- **Manual FM Demos**: `../fm/` - Interactive FM radio reception
- **E2SAR Tests**: `../e2sar_test/` - E2SAR protocol testing
- **Widget Demos**: `../widget/` - Bluesky widget control
- **Full System**: `../full_system/` - Complete Bluesky integration

## Dashboard

### Interactive Demo Dashboard

This directory also includes an **interactive Streamlit dashboard** for orchestrating E2SAR demos:

```bash
# Run the dashboard
streamlit run dashboard.py
```

The dashboard opens at `http://localhost:8501` and provides:
- **Load Balancer Management**: Reserve/free EJFAT load balancers
- **Process Control**: Start/stop transmitter and receiver flowgraphs
- **Real-time Status**: Monitor system status and logs
- **Interactive Guide**: Step-by-step narration with integrated slides
- **Modern UI**: Clean, professional web interface

**Dashboard Files:**
- `dashboard.py` - Main Streamlit application
- `dashboard_config.yaml` - Configuration file
- `ejfat_logo.svg` - EJFAT logo (local, SVG format)
- `slides/demo_slides.md` - Presentation slides
- `DASHBOARD_PLAN.md` - Dashboard implementation plan

**Dashboard Usage:**
1. Click "🔒 Reserve LB" to allocate a load balancer
2. Click "▶️ Start TX" to launch the transmitter
3. Click "▶️ Start RX" to launch the receiver
4. Monitor status in the right panel
5. Follow along with the slides in the sidebar
6. Use "⏹️ Stop" buttons and "🔓 Free LB" when done

The dashboard is ideal for:
- Live demonstrations
- Interactive tutorials
- Classroom teaching
- System testing and validation

## See Also

- Detailed documentation: `FM_BLUESKY_README.md`
- Dashboard plan: `DASHBOARD_PLAN.md`
- FM demos: `../fm/README.md`
- Bluesky integration: `../full_system/README.md`
- GNU Radio: https://www.gnuradio.org/
