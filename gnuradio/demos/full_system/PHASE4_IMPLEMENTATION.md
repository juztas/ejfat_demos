# Phase 4 Implementation: Experiment Types & Plans

**Status:** ✅ **COMPLETE**
**Date:** 2025-10-08
**Reference:** BLUESKY_COMPREHENSIVE_PLAN.md Phase 4 (lines 353-449)

## Overview

Phase 4 of the Bluesky Comprehensive Plan focuses on implementing various experiment types and scan plans. This phase demonstrates the flexibility and power of the Bluesky framework for different experimental scenarios.

## Implementation Summary

### Core Plans (bluesky_config/plans.py)

All plan types from Phase 4 have been implemented in `bluesky_config/plans.py`:

| Plan Type | Function Name | Description |
|-----------|--------------|-------------|
| **Basic Scans** | `frequency_scan()` | Linear frequency scan with detector readings |
| | `frequency_sweep()` | Frequency sweep without detector (visual observation) |
| | `grid_scan_2d()` | 2D grid scan wrapper for two parameters |
| **Adaptive Scans** | `adaptive_frequency_scan()` | Variable step size based on signal derivative |
| **Time Series** | `time_series_acquisition()` | Repeated measurements at fixed configuration |
| **Custom Plans** | `frequency_characterization()` | Multiple samples at each frequency for statistics |
| | `peak_finding_scan()` | Two-stage scan (coarse + fine around peaks) |
| **Multi-Device** | `synchronized_tx_rx_scan()` | Synchronized TX/RX frequency movement |

### Experiment Scripts (experiments/)

Complete experiment implementations demonstrating each plan type:

#### 1. Basic Scans
- **frequency_characterization.py** - Characterizes signal response at specific frequencies with multiple samples per point
- **signal_quality_scan.py** - Scans frequency range while monitoring signal quality metrics

#### 2. Adaptive Scans
- **adaptive_tuning.py** ✨ *NEW* - Uses adaptive step size to efficiently map frequency response
  - Takes smaller steps where signal changes rapidly
  - Takes larger steps where signal is stable
  - Ideal for unknown signal landscapes

#### 3. Time Series
- **time_series_monitoring.py** ✨ *NEW* - Monitors signal stability over time at fixed frequency
  - Detects variations, drift, and intermittent issues
  - Includes threshold alerting for anomalies
  - Useful for long-term stability testing

#### 4. Custom Plans (Peak Finding)
- **peak_finding_experiment.py** ✨ *NEW* - Two-stage intelligent peak detection
  - Stage 1: Quick coarse scan to locate peaks
  - Stage 2: Fine scan around each detected peak
  - Efficient for sparse signals (e.g., FM broadcast stations)

#### 5. Multi-Device Coordination
- **synchronized_sweep.py** ✨ *NEW* - Synchronized TX/RX frequency sweep
  - Keeps TX and RX frequencies locked together
  - Demonstrates multi-device coordination
  - Ensures proper synchronization with settling delays

#### 6. 2D Grid Scans
- **grid_scan_experiment.py** ✨ *NEW* - Maps 2D parameter space (TX freq vs RX freq)
  - Creates heat map of response surface
  - Uses efficient snake pattern for scanning
  - Total of 225 points (15×15 grid)
  - Results visualizable as 2D heat map

#### 7. Testing & Development
- **mock_experiment.py** - Simple test using mock devices (no hardware required)
- **test_all_experiments.py** ✨ *NEW* - Comprehensive test suite for all Phase 4 experiment types

## File Structure

```
full_system/
├── bluesky_config/
│   ├── plans.py              # All Phase 4 scan plans implemented here
│   ├── devices.py            # Ophyd device definitions
│   ├── callbacks.py          # Custom callbacks
│   └── metadata.py           # Metadata utilities
├── experiments/
│   ├── frequency_characterization.py    # Basic scan - custom plan
│   ├── signal_quality_scan.py           # Basic scan - standard
│   ├── adaptive_tuning.py               # Adaptive scan ✨ NEW
│   ├── time_series_monitoring.py        # Time series ✨ NEW
│   ├── peak_finding_experiment.py       # Custom peak finding ✨ NEW
│   ├── synchronized_sweep.py            # Multi-device ✨ NEW
│   ├── grid_scan_experiment.py          # 2D grid scan ✨ NEW
│   └── mock_experiment.py               # Testing with mocks
├── test_all_experiments.py              # Comprehensive test ✨ NEW
└── BLUESKY_COMPREHENSIVE_PLAN.md        # Master plan document
```

## Usage Examples

### Run Individual Experiments

```bash
# Adaptive tuning (efficient frequency mapping)
./experiments/adaptive_tuning.py

# Time series monitoring (stability over time)
./experiments/time_series_monitoring.py

# Peak finding (locate FM stations)
./experiments/peak_finding_experiment.py

# Synchronized TX/RX sweep
./experiments/synchronized_sweep.py

# 2D grid scan (map TX vs RX response)
./experiments/grid_scan_experiment.py
```

### Run Comprehensive Test Suite

```bash
# Interactive mode (select experiments)
./test_all_experiments.py

# Run all experiments
./test_all_experiments.py --all

# Run specific types
./test_all_experiments.py --basic --adaptive
./test_all_experiments.py --timeseries --peaks
./test_all_experiments.py --multidevice --grid

# Use mock devices (no GNU Radio required)
./test_all_experiments.py --all --mock
```

## Phase 4 Requirements Checklist

From BLUESKY_COMPREHENSIVE_PLAN.md Phase 4:

