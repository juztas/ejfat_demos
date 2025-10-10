#!/usr/bin/env python3
"""
Frequency Characterization Experiment

This experiment characterizes signal response across a frequency range
by taking multiple measurements at specific frequencies.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky_config.run_engine_setup import create_headless_run_engine
from bluesky_config.devices import GNURadioSignalGenerator, MockDetector
from bluesky_config.plans import frequency_characterization
from bluesky_config.callbacks import PeakDetectorCallback, StatisticsCallback
from bluesky_config.metadata import create_experiment_metadata, get_standard_fm_metadata


def main():
    """Run frequency characterization experiment."""

    # Create headless RunEngine (no GUI/plotting)
    RE, bec = create_headless_run_engine()
    RE.subscribe(bec)

    peak_detector = PeakDetectorCallback('det_value', threshold=1.5)
    RE.subscribe(peak_detector)

    stats = StatisticsCallback(['det_value'])
    RE.subscribe(stats)

    # Create devices
    print("Connecting to GNU Radio...")
    try:
        sig_gen = GNURadioSignalGenerator('', name='sig_gen',
                                           host='localhost', port=8080)
    except ConnectionError as e:
        print(f"\n❌ {e}")
        print("\nℹ️  Make sure GNU Radio flowgraph is running with XML-RPC server on port 8080")
        print("   Or use MockDetector for testing without hardware\n")
        return 1

    # Create detector (could be real hardware or mock)
    detector = MockDetector(name='det', noise_level=0.2)

    # Define frequencies to characterize (in Hz)
    frequencies = [
        1000,    # 1 kHz
        2000,    # 2 kHz
        3000,    # 3 kHz
        5000,    # 5 kHz
        10000,   # 10 kHz
    ]

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='FREQ-CHAR-001',
        purpose='Characterize frequency response of signal generator',
        plan_type='frequency_characterization',
        temperature=22.5,
        frequencies=frequencies,
        num_samples=10,
    )

    print("\n" + "="*70)
    print("FREQUENCY CHARACTERIZATION EXPERIMENT")
    print("="*70)
    print(f"Experiment ID: {md['experiment_id']}")
    print(f"Operator: {md['operator']}")
    print(f"Purpose: {md['purpose']}")
    print(f"\nFrequencies: {[f/1e3 for f in frequencies]} kHz")
    print(f"Samples per frequency: 10")
    print("="*70 + "\n")

    # Run the experiment
    uid = RE(frequency_characterization([detector], sig_gen, frequencies,
                                         num_samples=10), **md)

    print("\n" + "="*70)
    print("EXPERIMENT COMPLETE")
    print("="*70)
    print(f"Run UID: {uid[0][:8]}")
    print("\nTo analyze this data:")
    print(f"  from databroker import Broker")
    print(f"  db = Broker.named('temp')")
    print(f"  run = db['{uid[0][:8]}']")
    print(f"  table = run.table()")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
