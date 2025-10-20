# FM Shared Memory Beamline Integration Plan

**Created:** 2025-10-08
**Purpose:** Integrate FM transmit/receive GNU Radio flowgraphs with shared memory into the Bluesky framework as a new "beamline"

## Executive Summary

This plan outlines the integration of the FM transmitter and receiver GNU Radio flowgraphs (using EJFAT shared memory blocks) into the existing Bluesky experiment framework. We will treat this as a new **FM SHM Beamline** - a complete transmit-receive system that can be controlled, monitored, and analyzed through Bluesky.

## Architecture Analysis

### Current FM SHM System

#### FM Transmitter (SDR → Shared Memory)
**File:** `../fm/fm_transmitter_shm.py`

**Signal Chain:**
```
RTL-SDR (osmosdr_source)
  → Low Pass Filter (75kHz)
  → Stream to Vector (vlen=8192)
  → EJFAT SHM Sink ("fm_stream")
```

**Key Parameters:**
- Sample rate: 2.4 MHz
- Frequency range: 88-108 MHz (FM band)
- Vector length: 8192 samples
- SHM name: `"fm_stream"`
- SHM capacity: 1024 entries
- SHM entry size: 65552 bytes
- XML-RPC: Port 8080
- Controllable: `freq` (frequency slider)

**Visualization:**
- Waterfall sink
- FFT frequency sink

#### FM Receiver (Shared Memory → Audio)
**File:** `../fm/fm_receiver_shm.py`

**Signal Chain:**
```
EJFAT SHM Source ("fm_stream")
  → Vector to Stream
  → Rational Resampler (1:5 decimation)
  → WBFM Receiver
  → Audio Resampler
  → Volume Control
  → Audio Sink
```

**Key Parameters:**
- Sample rate: 2.4 MHz
- Audio rate: 48 kHz
- Vector length: 8192 samples
- SHM name: `"fm_stream"` (same as transmitter)
- Controllable: `volume` (volume slider)

**Visualization:**
- Waterfall sink
- FFT frequency sink

### Integration Pattern

This is a **producer-consumer** architecture via shared memory:
- **Producer (TX):** Captures RF → writes to SHM
- **Consumer (RX):** Reads from SHM → outputs audio
- **Communication:** POSIX shared memory ring buffer

## Bluesky Integration Strategy

### Beamline Concept

In Bluesky terminology, a "beamline" represents a complete experimental setup. For the FM SHM system:

**FM SHM Beamline Components:**
1. **Signal Source Device** - FM Transmitter (controllable frequency)
2. **Signal Receiver Device** - FM Receiver (controllable volume)
3. **Data Transport** - Shared memory buffer
4. **Measurement Signals** - Power, SNR, buffer health

### Device Hierarchy

```
FM_SHM_Beamline (Ophyd Device)
├── transmitter (FMTransmitterSHM)
│   ├── frequency (Signal) - tunable 88-108 MHz
│   ├── sample_rate (Signal) - read-only
│   ├── shm_name (Signal) - read-only
│   └── rf_power (Signal) - measured from FFT
│
├── receiver (FMReceiverSHM)
│   ├── volume (Signal) - tunable 0-10
│   ├── audio_rate (Signal) - read-only
│   ├── shm_name (Signal) - read-only
│   └── audio_power (Signal) - measured output
│
└── shm_buffer (SHMMonitor)
    ├── buffer_fill (Signal) - % full
    ├── data_rate (Signal) - samples/sec
    ├── overruns (Signal) - buffer overrun count
    └── underruns (Signal) - buffer underrun count
```

## Implementation Plan

### Phase 1: Core Device Wrappers

**File:** `bluesky_config/devices_fm_shm.py`

Create Ophyd device wrappers for the FM flowgraphs:

#### 1.1 FMTransmitterSHM Device

```python
class FMTransmitterSHM(Device):
    """
    Ophyd device for FM Transmitter with SHM output.

    Controls the fm_transmitter_shm.py flowgraph via:
    - XML-RPC for frequency control
    - Process management for start/stop
    - Signal monitoring via GNU Radio message passing
    """

    frequency = Cpt(Signal, kind='hinted')  # Tunable 88-108 MHz
    sample_rate = Cpt(Signal, value=2.4e6, kind='config')
    shm_name = Cpt(Signal, value='fm_stream', kind='config')
    rf_power = Cpt(Signal, kind='hinted')  # Measured signal strength

    def __init__(self, *args, flowgraph_path=None, **kwargs):
        """
        Parameters
        ----------
        flowgraph_path : str
            Path to fm_transmitter_shm.py
        """
        self._flowgraph_path = flowgraph_path
        self._process = None
        self._rpc_client = None
        super().__init__(*args, **kwargs)

    def start_flowgraph(self):
        """Launch the GNU Radio flowgraph"""
        # subprocess.Popen([sys.executable, self._flowgraph_path])
        # Connect to XML-RPC server
        pass

    def stop_flowgraph(self):
        """Stop the GNU Radio flowgraph"""
        # self._process.terminate()
        pass
```

