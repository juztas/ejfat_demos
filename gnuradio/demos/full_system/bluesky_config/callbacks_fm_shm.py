"""
Custom Bluesky Callbacks for FM SHM Beamline

This module provides live feedback callbacks specifically designed for
the FM shared memory beamline, including buffer monitoring, station
detection, and signal quality tracking.

Available Callbacks:
- BufferHealthCallback: Monitor SHM buffer health
- StationFinderCallback: Detect FM stations during sweeps
- SignalQualityCallback: Track signal quality metrics
- FrequencyTrackerCallback: Log frequency changes
- ScanProgressCallback: Enhanced progress reporting
"""

import time
import numpy as np
from collections import deque

from .fm_beamline_config import (
    THRESHOLDS,
    get_station_info,
)


class BufferHealthCallback:
    """
    Monitor shared memory buffer health and alert on issues.

    Tracks buffer fill percentage, overruns, and underruns, alerting
    when thresholds are exceeded.

    Parameters
    ----------
    overrun_threshold : int, optional
        Number of overruns before alerting
    underrun_threshold : int, optional
        Number of underruns before alerting
    fill_high_threshold : float, optional
        Buffer fill % high water mark
    fill_low_threshold : float, optional
        Buffer fill % low water mark
    alert_callback : callable, optional
        Function to call on alert (receives message string)

    Attributes
    ----------
    overrun_count : int
        Total overruns detected
    underrun_count : int
        Total underruns detected
    alerts : list
        List of alert messages

    Examples
    --------
    >>> callback = BufferHealthCallback()
    >>> RE.subscribe(callback)
    >>> RE(fm_band_sweep(beamline))
    """

    def __init__(self,
                 overrun_threshold=None,
                 underrun_threshold=None,
                 fill_high_threshold=None,
                 fill_low_threshold=None,
                 alert_callback=None):

        self.overrun_threshold = overrun_threshold or THRESHOLDS['overrun_threshold']
        self.underrun_threshold = underrun_threshold or THRESHOLDS['underrun_threshold']
        self.fill_high_threshold = fill_high_threshold or THRESHOLDS['buffer_high_watermark']
        self.fill_low_threshold = fill_low_threshold or THRESHOLDS['buffer_low_watermark']
        self.alert_callback = alert_callback

        # State tracking
        self.overrun_count = 0
        self.underrun_count = 0
        self.alerts = []
        self.stats = {
            'max_fill': 0,
            'min_fill': 100,
            'avg_fill': 0,
            'samples': 0,
        }

    def __call__(self, name, doc):
        """Dispatch documents to appropriate handlers."""
        if name == 'start':
            self.start(doc)
        elif name == 'event':
            self.event(doc)
        elif name == 'stop':
            self.stop(doc)

    def start(self, doc):
        """Reset on new run."""
        self.overrun_count = 0
        self.underrun_count = 0
        self.alerts = []
        self.stats = {
            'max_fill': 0,
            'min_fill': 100,
            'avg_fill': 0,
            'samples': 0,
        }
        print("\n[BufferHealth] Monitoring started")

    def event(self, doc):
        """Check each event for buffer issues."""
        data = doc['data']

        # Check for overruns
        if 'fm_shm_buffer_overruns' in data:
            new_overruns = data['fm_shm_buffer_overruns']
            if new_overruns > self.overrun_count:
                delta = new_overruns - self.overrun_count
                msg = f"⚠️  OVERRUN: {delta} buffer overruns detected! (total: {new_overruns})"
                self._alert(msg)
                self.overrun_count = new_overruns

        # Check for underruns
        if 'fm_shm_buffer_underruns' in data:
            new_underruns = data['fm_shm_buffer_underruns']
            if new_underruns > self.underrun_count:
                delta = new_underruns - self.underrun_count
                msg = f"⚠️  UNDERRUN: {delta} buffer underruns detected! (total: {new_underruns})"
                self._alert(msg)
                self.underrun_count = new_underruns

        # Check buffer fill percentage
        if 'fm_shm_buffer_buffer_fill' in data:
            fill = data['fm_shm_buffer_buffer_fill']

            # Update statistics
            self.stats['max_fill'] = max(self.stats['max_fill'], fill)
            self.stats['min_fill'] = min(self.stats['min_fill'], fill)
            self.stats['avg_fill'] = (
                (self.stats['avg_fill'] * self.stats['samples'] + fill) /
                (self.stats['samples'] + 1)
            )
            self.stats['samples'] += 1

            # Check thresholds
            if fill > self.fill_high_threshold:
                msg = f"⚠️  HIGH BUFFER: {fill:.1f}% full (threshold: {self.fill_high_threshold}%)"
                self._alert(msg)
            elif fill < self.fill_low_threshold:
                msg = f"⚠️  LOW BUFFER: {fill:.1f}% full (threshold: {self.fill_low_threshold}%)"
                self._alert(msg)

    def stop(self, doc):
        """Report final statistics."""
        print("\n" + "="*60)
        print("[BufferHealth] Final Statistics")
        print("="*60)
        print(f"Buffer Fill:")
        print(f"  Average: {self.stats['avg_fill']:.1f}%")
        print(f"  Min:     {self.stats['min_fill']:.1f}%")
        print(f"  Max:     {self.stats['max_fill']:.1f}%")
        print(f"Issues:")
        print(f"  Overruns:  {self.overrun_count}")
        print(f"  Underruns: {self.underrun_count}")
        print(f"  Alerts:    {len(self.alerts)}")

        if self.overrun_count == 0 and self.underrun_count == 0:
            print("\n✓ No buffer issues detected!")
        else:
            print("\n⚠️  Buffer issues detected - see alerts above")

        print("="*60 + "\n")

    def _alert(self, message):
        """Issue an alert."""
        if message not in self.alerts:  # Avoid duplicate alerts
            self.alerts.append(message)
            print(f"\n{message}\n")

            if self.alert_callback:
                self.alert_callback(message)


