#!/usr/bin/env python3
"""
Peak Finding Experiment

This experiment uses a two-stage scan strategy to efficiently locate
and characterize signal peaks:
1. Coarse scan to identify peak locations
2. Fine scan around each peak for detailed characterization
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky_config.run_engine_setup import create_headless_run_engine
from bluesky_config.devices import GNURadioSignalGenerator, PowerMeter, MockDetector
from bluesky_config.plans import peak_finding_scan
from bluesky_config.callbacks import (PeakDetectorCallback, StatisticsCallback,
                                       ProgressCallback, DocumentLogger)
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run peak finding experiment."""

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
        sig_gen = Signal(name='sig_gen', value=88e6)
        use_mock = True

    # Create detector
    if use_mock:
        # MockDetector will simulate peaks at specific frequencies
        detector = MockDetector(name='det', noise_level=0.15)
    else:
        detector = PowerMeter(name='det')

    # Scan parameters
    start_freq = 88e6       # 88 MHz (Ottawa FM band start)
    stop_freq = 108e6       # 108 MHz (Ottawa FM band end)
    coarse_points = 30      # Initial coarse scan points

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='PEAK-FIND-001',
        purpose='Locate and characterize FM broadcast stations',
        plan_type='peak_finding_scan',
        temperature=22.5,
        start_freq=start_freq,
        stop_freq=stop_freq,
        num_initial_points=coarse_points,
        notes='Two-stage scan: coarse scan + fine scan around peaks',
    )

    print("\n" + "="*70)
    print("PEAK FINDING EXPERIMENT")
    print("="*70)
    print(f"Experiment ID: {md['experiment_id']}")
    print(f"Operator: {md['operator']}")
    print(f"Purpose: {md['purpose']}")
    print(f"\nFrequency range: {start_freq/1e6:.1f} - {stop_freq/1e6:.1f} MHz")
    print(f"Coarse scan points: {coarse_points}")
    print(f"Coarse step size: {(stop_freq-start_freq)/coarse_points/1e6:.2f} MHz")
    print("\nThis experiment:")
    print("  • Stage 1: Quick coarse scan to locate peaks")
    print("  • Automatic peak detection using scipy.signal.find_peaks")
    print("  • Stage 2: Fine scan around each detected peak")
    print("  • Efficient way to characterize sparse signals (FM stations)")
    print("="*70 + "\n")

    # Run the peak finding scan
    uid = RE(peak_finding_scan([detector], sig_gen,
                                start_freq, stop_freq,
                                num_initial_points=coarse_points), **md)

    print("\n" + "="*70)
    print("PEAK FINDING COMPLETE")
    print("="*70)
    print(f"Run UID: {uid[0][:8]}")
    print(f"\nDocuments saved to: data/documents/{uid[0][:8]}_*.json")
    print("\nTo analyze this data:")
    print(f"  from databroker import Broker")
    print(f"  import matplotlib.pyplot as plt")
    print(f"  db = Broker.named('temp')")
    print(f"  run = db['{uid[0][:8]}']")
    print(f"  table = run.table()")
    print(f"  # Plot to see coarse scan + fine scans around peaks")
    print(f"  plt.plot(table['sig_gen_frequency']/1e6, table['det_value'], 'o-')")
    print(f"  plt.xlabel('Frequency (MHz)')")
    print(f"  plt.ylabel('Signal Strength')")
    print(f"  plt.title('Peak Finding Scan Results')")
    print(f"  plt.show()")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