#### 1.2 FMReceiverSHM Device

```python
class FMReceiverSHM(Device):
    """
    Ophyd device for FM Receiver from SHM input.

    Controls the fm_receiver_shm.py flowgraph.
    """

    volume = Cpt(Signal, kind='hinted')  # Tunable 0-10
    audio_rate = Cpt(Signal, value=48000, kind='config')
    shm_name = Cpt(Signal, value='fm_stream', kind='config')
    audio_power = Cpt(Signal, kind='hinted')  # Measured audio level
```

#### 1.3 SHMMonitor Device

```python
class SHMMonitor(Device):
    """
    Monitor the shared memory buffer health.

    Uses the ejfat_shm Python API to read buffer statistics.
    """

    buffer_fill = Cpt(Signal, kind='hinted')  # Percentage full
    data_rate = Cpt(Signal, kind='hinted')    # Samples per second
    overruns = Cpt(Signal, kind='normal')     # Buffer overruns
    underruns = Cpt(Signal, kind='normal')    # Buffer underruns

    def trigger(self):
        """Read current buffer statistics"""
        # Use ejfat_shm API to get stats
        pass
```

#### 1.4 Composite Beamline Device

```python
class FMSHMBeamline(Device):
    """
    Complete FM SHM beamline - transmitter, receiver, and buffer.
    """

    transmitter = Cpt(FMTransmitterSHM, name='fm_tx')
    receiver = Cpt(FMReceiverSHM, name='fm_rx')
    buffer = Cpt(SHMMonitor, name='shm_buffer')

    def startup(self):
        """Start both TX and RX flowgraphs"""
        self.transmitter.start_flowgraph()
        time.sleep(2)  # Let TX fill buffer
        self.receiver.start_flowgraph()

    def shutdown(self):
        """Stop both flowgraphs"""
        self.receiver.stop_flowgraph()
        self.transmitter.stop_flowgraph()
```

### Phase 2: FM Beamline Configuration

**File:** `bluesky_config/fm_beamline_config.py`

Configuration specific to the FM SHM beamline:

```python
"""
FM SHM Beamline Configuration
"""

from pathlib import Path

# Paths to flowgraph scripts
FM_DIR = Path(__file__).parent.parent.parent / "fm"
FM_TX_FLOWGRAPH = FM_DIR / "fm_transmitter_shm.py"
FM_RX_FLOWGRAPH = FM_DIR / "fm_receiver_shm.py"

# FM Band Configuration
FM_BAND = {
    'min_freq': 88.0e6,
    'max_freq': 108.0e6,
    'step_freq': 100e3,  # 100 kHz steps
}

# Ottawa FM Stations (for testing)
OTTAWA_FM_STATIONS = {
    'CBC Radio One': 91.5e6,
    'CHEZ 106': 106.1e6,
    'Hot 89.9': 89.9e6,
    'The Bear 106.9': 106.9e6,
    'BOB FM': 93.9e6,
    'DAWG FM': 101.9e6,
}

# SHM Configuration
SHM_CONFIG = {
    'name': 'fm_stream',
    'capacity': 1024,
    'entry_size': 65552,
    'vlen': 8192,
}

# Signal Processing
SIGNAL_CONFIG = {
    'sample_rate': 2.4e6,
    'audio_rate': 48000,
    'filter_cutoff': 75e3,
    'filter_transition': 25e3,
}
```

### Phase 3: Custom Scan Plans

**File:** `bluesky_config/plans_fm_shm.py`

FM-specific scan plans:

#### 3.1 FM Band Sweep

