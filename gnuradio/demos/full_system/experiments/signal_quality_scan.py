#!/usr/bin/env python3
"""
Signal Quality Scan Experiment

This experiment scans through a frequency range while monitoring
signal quality metrics.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky_config.run_engine_setup import create_headless_run_engine
from bluesky_config.devices import GNURadioSignalGenerator, PowerMeter
from bluesky_config.plans import frequency_scan
from bluesky_config.callbacks import (PeakDetectorCallback, StatisticsCallback,
                                       ProgressCallback, DocumentLogger)
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run signal quality scan experiment."""

    # Create headless RunEngine (no GUI/plotting)
    RE, bec = create_headless_run_engine()
    RE.subscribe(bec)

    peak_detector = PeakDetectorCallback('power_meter_power', threshold=-30.0)
    RE.subscribe(peak_detector)

    stats = StatisticsCallback(['power_meter_power'])
    RE.subscribe(stats)

    progress = ProgressCallback()
    RE.subscribe(progress)

    doc_logger = DocumentLogger('data/documents')
    RE.subscribe(doc_logger)

    # Create devices
    print("Connecting to GNU Radio...")
    try:
        sig_gen = GNURadioSignalGenerator('', name='sig_gen',
                                           host='localhost', port=8080)
    except ConnectionError as e:
        print(f"\n❌ {e}")
        print("\nℹ️  Make sure GNU Radio flowgraph is running with XML-RPC server on port 8080")
        print("   Or modify this script to use MockDetector for testing\n")
        return 1

    # Create power meter (simulated for now)
    power_meter = PowerMeter(name='power_meter')

    # Scan parameters
    start_freq = 100e6   # 100 MHz
    stop_freq = 200e6    # 200 MHz
    num_points = 50

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='SIG-QUAL-001',
        purpose='Scan frequency range and measure signal quality',
        plan_type='frequency_scan',
        temperature=22.0,
        start_freq=start_freq,
        stop_freq=stop_freq,
        num_points=num_points,
    )

    print("\n" + "="*70)
    print("SIGNAL QUALITY SCAN EXPERIMENT")
    print("="*70)
    print(f"Experiment ID: {md['experiment_id']}")
    print(f"Operator: {md['operator']}")
    print(f"Purpose: {md['purpose']}")
    print(f"\nFrequency range: {start_freq/1e6:.1f} - {stop_freq/1e6:.1f} MHz")
    print(f"Number of points: {num_points}")
    print(f"Step size: {(stop_freq-start_freq)/num_points/1e6:.2f} MHz")
    print("="*70 + "\n")

    # Run the scan
    uid = RE(frequency_scan([power_meter], sig_gen, start_freq, stop_freq,
                             num_points), **md)

    print("\n" + "="*70)
    print("SCAN COMPLETE")
    print("="*70)
    print(f"Run UID: {uid[0][:8]}")
    print(f"\nDocuments saved to: data/documents/{uid[0][:8]}_documents.jsonl")
    print("\nTo analyze this data:")
    print(f"  from databroker import Broker")
    print(f"  db = Broker.named('temp')")
    print(f"  run = db['{uid[0][:8]}']")
    print(f"  table = run.table()")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
