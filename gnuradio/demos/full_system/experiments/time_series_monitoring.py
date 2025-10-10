#!/usr/bin/env python3
"""
Time Series Monitoring Experiment

This experiment monitors signal quality over time at a fixed frequency
to detect variations, drift, or intermittent issues.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky_config.run_engine_setup import create_headless_run_engine
from bluesky_config.devices import GNURadioSignalGenerator, PowerMeter, MockDetector
from bluesky_config.plans import time_series_acquisition
from bluesky_config.callbacks import (StatisticsCallback, ProgressCallback,
                                       DocumentLogger, ThresholdAlertCallback)
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run time series monitoring experiment."""

    # Create headless RunEngine (no GUI/plotting)
    RE, bec = create_headless_run_engine()
    RE.subscribe(bec)

    stats = StatisticsCallback(['det_value'])
    RE.subscribe(stats)

    progress = ProgressCallback()
    RE.subscribe(progress)

    doc_logger = DocumentLogger('data/documents')
    RE.subscribe(doc_logger)

    # Threshold alert callback for detecting anomalies
    try:
        threshold_alert = ThresholdAlertCallback('det_value',
                                                  low_threshold=0.5,
                                                  high_threshold=2.0)
        RE.subscribe(threshold_alert)
    except AttributeError:
        # ThresholdAlertCallback may not be implemented yet
        print("⚠️  ThresholdAlertCallback not available, skipping")

    # Create devices
    print("Setting up devices...")
    try:
        sig_gen = GNURadioSignalGenerator('', name='sig_gen',
                                           host='localhost', port=8080)
        print("✓ Connected to GNU Radio")
        use_mock = False
    except ConnectionError as e:
        print(f"\n⚠️  GNU Radio not available: {e}")
        print("   Using MockDetector for demonstration\n")
        from ophyd import Signal
        sig_gen = Signal(name='sig_gen', value=98.5e6)  # Ottawa CBC Radio One
        use_mock = True

    # Create detector
    if use_mock:
        detector = MockDetector(name='det', noise_level=0.15)
    else:
        detector = PowerMeter(name='det')

    # Monitoring parameters
    monitor_frequency = 98.5e6  # 98.5 MHz (Ottawa CBC Radio One)
    num_samples = 100           # Number of samples to collect
    sample_interval = 1.0       # 1 second between samples

    # Set frequency (if not using mock)
    if hasattr(sig_gen, 'frequency'):
        print(f"Setting frequency to {monitor_frequency/1e6:.1f} MHz...")
        sig_gen.frequency.set(monitor_frequency).wait()
        print("✓ Frequency set")

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='TIMESERIES-001',
        purpose='Monitor signal stability over time',
        plan_type='time_series_acquisition',
        temperature=22.5,
        monitor_frequency=monitor_frequency,
        num_samples=num_samples,
        sample_interval=sample_interval,
        notes='Monitoring for signal drift and anomalies',
    )

    print("\n" + "="*70)
    print("TIME SERIES MONITORING EXPERIMENT")
    print("="*70)
    print(f"Experiment ID: {md['experiment_id']}")
    print(f"Operator: {md['operator']}")
    print(f"Purpose: {md['purpose']}")
    print(f"\nMonitoring frequency: {monitor_frequency/1e6:.1f} MHz")
    print(f"Number of samples: {num_samples}")
    print(f"Sample interval: {sample_interval:.1f} seconds")
    print(f"Total duration: {num_samples * sample_interval / 60:.1f} minutes")
    print("\nMonitoring for:")
    print("  • Signal strength variations")
    print("  • Drift over time")
    print("  • Anomalies and outliers")
    print("="*70 + "\n")

    # Run the time series acquisition
    uid = RE(time_series_acquisition([detector], num_samples, sample_interval), **md)

    print("\n" + "="*70)
    print("TIME SERIES MONITORING COMPLETE")
    print("="*70)
    print(f"Run UID: {uid[0][:8]}")
    print(f"\nDocuments saved to: data/documents/{uid[0][:8]}_*.json")
    print("\nTo analyze this data:")
    print(f"  from databroker import Broker")
    print(f"  db = Broker.named('temp')")
    print(f"  run = db['{uid[0][:8]}']")
    print(f"  table = run.table()")
    print(f"  # Plot time series to see drift and variations")
    print(f"  import matplotlib.pyplot as plt")
    print(f"  table['det_value'].plot()")
    print(f"  plt.show()")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