```python
def fm_band_sweep(beamline, start=88e6, stop=108e6, num=200,
                  dwell_time=0.5):
    """
    Sweep across FM band and measure signal strength.

    Parameters
    ----------
    beamline : FMSHMBeamline
        The FM beamline device
    start : float
        Start frequency (Hz)
    stop : float
        Stop frequency (Hz)
    num : int
        Number of points
    dwell_time : float
        Time to dwell at each frequency (seconds)
    """

    @run_decorator(md={
        'plan_name': 'fm_band_sweep',
        'beamline': 'fm_shm',
        'start_freq': start,
        'stop_freq': stop,
        'num_points': num,
    })
    def inner():
        import numpy as np
        frequencies = np.linspace(start, stop, num)

        for freq in frequencies:
            # Set transmitter frequency
            yield from bps.abs_set(beamline.transmitter.frequency,
                                   freq, wait=True)

            # Wait for settling
            yield from bps.sleep(dwell_time)

            # Measure signal strength and buffer health
            yield from bps.trigger_and_read([
                beamline.transmitter,
                beamline.receiver,
                beamline.buffer,
            ])

    yield from inner()
```

#### 3.2 Station Characterization

```python
def characterize_fm_station(beamline, frequency, duration=60,
                            sample_interval=1.0):
    """
    Monitor a specific FM station over time.

    Measures signal quality, buffer health, and audio power.
    """

    @run_decorator(md={
        'plan_name': 'fm_station_characterization',
        'station_frequency': frequency,
        'duration': duration,
    })
    def inner():
        # Tune to station
        yield from bps.abs_set(beamline.transmitter.frequency,
                               frequency, wait=True)
        yield from bps.sleep(2.0)  # Settling time

        # Time-series monitoring
        num_samples = int(duration / sample_interval)
        for i in range(num_samples):
            yield from bps.trigger_and_read([
                beamline.transmitter,
                beamline.receiver,
                beamline.buffer,
            ])
            yield from bps.sleep(sample_interval)

    yield from inner()
```

#### 3.3 SHM Performance Test

```python
def shm_performance_test(beamline, test_duration=300):
    """
    Test shared memory performance under load.

    Monitors buffer statistics while sweeping frequencies.
    """

    @run_decorator(md={
        'plan_name': 'shm_performance_test',
        'test_duration': test_duration,
    })
    def inner():
        import numpy as np
        import time

        start_time = time.time()
        freq_range = np.linspace(88e6, 108e6, 100)

        while (time.time() - start_time) < test_duration:
            for freq in freq_range:
                yield from bps.abs_set(beamline.transmitter.frequency,
                                       freq, wait=True)
                yield from bps.trigger_and_read([beamline.buffer])
                yield from bps.sleep(0.1)

    yield from inner()
```

### Phase 4: Custom Callbacks

**File:** `bluesky_config/callbacks_fm_shm.py`

FM-specific live callbacks:

#### 4.1 Buffer Health Monitor

```python
class BufferHealthCallback:
    """
    Monitor SHM buffer health and alert on issues.
    """

    def __init__(self, overrun_threshold=10, underrun_threshold=10):
        self.overrun_threshold = overrun_threshold
        self.underrun_threshold = underrun_threshold
        self.overrun_count = 0
        self.underrun_count = 0

    def event(self, doc):
        """Check each event for buffer issues"""
        data = doc['data']

        # Check for overruns
        if 'shm_buffer_overruns' in data:
            new_overruns = data['shm_buffer_overruns']
            if new_overruns > self.overrun_count:
                delta = new_overruns - self.overrun_count
                print(f"⚠️  WARNING: {delta} buffer OVERRUNS detected!")
                self.overrun_count = new_overruns

        # Check for underruns
        if 'shm_buffer_underruns' in data:
            new_underruns = data['shm_buffer_underruns']
            if new_underruns > self.underrun_count:
                delta = new_underruns - self.underrun_count
                print(f"⚠️  WARNING: {delta} buffer UNDERRUNS detected!")
                self.underrun_count = new_underruns

        # Check buffer fill percentage
        if 'shm_buffer_buffer_fill' in data:
            fill = data['shm_buffer_buffer_fill']
            if fill > 90:
                print(f"⚠️  WARNING: Buffer {fill:.1f}% full!")
            elif fill < 10:
                print(f"⚠️  WARNING: Buffer only {fill:.1f}% full!")

    def start(self, doc):
        """Reset counters on new run"""
        self.overrun_count = 0
        self.underrun_count = 0
```

#### 4.2 Station Finder Callback