class StationFinderCallback:
    """
    Automatically detect FM stations during frequency sweeps.

    Identifies peaks in RF power that exceed a threshold, indicating
    active FM stations.

    Parameters
    ----------
    power_threshold : float, optional
        Minimum power to consider as station (dBm)
    min_separation : float, optional
        Minimum frequency separation between stations (Hz)
    show_live : bool
        Print station detections as they occur

    Attributes
    ----------
    stations_found : list
        List of detected stations with frequency and power

    Examples
    --------
    >>> callback = StationFinderCallback(power_threshold=-60)
    >>> RE.subscribe(callback)
    >>> RE(fm_band_sweep(beamline))
    >>> print(f"Found {len(callback.stations_found)} stations")
    """

    def __init__(self,
                 power_threshold=None,
                 min_separation=200e3,
                 show_live=True):

        self.power_threshold = power_threshold or THRESHOLDS['station_threshold']
        self.min_separation = min_separation
        self.show_live = show_live

        self.stations_found = []
        self._last_station_freq = None

    def __call__(self, name, doc):
        """Dispatch documents to appropriate handlers."""
        if name == 'start':
            self.start(doc)
        elif name == 'event':
            self.event(doc)
        elif name == 'stop':
            self.stop(doc)

    def start(self, doc):
        """Reset on new run."""
        self.stations_found = []
        self._last_station_freq = None
        print(f"\n[StationFinder] Searching for stations (threshold: {self.power_threshold} dBm)")

    def event(self, doc):
        """Check for strong signals indicating stations."""
        data = doc['data']

        # Get frequency and power
        # Note: In real system, use actual rf_power measurement
        if 'fm_shm_transmitter_frequency' in data:
            freq = data['fm_shm_transmitter_frequency']

            # For now, simulate power measurement
            # TODO: Replace with actual rf_power from transmitter
            power = self._simulate_power(freq)

            # Check if this looks like a station
            if power > self.power_threshold:
                # Check minimum separation from last station
                if (self._last_station_freq is None or
                    abs(freq - self._last_station_freq) > self.min_separation):

                    station_info = {
                        'frequency': freq,
                        'frequency_mhz': freq / 1e6,
                        'power': power,
                        'timestamp': time.time(),
                    }

                    # Check if this matches a known station
                    known = get_station_info(freq, tolerance=100e3)
                    if known:
                        station_info['name'] = known['name']
                        station_info['format'] = known.get('format', 'Unknown')

                    self.stations_found.append(station_info)
                    self._last_station_freq = freq

                    if self.show_live:
                        self._print_station(station_info)

    def stop(self, doc):
        """Report all stations found."""
        print("\n" + "="*60)
        print("[StationFinder] FM Stations Detected")
        print("="*60)

        if not self.stations_found:
            print("No stations found above threshold")
        else:
            print(f"Found {len(self.stations_found)} stations:\n")
            print(f"{'Frequency':>10s}  {'Power':>8s}  {'Station':<20s}")
            print("-" * 60)

            for station in sorted(self.stations_found, key=lambda x: x['frequency']):
                freq_str = f"{station['frequency_mhz']:.1f} MHz"
                power_str = f"{station['power']:.1f} dBm"
                name = station.get('name', 'Unknown')

                print(f"{freq_str:>10s}  {power_str:>8s}  {name:<20s}")

        print("="*60 + "\n")

    def _print_station(self, station_info):
        """Print station detection."""
        freq_mhz = station_info['frequency_mhz']
        power = station_info['power']
        name = station_info.get('name', 'Unknown station')

        print(f"📻 Station: {freq_mhz:6.1f} MHz ({power:+6.1f} dBm) - {name}")

    def _simulate_power(self, freq):
        """
        Simulate RF power measurement.

        TODO: Replace with actual RF power measurement from transmitter.rf_power
        """
        # Simulate some stations at known frequencies
        from .fm_beamline_config import OTTAWA_FM_FREQUENCIES

        # Check if close to known station
        for station_freq in OTTAWA_FM_FREQUENCIES.values():
            if abs(freq - station_freq) < 50e3:
                # Simulate strong signal
                return -40 + np.random.normal(0, 2)

        # Background noise
        return -80 + np.random.normal(0, 5)


