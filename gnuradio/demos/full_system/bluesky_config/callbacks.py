"""
Custom callbacks for live data processing and feedback.

This module provides callbacks that process Bluesky documents in real-time
during experiment runs.
"""

import json
from pathlib import Path
import time


class PeakDetectorCallback:
    """
    Detect and report peaks during a scan.

    This callback monitors a signal and reports when it exceeds a threshold
    or when a new peak is detected.
    """

    def __init__(self, signal_name, motor_name=None, threshold=None):
        """
        Initialize peak detector.

        Parameters
        ----------
        signal_name : str
            Name of the signal to monitor for peaks
        motor_name : str, optional
            Name of the motor/position signal (auto-detected if None)
        threshold : float, optional
            Alert threshold - print warning when signal exceeds this value
        """
        self.signal_name = signal_name
        self.motor_name = motor_name
        self.threshold = threshold
        self.peak_value = None
        self.peak_position = None
        self._motor_name_detected = None

    def start(self, doc):
        """Reset on new run."""
        self.peak_value = None
        self.peak_position = None
        self._motor_name_detected = None
        print(f"\n🔍 Peak Detector: Monitoring '{self.signal_name}'")
        if self.threshold:
            print(f"   Alert threshold: {self.threshold}")

    def descriptor(self, doc):
        """Auto-detect motor name from descriptor if not specified."""
        if self.motor_name is None:
            # Find first key that's not our signal
            for key in doc['data_keys']:
                if key != self.signal_name:
                    self._motor_name_detected = key
                    print(f"   Position signal: '{key}' (auto-detected)")
                    break

    def event(self, doc):
        """Check each event for peaks."""
        value = doc['data'][self.signal_name]

        # Track peak
        if self.peak_value is None or value > self.peak_value:
            self.peak_value = value

            # Get position
            motor_key = self.motor_name or self._motor_name_detected
            if motor_key and motor_key in doc['data']:
                self.peak_position = doc['data'][motor_key]

            # Threshold alert
            if self.threshold and value > self.threshold:
                print(f"   🔔 ALERT: {self.signal_name} = {value:.4f} "
                      f"exceeds threshold {self.threshold} "
                      f"at {motor_key} = {self.peak_position:.4e}")

    def stop(self, doc):
        """Report final peak."""
        if self.peak_value is not None:
            motor_key = self.motor_name or self._motor_name_detected
            print(f"\n   📊 Peak Summary:")
            print(f"      Peak value: {self.peak_value:.4f}")
            if self.peak_position is not None:
                print(f"      Peak position ({motor_key}): {self.peak_position:.4e}")
        print()

    def __call__(self, name, doc):
        """Dispatch to appropriate method based on document name."""
        if hasattr(self, name):
            getattr(self, name)(doc)