```python
class StationFinderCallback:
    """
    Automatically detect FM stations during band sweep.
    """

    def __init__(self, power_threshold=-60):
        self.power_threshold = power_threshold
        self.stations_found = []

    def event(self, doc):
        """Check for strong signals"""
        data = doc['data']

        if 'fm_tx_frequency' in data and 'fm_tx_rf_power' in data:
            freq = data['fm_tx_frequency']
            power = data['fm_tx_rf_power']

            if power > self.power_threshold:
                self.stations_found.append({
                    'frequency': freq,
                    'power': power,
                    'frequency_mhz': freq / 1e6,
                })
                print(f"📻 Station found: {freq/1e6:.1f} MHz "
                      f"(power: {power:.1f} dBm)")

    def stop(self, doc):
        """Report all stations found"""
        print(f"\n{'='*60}")
        print(f"Found {len(self.stations_found)} FM stations:")
        print(f"{'='*60}")
        for station in self.stations_found:
            print(f"  {station['frequency_mhz']:>6.1f} MHz  "
                  f"({station['power']:>6.1f} dBm)")
        print(f"{'='*60}\n")
```

### Phase 5: Experiment Scripts

**File:** `experiments/fm_band_survey.py`

```python
#!/usr/bin/env python3
"""
FM Band Survey Experiment

Sweeps the entire FM band and identifies active stations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from databroker import Broker

from bluesky_config.devices_fm_shm import FMSHMBeamline
from bluesky_config.plans_fm_shm import fm_band_sweep
from bluesky_config.callbacks_fm_shm import (
    BufferHealthCallback,
    StationFinderCallback,
)
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run FM band survey experiment."""

    # Setup RunEngine
    RE = RunEngine({})
    db = Broker.named('temp')
    RE.subscribe(db.insert)

    # Setup callbacks
    bec = BestEffortCallback()
    buffer_health = BufferHealthCallback()
    station_finder = StationFinderCallback(power_threshold=-60)

    RE.subscribe(bec)
    RE.subscribe(buffer_health)
    RE.subscribe(station_finder)

    # Create FM beamline
    print("Initializing FM SHM Beamline...")
    beamline = FMSHMBeamline(name='fm_shm')
    beamline.startup()

    try:
        # Create metadata
        md = create_experiment_metadata(
            experiment_id='FM-SURVEY-001',
            purpose='Survey Ottawa FM band for active stations',
            beamline='fm_shm',
        )

        # Run sweep
        print("\nStarting FM band sweep (88-108 MHz)...")
        RE(fm_band_sweep(beamline,
                         start=88e6,
                         stop=108e6,
                         num=200,
                         dwell_time=0.5),
           **md)

        print("\nExperiment complete!")

    finally:
        # Cleanup
        print("Shutting down beamline...")
        beamline.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**File:** `experiments/fm_station_monitor.py`

```python
#!/usr/bin/env python3
"""
FM Station Monitoring Experiment

Monitors a specific FM station over time to characterize
signal quality and shared memory performance.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from databroker import Broker

from bluesky_config.devices_fm_shm import FMSHMBeamline
from bluesky_config.plans_fm_shm import characterize_fm_station
from bluesky_config.callbacks_fm_shm import BufferHealthCallback
from bluesky_config.metadata import create_experiment_metadata
from bluesky_config.fm_beamline_config import OTTAWA_FM_STATIONS


def main():
    """Run FM station monitoring experiment."""

    # Setup
    RE = RunEngine({})
    db = Broker.named('temp')
    RE.subscribe(db.insert)

    bec = BestEffortCallback()
    buffer_health = BufferHealthCallback()
    RE.subscribe(bec)
    RE.subscribe(buffer_health)

    # Create beamline
    beamline = FMSHMBeamline(name='fm_shm')
    beamline.startup()

    try:
        # Monitor CHEZ 106.1
        station_freq = OTTAWA_FM_STATIONS['CHEZ 106']

        md = create_experiment_metadata(
            experiment_id='FM-MONITOR-001',
            purpose='Monitor CHEZ 106.1 FM signal quality',
            station_name='CHEZ 106',
            station_frequency=station_freq,
        )

        print(f"\nMonitoring {station_freq/1e6:.1f} MHz for 60 seconds...")
        RE(characterize_fm_station(beamline,
                                   station_freq,
                                   duration=60,
                                   sample_interval=1.0),
           **md)

        print("\nMonitoring complete!")

    finally:
        beamline.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Phase 6: Analysis Tools

**File:** `analysis/fm_analysis.py`

```python
"""
FM-specific analysis tools.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks


