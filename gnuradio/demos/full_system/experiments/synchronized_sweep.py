#!/usr/bin/env python3
"""
Synchronized TX/RX Sweep Experiment

This experiment demonstrates multi-device coordination by sweeping
both transmitter and receiver frequencies synchronously while
monitoring signal strength.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky_config.run_engine_setup import create_headless_run_engine
from bluesky_config.devices import GNURadioSignalGenerator, PowerMeter, MockDetector
from bluesky_config.plans import synchronized_tx_rx_scan
from bluesky_config.callbacks import (PeakDetectorCallback, StatisticsCallback,
                                       ProgressCallback, DocumentLogger)
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run synchronized TX/RX sweep experiment."""

    # Create headless RunEngine (no GUI/plotting)
    RE, bec = create_headless_run_engine()
    RE.subscribe(bec)

    peak_detector = PeakDetectorCallback('det_value', threshold=1.8)
    RE.subscribe(peak_detector)

    stats = StatisticsCallback(['det_value'])
    RE.subscribe(stats)

    progress = ProgressCallback()
    RE.subscribe(progress)

    doc_logger = DocumentLogger('data/documents')
    RE.subscribe(doc_logger)

    # Create devices
    print("Setting up devices...")
    try:
        tx_gen = GNURadioSignalGenerator('', name='tx_gen',
                                          host='localhost', port=8080)
        rx_gen = GNURadioSignalGenerator('', name='rx_gen',
                                          host='localhost', port=8081)
        print("✓ Connected to GNU Radio TX and RX")
        use_mock = False
    except ConnectionError as e:
        print(f"\n⚠️  GNU Radio not available: {e}")
        print("   Using mock devices for demonstration\n")
        from ophyd import Signal
        tx_gen = Signal(name='tx_gen', value=100e6)
        rx_gen = Signal(name='rx_gen', value=100e6)
        use_mock = True

    # Create detector
    if use_mock:
        # MockDetector simulates maximum signal when TX and RX are aligned
        detector = MockDetector(name='det', noise_level=0.1)
    else:
        detector = PowerMeter(name='det')

    # Sweep parameters
    start_freq = 88e6      # 88 MHz
    stop_freq = 108e6      # 108 MHz
    num_points = 40

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='SYNC-SWEEP-001',
        purpose='Synchronized TX/RX frequency sweep',
        plan_type='synchronized_tx_rx_scan',
        temperature=22.5,
        start_freq=start_freq,
        stop_freq=stop_freq,
        num_points=num_points,
        notes='TX and RX frequencies move together',
    )

    print("\n" + "="*70)
    print("SYNCHRONIZED TX/RX SWEEP EXPERIMENT")
    print("="*70)
    print(f"Experiment ID: {md['experiment_id']}")
    print(f"Operator: {md['operator']}")
    print(f"Purpose: {md['purpose']}")
    print(f"\nFrequency range: {start_freq/1e6:.1f} - {stop_freq/1e6:.1f} MHz")
    print(f"Number of points: {num_points}")
    print(f"Step size: {(stop_freq-start_freq)/num_points/1e6:.2f} MHz")
    print("\nThis experiment:")
    print("  • Sweeps TX and RX together across frequency range")
    print("  • Ensures both devices stay synchronized")
    print("  • Measures signal strength at each frequency")
    print("  • Useful for finding optimal TX/RX alignment")
    print("="*70 + "\n")

    # Run the synchronized sweep
    uid = RE(synchronized_tx_rx_scan(tx_gen, rx_gen, [detector],
                                      start_freq, stop_freq, num_points), **md)

    print("\n" + "="*70)
    print("SYNCHRONIZED SWEEP COMPLETE")
    print("="*70)
    print(f"Run UID: {uid[0][:8]}")
    print(f"\nDocuments saved to: data/documents/{uid[0][:8]}_*.json")
    print("\nTo analyze this data:")
    print(f"  from databroker import Broker")
    print(f"  db = Broker.named('temp')")
    print(f"  run = db['{uid[0][:8]}']")
    print(f"  table = run.table()")
    print(f"  # Verify TX and RX frequencies stayed synchronized")
    print(f"  print(table[['tx_gen_frequency', 'rx_gen_frequency', 'det_value']])")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