class SignalQualityCallback:
    """
    Track signal quality metrics over time.

    Computes statistics on signal strength, buffer health, and
    stability to assess overall system performance.

    Parameters
    ----------
    window_size : int
        Number of samples to use for rolling statistics
    report_interval : int
        Print report every N events (0 = only at end)

    Attributes
    ----------
    signal_history : deque
        Recent signal measurements
    buffer_history : deque
        Recent buffer fill measurements

    Examples
    --------
    >>> callback = SignalQualityCallback(window_size=100)
    >>> RE.subscribe(callback)
    >>> RE(characterize_fm_station(beamline, 106.1e6, duration=60))
    """

    def __init__(self, window_size=100, report_interval=0):
        self.window_size = window_size
        self.report_interval = report_interval

        self.signal_history = deque(maxlen=window_size)
        self.buffer_history = deque(maxlen=window_size)
        self.event_count = 0

        self.stats = {
            'signal_mean': 0,
            'signal_std': 0,
            'buffer_mean': 0,
            'buffer_std': 0,
        }

    def __call__(self, name, doc):
        """Dispatch documents to appropriate handlers."""
        if name == 'start':
            self.start(doc)
        elif name == 'event':
            self.event(doc)
        elif name == 'stop':
            self.stop(doc)

    def start(self, doc):
        """Reset on new run."""
        self.signal_history.clear()
        self.buffer_history.clear()
        self.event_count = 0
        print("\n[SignalQuality] Monitoring started")

    def event(self, doc):
        """Track signal and buffer metrics."""
        data = doc['data']

        # Track RF power (when available)
        if 'fm_shm_transmitter_rf_power' in data:
            power = data['fm_shm_transmitter_rf_power']
            self.signal_history.append(power)

        # Track buffer fill
        if 'fm_shm_buffer_buffer_fill' in data:
            fill = data['fm_shm_buffer_buffer_fill']
            self.buffer_history.append(fill)

        self.event_count += 1

        # Compute rolling statistics
        if len(self.signal_history) > 0:
            self.stats['signal_mean'] = np.mean(self.signal_history)
            self.stats['signal_std'] = np.std(self.signal_history)

        if len(self.buffer_history) > 0:
            self.stats['buffer_mean'] = np.mean(self.buffer_history)
            self.stats['buffer_std'] = np.std(self.buffer_history)

        # Periodic reporting
        if self.report_interval > 0 and self.event_count % self.report_interval == 0:
            self._print_report()

    def stop(self, doc):
        """Report final statistics."""
        print("\n" + "="*60)
        print("[SignalQuality] Final Report")
        print("="*60)
        print(f"Samples: {self.event_count}")

        if len(self.signal_history) > 0:
            print(f"\nSignal Strength:")
            print(f"  Mean:   {self.stats['signal_mean']:.2f} dBm")
            print(f"  StdDev: {self.stats['signal_std']:.2f} dBm")
            print(f"  Range:  {np.min(self.signal_history):.1f} to {np.max(self.signal_history):.1f} dBm")

        if len(self.buffer_history) > 0:
            print(f"\nBuffer Health:")
            print(f"  Mean Fill:   {self.stats['buffer_mean']:.1f}%")
            print(f"  StdDev:      {self.stats['buffer_std']:.1f}%")
            print(f"  Range:       {np.min(self.buffer_history):.1f}% to {np.max(self.buffer_history):.1f}%")

        # Quality assessment
        print(f"\nQuality Assessment:")
        quality = self._assess_quality()
        print(f"  {quality}")

        print("="*60 + "\n")

    def _print_report(self):
        """Print periodic report."""
        print(f"\n[SignalQuality] Sample {self.event_count}:")
        print(f"  Signal: {self.stats['signal_mean']:.1f} ± {self.stats['signal_std']:.1f} dBm")
        print(f"  Buffer: {self.stats['buffer_mean']:.1f} ± {self.stats['buffer_std']:.1f}%")

    def _assess_quality(self):
        """Assess overall quality."""
        issues = []

        if self.stats['signal_std'] > 10:
            issues.append("high signal variability")

        if self.stats['buffer_std'] > 20:
            issues.append("unstable buffer fill")

        if not issues:
            return "✓ Excellent - stable signal and buffer"
        else:
            return "⚠️  Issues: " + ", ".join(issues)