def analyze_band_sweep(run):
    """
    Analyze FM band sweep to identify stations.

    Parameters
    ----------
    run : BlueskyRun
        A run from an fm_band_sweep plan

    Returns
    -------
    dict
        Analysis results including detected stations
    """
    table = run.table()

    frequencies = table['fm_tx_frequency'].values
    powers = table['fm_tx_rf_power'].values

    # Find peaks (stations)
    peaks, properties = find_peaks(powers,
                                   prominence=10,
                                   distance=10)

    stations = []
    for peak_idx in peaks:
        stations.append({
            'frequency': frequencies[peak_idx],
            'frequency_mhz': frequencies[peak_idx] / 1e6,
            'power': powers[peak_idx],
        })

    return {
        'num_stations': len(stations),
        'stations': stations,
        'frequencies': frequencies,
        'powers': powers,
        'peak_indices': peaks,
    }


def plot_fm_spectrum(run, save_path=None):
    """
    Plot FM spectrum from band sweep.
    """
    table = run.table()

    frequencies = table['fm_tx_frequency'].values / 1e6  # MHz
    powers = table['fm_tx_rf_power'].values

    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(frequencies, powers, 'b-', linewidth=1.5, label='RF Power')

    # Find and mark stations
    analysis = analyze_band_sweep(run)
    for station in analysis['stations']:
        ax.axvline(station['frequency_mhz'],
                   color='r', alpha=0.3, linestyle='--')
        ax.text(station['frequency_mhz'], station['power'] + 2,
                f"{station['frequency_mhz']:.1f}",
                rotation=90, fontsize=8)

    ax.set_xlabel('Frequency (MHz)', fontsize=12)
    ax.set_ylabel('RF Power (dBm)', fontsize=12)
    ax.set_title('FM Band Spectrum (Ottawa)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    return fig, ax


def analyze_buffer_health(run):
    """
    Analyze shared memory buffer performance.
    """
    table = run.table()

    stats = {
        'mean_fill': table['shm_buffer_buffer_fill'].mean(),
        'max_fill': table['shm_buffer_buffer_fill'].max(),
        'min_fill': table['shm_buffer_buffer_fill'].min(),
        'total_overruns': table['shm_buffer_overruns'].max(),
        'total_underruns': table['shm_buffer_underruns'].max(),
        'mean_data_rate': table['shm_buffer_data_rate'].mean(),
    }

    return stats
```

### Phase 7: Documentation

**File:** `FM_SHM_BEAMLINE_README.md`

Create comprehensive documentation including:
- Architecture overview
- Device descriptions
- Available plans
- Example workflows
- Troubleshooting guide

## Implementation Timeline

### Week 1: Core Infrastructure
- [ ] Create `devices_fm_shm.py` with basic device wrappers
- [ ] Implement process management for flowgraphs
- [ ] Test XML-RPC communication
- [ ] Create SHM monitoring using ejfat_shm API

### Week 2: Plans and Callbacks
- [ ] Implement `plans_fm_shm.py` with sweep and characterization plans
- [ ] Create `callbacks_fm_shm.py` with buffer monitoring
- [ ] Test basic scans with mock data

### Week 3: Experiments and Analysis
- [ ] Create FM band survey experiment
- [ ] Create station monitoring experiment
- [ ] Implement FM-specific analysis tools
- [ ] Test end-to-end workflow

### Week 4: Polish and Documentation
- [ ] Write comprehensive documentation
- [ ] Create example notebooks
- [ ] Performance testing
- [ ] Integration testing with real SDR

## Key Benefits

1. **Unified Control** - Single interface for TX and RX
2. **Automated Monitoring** - Buffer health tracking
3. **Rich Metadata** - All parameters captured
4. **Reproducibility** - Experiments fully documented
5. **Analysis Ready** - Data in standard formats
6. **Extensibility** - Easy to add new measurements

## Future Enhancements

1. **Multi-Station Tracking** - Monitor multiple frequencies
2. **Adaptive Tuning** - Auto-tune to strongest station
3. **Quality Metrics** - SNR, BER, audio quality
4. **Network Integration** - E2SAR data distribution
5. **Real-time Dashboard** - Web-based monitoring
6. **Machine Learning** - Anomaly detection, classification

## Related Files

- Current FM flowgraphs: `../fm/fm_transmitter_shm.py`, `../fm/fm_receiver_shm.py`
- Existing Bluesky framework: `./bluesky_config/`, `./experiments/`
- Configuration: `./config.py`
- Main README: `./README.md`

## References

- [Bluesky Documentation](https://blueskyproject.io/)
- [Ophyd Devices](https://blueskyproject.io/ophyd/)
- [GNU Radio](https://www.gnuradio.org/)
- [EJFAT Project](https://github.com/JeffersonLab/E2SAR)
