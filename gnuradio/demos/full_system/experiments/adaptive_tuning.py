#!/usr/bin/env python3
"""
Adaptive Tuning Experiment

This experiment uses adaptive scanning to efficiently map signal response
by taking smaller steps where the signal changes rapidly and larger steps
where it's stable.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky_config.run_engine_setup import create_headless_run_engine
from bluesky_config.devices import GNURadioSignalGenerator, PowerMeter, MockDetector
from bluesky_config.plans import adaptive_frequency_scan
from bluesky_config.callbacks import (PeakDetectorCallback, StatisticsCallback,
                                       ProgressCallback, DocumentLogger)
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run adaptive frequency tuning experiment."""

    # Create headless RunEngine (no GUI/plotting)
    RE, bec = create_headless_run_engine()
    RE.subscribe(bec)

    peak_detector = PeakDetectorCallback('det_value', threshold=1.5)
    RE.subscribe(peak_detector)

    stats = StatisticsCallback(['det_value'])
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
        print("✓ Connected to GNU Radio")
        use_mock = False
    except ConnectionError as e:
        print(f"\n⚠️  GNU Radio not available: {e}")
        print("   Using MockDetector for demonstration\n")
        from ophyd import Signal
        sig_gen = Signal(name='sig_gen', value=100e6)
        use_mock = True

    # Create detector
    if use_mock:
        # MockDetector simulates a signal with peaks
        detector = MockDetector(name='det', noise_level=0.1)
    else:
        detector = PowerMeter(name='det')

    # Scan parameters
    start_freq = 88e6      # 88 MHz (FM band start)
    stop_freq = 108e6      # 108 MHz (FM band end)
    target_delta = 0.05    # Adjust step when signal changes by 5%
    min_step = 100e3       # Minimum 100 kHz steps
    max_step = 2e6         # Maximum 2 MHz steps

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='ADAPTIVE-001',
        purpose='Adaptive frequency scan with variable step size',
        plan_type='adaptive_frequency_scan',
        temperature=22.5,
        start_freq=start_freq,
        stop_freq=stop_freq,
        target_delta=target_delta,
        min_step=min_step,
        max_step=max_step,
        notes='Uses smaller steps where signal changes rapidly',
    )

    print("\n" + "="*70)
    print("ADAPTIVE FREQUENCY TUNING EXPERIMENT")
    print("="*70)
    print(f"Experiment ID: {md['experiment_id']}")
    print(f"Operator: {md['operator']}")
    print(f"Purpose: {md['purpose']}")
    print(f"\nFrequency range: {start_freq/1e6:.1f} - {stop_freq/1e6:.1f} MHz")
    print(f"Target delta: {target_delta*100:.1f}%")
    print(f"Step range: {min_step/1e3:.0f} kHz - {max_step/1e6:.1f} MHz")
    print("\nThe scan will automatically:")
    print("  • Take smaller steps where signal changes rapidly")
    print("  • Take larger steps where signal is stable")
    print("  • Efficiently map the entire frequency range")
    print("="*70 + "\n")

    # Run the adaptive scan
    uid = RE(adaptive_frequency_scan([detector], sig_gen,
                                      start_freq, stop_freq,
                                      target_delta=target_delta,
                                      min_step=min_step,
                                      max_step=max_step), **md)

    print("\n" + "="*70)
    print("ADAPTIVE SCAN COMPLETE")
    print("="*70)
    print(f"Run UID: {uid[0][:8]}")
    print(f"\nDocuments saved to: data/documents/{uid[0][:8]}_*.json")
    print("\nTo analyze this data:")
    print(f"  from databroker import Broker")
    print(f"  db = Broker.named('temp')")
    print(f"  run = db['{uid[0][:8]}']")
    print(f"  table = run.table()")
    print(f"  # Plot frequency vs detector reading to see adaptive sampling")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