- ✅ **Basic Scans**
  - ✅ `scan()` - Linear scan (using built-in Bluesky)
  - ✅ `grid_scan()` - 2D grid (wrapper implemented)
  - ✅ `list_scan()` - Arbitrary points (can use built-in)

- ✅ **Adaptive Scans**
  - ✅ `adaptive_frequency_scan()` - Step size based on derivative
  - ✅ Example experiment demonstrating adaptive behavior

- ✅ **Time Series**
  - ✅ `time_series_acquisition()` - Repeated measurements
  - ✅ Example experiment with statistics and monitoring

- ✅ **Custom Plans**
  - ✅ `frequency_characterization()` - Multiple samples per point
  - ✅ `peak_finding_scan()` - Two-stage intelligent scanning
  - ✅ Proper metadata decoration

- ✅ **Multi-Device Coordination**
  - ✅ `synchronized_tx_rx_scan()` - Coordinated device movement
  - ✅ Example experiment demonstrating synchronization
  - ✅ Proper settling delays to prevent segfaults

## Key Features Implemented

### 1. Intelligent Scanning
- **Adaptive step sizing** - Automatically adjusts resolution based on signal behavior
- **Two-stage peak finding** - Efficient coarse scan followed by fine characterization
- **Snake pattern grid scans** - Minimizes movement in 2D scans

### 2. Multi-Device Coordination
- **Synchronized movements** - TX and RX stay locked together
- **Proper settling delays** - 1-2 second delays prevent GNU Radio segfaults
- **Independent control** - Can also scan devices independently

### 3. Data Quality
- **Multiple samples** - Statistical characterization at each point
- **Metadata capture** - All parameters and settings recorded
- **Real-time feedback** - Progress, statistics, and peak detection during runs

### 4. Flexibility
- **Mock device support** - All experiments work without hardware
- **Configurable parameters** - Step sizes, dwell times, sample counts
- **Extensible framework** - Easy to add new experiment types

## Testing

### Quick Test (Mock Devices)
```bash
# Test all experiment types with mock devices (fast, ~2 minutes)
./test_all_experiments.py --all --mock
```

### Full Test (Real Hardware)
```bash
# Requires GNU Radio flowgraph running with XML-RPC on ports 8080, 8081
./test_all_experiments.py --all
```

### Individual Experiment Test
```bash
# Each experiment has fallback to mock devices if GNU Radio unavailable
./experiments/adaptive_tuning.py
./experiments/peak_finding_experiment.py
```

## Data Analysis

All experiments save data to DataBroker. Example analysis:

```python
from databroker import Broker
import matplotlib.pyplot as plt

# Connect to database
db = Broker.named('temp')

# Get recent runs
runs = list(db.search(since='today'))
print(f"Found {len(runs)} runs")

# Get specific run
run = db[-1]  # Most recent

# View metadata
print("Plan:", run.metadata['start']['plan_name'])
print("Purpose:", run.metadata['start']['purpose'])

# Get data as DataFrame
table = run.table()
print(table.head())

# Plot results
table.plot(x='sig_gen_frequency', y='det_value')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Signal Strength')
plt.title(run.metadata['start']['purpose'])
plt.show()

# For 2D grid scans, create heat map
if run.metadata['start']['plan_name'] == 'grid_scan_2d':
    import numpy as np

    # Reshape data
    tx_freq = table['tx_gen_frequency'].values.reshape(15, 15)
    rx_freq = table['rx_gen_frequency'].values.reshape(15, 15)
    signal = table['det_value'].values.reshape(15, 15)

    # Heat map
    plt.pcolormesh(tx_freq/1e6, rx_freq/1e6, signal, shading='auto')
    plt.colorbar(label='Signal Strength')
    plt.xlabel('TX Frequency (MHz)')
    plt.ylabel('RX Frequency (MHz)')
    plt.title('2D Response Map')
    plt.show()
```

## Comparison with Plan Document

| Plan Document (lines 353-449) | Implementation Status |
|-------------------------------|----------------------|
| Basic scan examples | ✅ Implemented in plans.py |
| Adaptive scan example | ✅ Implemented + experiment script |
| Time series example | ✅ Implemented + experiment script |
| Custom plan examples | ✅ Multiple custom plans implemented |
| Multi-device example | ✅ Implemented + experiment script |
| Grid scan mentioned | ✅ Wrapper + full experiment |

## Performance Notes

- **Minimum settling time:** 1.0 second between frequency changes (prevents GNU Radio segfaults)
- **Adaptive scan:** Variable runtime depending on signal complexity (typically 2-5 minutes)
- **Grid scan (15×15):** ~10-15 minutes (225 points × 2.5s per point)
- **Time series (100 points):** 100 seconds at 1Hz sampling
- **Peak finding:** 2-5 minutes depending on number of peaks found

## Next Steps

Phase 4 is complete. Ready to proceed to:

- **Phase 5:** Metadata Strategy (if not already complete)
- **Phase 6:** Live Callbacks (if not already complete)
- **Phase 7:** Data Retrieval & Analysis (if not already complete)
- **Phase 8:** Future Integration - High-Speed Sample Recording

## References

- **Master Plan:** `BLUESKY_COMPREHENSIVE_PLAN.md`
- **Phase 4 Section:** Lines 353-449
- **Related Phases:** Phase 2 (Document Model), Phase 3 (DataBroker)
- **Bluesky Docs:** https://blueskyproject.io/

---

**Implementation Date:** 2025-10-08
**Implemented By:** Claude Code
**Status:** ✅ Complete and Tested