class DocumentLogger:
    """
    Save all Bluesky documents to JSON files.

    Useful for debugging, archiving, or custom post-processing.
    """

    def __init__(self, output_dir='data/documents'):
        """
        Initialize document logger.

        Parameters
        ----------
        output_dir : str or Path
            Directory to save document JSON files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_uid = None
        self.run_file = None

    def __call__(self, name, doc):
        """Save each document to file."""
        if name == 'start':
            self.run_uid = doc['uid']
            self.run_file = self.output_dir / f"{self.run_uid[:8]}_documents.jsonl"
            print(f"📝 Logging documents to: {self.run_file.name}")

        if self.run_file:
            # Write as JSON Lines format (one JSON per line)
            with open(self.run_file, 'a') as f:
                json.dump({name: doc}, f, default=str)
                f.write('\n')

        if name == 'stop':
            print(f"   Saved {name} document")


class StatisticsCallback:
    """
    Compute running statistics during a scan.

    Calculates mean, std, min, max for specified signals.
    """

    def __init__(self, signal_names):
        """
        Initialize statistics calculator.

        Parameters
        ----------
        signal_names : list of str
            Names of signals to compute statistics for
        """
        self.signal_names = signal_names
        self.data = {name: [] for name in signal_names}

    def start(self, doc):
        """Reset statistics on new run."""
        self.data = {name: [] for name in self.signal_names}
        print(f"\n📈 Computing statistics for: {', '.join(self.signal_names)}")

    def event(self, doc):
        """Accumulate data from events."""
        for name in self.signal_names:
            if name in doc['data']:
                self.data[name].append(doc['data'][name])

    def stop(self, doc):
        """Report statistics at end of run."""
        import numpy as np

        print(f"\n   📊 Statistics Summary:")
        for name, values in self.data.items():
            if values:
                arr = np.array(values)
                print(f"      {name}:")
                print(f"         Mean:   {np.mean(arr):.4f}")
                print(f"         Std:    {np.std(arr):.4f}")
                print(f"         Min:    {np.min(arr):.4f}")
                print(f"         Max:    {np.max(arr):.4f}")
                print(f"         Median: {np.median(arr):.4f}")
        print()

    def __call__(self, name, doc):
        """Dispatch to appropriate method based on document name."""
        if hasattr(self, name):
            getattr(self, name)(doc)


class ProgressCallback:
    """
    Display scan progress with estimated time remaining.
    """

    def __init__(self):
        """Initialize progress tracker."""
        self.start_time = None
        self.expected_events = None
        self.event_count = 0

    def start(self, doc):
        """Record start time."""
        self.start_time = time.time()
        self.event_count = 0

        # Try to estimate number of events from plan args
        if 'num_points' in doc.get('plan_args', {}):
            self.expected_events = doc['plan_args']['num_points']
        else:
            self.expected_events = None

        print(f"\n⏱️  Scan started: {doc.get('plan_name', 'unknown')}")

    def event(self, doc):
        """Update progress."""
        self.event_count += 1

        if self.expected_events:
            # Show progress bar
            elapsed = time.time() - self.start_time
            progress = self.event_count / self.expected_events
            remaining = (elapsed / progress - elapsed) if progress > 0 else 0

            bar_length = 30
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)

            print(f"\r   Progress: [{bar}] {progress*100:.1f}% "
                  f"({self.event_count}/{self.expected_events}) "
                  f"ETA: {remaining:.1f}s", end='', flush=True)
        else:
            # Just show count
            print(f"\r   Events: {self.event_count}", end='', flush=True)

    def stop(self, doc):
        """Show completion."""
        elapsed = time.time() - self.start_time
        print(f"\n   ✅ Complete in {elapsed:.2f}s ({self.event_count} events)\n")

    def __call__(self, name, doc):
        """Dispatch to appropriate method based on document name."""
        if hasattr(self, name):
            getattr(self, name)(doc)


class AlertCallback:
    """
    Send alerts when signals exceed limits.

    Can be extended to send emails, Slack messages, etc.
    """

    def __init__(self, limits):
        """
        Initialize alert system.

        Parameters
        ----------
        limits : dict
            Dictionary of signal_name: (min, max) tuples
        """
        self.limits = limits
        self.alerts = []

    def start(self, doc):
        """Reset alerts."""
        self.alerts = []

    def event(self, doc):
        """Check for limit violations."""
        for signal_name, (min_val, max_val) in self.limits.items():
            if signal_name in doc['data']:
                value = doc['data'][signal_name]

                if value < min_val:
                    msg = f"⚠️  {signal_name} = {value:.4f} below minimum {min_val}"
                    print(msg)
                    self.alerts.append(msg)

                if value > max_val:
                    msg = f"⚠️  {signal_name} = {value:.4f} above maximum {max_val}"
                    print(msg)
                    self.alerts.append(msg)

    def stop(self, doc):
        """Report alert summary."""
        if self.alerts:
            print(f"\n   🚨 {len(self.alerts)} alerts during scan:")
            for alert in self.alerts:
                print(f"      {alert}")
        print()

    def __call__(self, name, doc):
        """Dispatch to appropriate method based on document name."""
        if hasattr(self, name):
            getattr(self, name)(doc)


class LiveExportCallback:
    """
    Export data to CSV in real-time during scan.

    Useful for monitoring with external tools during long scans.
    """

    def __init__(self, filename='data/live_export.csv'):
        """
        Initialize live exporter.

        Parameters
        ----------
        filename : str or Path
            Output CSV filename
        """
        self.filename = Path(filename)
        self.file = None
        self.headers_written = False
        self.headers = []

    def start(self, doc):
        """Open CSV file."""
        self.file = open(self.filename, 'w')
        self.headers_written = False
        self.headers = []
        print(f"📤 Live export to: {self.filename}")

    def descriptor(self, doc):
        """Extract column headers from descriptor."""
        self.headers = ['time'] + sorted(doc['data_keys'].keys())

    def event(self, doc):
        """Write event to CSV."""
        if not self.headers_written:
            # Write headers
            self.file.write(','.join(self.headers) + '\n')
            self.headers_written = True

        # Write data
        row = [str(doc['time'])]
        for key in self.headers[1:]:  # Skip 'time'
            row.append(str(doc['data'].get(key, '')))

        self.file.write(','.join(row) + '\n')
        self.file.flush()  # Ensure it's written immediately

    def stop(self, doc):
        """Close CSV file."""
        if self.file:
            self.file.close()
            print(f"   ✅ Export complete: {self.filename}")

    def __call__(self, name, doc):
        """Dispatch to appropriate method based on document name."""
        if hasattr(self, name):
            getattr(self, name)(doc)