class FrequencyTrackerCallback:
    """
    Log frequency changes during experiment.

    Tracks all frequency changes and reports transition statistics.

    Parameters
    ----------
    log_file : str, optional
        Path to log file (None = no file logging)
    show_transitions : bool
        Print frequency changes as they occur

    Examples
    --------
    >>> callback = FrequencyTrackerCallback(show_transitions=True)
    >>> RE.subscribe(callback)
    >>> RE(fm_band_sweep(beamline))
    """

    def __init__(self, log_file=None, show_transitions=False):
        self.log_file = log_file
        self.show_transitions = show_transitions

        self.frequency_log = []
        self.last_frequency = None
        self.transition_count = 0

    def __call__(self, name, doc):
        """Dispatch documents to appropriate handlers."""
        if name == 'start':
            self.start(doc)
        elif name == 'event':
            self.event(doc)
        elif name == 'stop':
            self.stop(doc)

    def start(self, doc):
        """Reset on new run."""
        self.frequency_log = []
        self.last_frequency = None
        self.transition_count = 0

        if self.log_file:
            with open(self.log_file, 'w') as f:
                f.write("# Frequency Log\n")
                f.write("# timestamp,frequency_hz,frequency_mhz\n")

        print("\n[FrequencyTracker] Tracking started")

    def event(self, doc):
        """Track frequency changes."""
        data = doc['data']

        if 'fm_shm_transmitter_frequency' in data:
            freq = data['fm_shm_transmitter_frequency']
            timestamp = doc['time']

            # Check if frequency changed
            if self.last_frequency is not None and abs(freq - self.last_frequency) > 1e3:
                self.transition_count += 1

                if self.show_transitions:
                    print(f"  Frequency: {self.last_frequency/1e6:.1f} → {freq/1e6:.1f} MHz")

            self.last_frequency = freq

            # Log
            self.frequency_log.append({
                'timestamp': timestamp,
                'frequency': freq,
            })

            if self.log_file:
                with open(self.log_file, 'a') as f:
                    f.write(f"{timestamp},{freq},{freq/1e6}\n")

    def stop(self, doc):
        """Report statistics."""
        print("\n" + "="*60)
        print("[FrequencyTracker] Summary")
        print("="*60)
        print(f"Total samples:      {len(self.frequency_log)}")
        print(f"Frequency changes:  {self.transition_count}")

        if self.frequency_log:
            freqs = [x['frequency'] for x in self.frequency_log]
            print(f"Frequency range:    {min(freqs)/1e6:.1f} - {max(freqs)/1e6:.1f} MHz")

        if self.log_file:
            print(f"Log written to:     {self.log_file}")

        print("="*60 + "\n")


