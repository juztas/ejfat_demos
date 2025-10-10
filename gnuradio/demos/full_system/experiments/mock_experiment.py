#!/usr/bin/env python3
"""
Mock Experiment (No Hardware Required)

This is a simple experiment using mock devices for testing the Bluesky
framework without requiring GNU Radio or other hardware.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky_config.run_engine_setup import create_headless_run_engine
from ophyd import Signal
from bluesky.plans import scan
from bluesky_config.devices import MockDetector
from bluesky_config.callbacks import (PeakDetectorCallback, StatisticsCallback,
                                       ProgressCallback, DocumentLogger)
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run mock experiment for testing."""

    # Create headless RunEngine (no GUI/plotting)
    RE, bec = create_headless_run_engine()
    RE.subscribe(bec)

    peak_detector = PeakDetectorCallback('det_value', threshold=1.2)
    RE.subscribe(peak_detector)

    stats = StatisticsCallback(['det_value'])
    RE.subscribe(stats)

    progress = ProgressCallback()
    RE.subscribe(progress)

    doc_logger = DocumentLogger('data/documents')
    RE.subscribe(doc_logger)

    # Create mock devices (no hardware required)
    motor = Signal(name='motor', value=0)
    detector = MockDetector(name='det', noise_level=0.15)

    # Scan parameters
    start = 0
    stop = 10
    num_points = 20

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='MOCK-001',
        purpose='Test Bluesky framework with mock devices',
        plan_type='scan',
        start=start,
        stop=stop,
        num_points=num_points,
    )

    print("\n" + "="*70)
    print("MOCK EXPERIMENT (No Hardware Required)")
    print("="*70)
    print(f"Experiment ID: {md['experiment_id']}")
    print(f"Operator: {md['operator']}")
    print(f"Purpose: {md['purpose']}")
    print(f"\nMotor range: {start} - {stop}")
    print(f"Number of points: {num_points}")
    print("="*70 + "\n")

    # Run the scan
    uid = RE(scan([detector], motor, start, stop, num_points), **md)

    print("\n" + "="*70)
    print("EXPERIMENT COMPLETE")
    print("="*70)
    print(f"Run UID: {uid[0][:8]}")
    print(f"\nDocuments saved to: data/documents/{uid[0][:8]}_documents.jsonl")
    print("\nTo analyze this data:")
    print(f"  from databroker import Broker")
    print(f"  db = Broker.named('temp')")
    print(f"  run = db['{uid[0][:8]}']")
    print(f"  table = run.table()")
    print(f"  print(table)")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