class ScanProgressCallback:
    """
    Enhanced progress reporting for scans.

    Provides detailed progress information including ETA,
    scan rate, and completion percentage.

    Parameters
    ----------
    expected_points : int, optional
        Expected number of data points (for ETA calculation)
    update_interval : int
        Print update every N events

    Examples
    --------
    >>> callback = ScanProgressCallback(expected_points=200)
    >>> RE.subscribe(callback)
    >>> RE(fm_band_sweep(beamline, num=200))
    """

    def __init__(self, expected_points=None, update_interval=10):
        self.expected_points = expected_points
        self.update_interval = update_interval

        self.start_time = None
        self.event_count = 0

    def __call__(self, name, doc):
        """Dispatch documents to appropriate handlers."""
        if name == 'start':
            self.start(doc)
        elif name == 'event':
            self.event(doc)
        elif name == 'stop':
            self.stop(doc)

    def start(self, doc):
        """Initialize on run start."""
        self.start_time = time.time()
        self.event_count = 0

        # Try to extract expected points from metadata
        if self.expected_points is None:
            if 'num_points' in doc:
                self.expected_points = doc['num_points']
            elif 'num_samples' in doc:
                self.expected_points = doc['num_samples']

        print("\n[Progress] Scan started")
        if self.expected_points:
            print(f"  Expected points: {self.expected_points}")

    def event(self, doc):
        """Update progress."""
        self.event_count += 1

        if self.event_count % self.update_interval == 0:
            elapsed = time.time() - self.start_time
            rate = self.event_count / elapsed

            msg = f"[Progress] Point {self.event_count}"

            if self.expected_points:
                progress = (self.event_count / self.expected_points) * 100
                remaining = self.expected_points - self.event_count
                eta = remaining / rate if rate > 0 else 0

                msg += f" / {self.expected_points} ({progress:.0f}%)"
                msg += f" - ETA: {eta:.0f}s"

            msg += f" - Rate: {rate:.1f} pts/s"
            print(msg)

    def stop(self, doc):
        """Report final statistics."""
        elapsed = time.time() - self.start_time
        rate = self.event_count / elapsed if elapsed > 0 else 0

        print(f"\n[Progress] Scan complete!")
        print(f"  Points:  {self.event_count}")
        print(f"  Time:    {elapsed:.1f}s")
        print(f"  Rate:    {rate:.1f} pts/s\n")


# Export all callbacks
__all__ = [
    'BufferHealthCallback',
    'StationFinderCallback',
    'SignalQualityCallback',
    'FrequencyTrackerCallback',
    'ScanProgressCallback',
]
