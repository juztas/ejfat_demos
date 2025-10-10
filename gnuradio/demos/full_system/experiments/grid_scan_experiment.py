#!/usr/bin/env python3
"""
Grid Scan Experiment (2D Parameter Space)

This experiment maps signal response across two independent parameters
(e.g., TX frequency vs RX frequency, or frequency vs gain) to create
a 2D heat map of the response surface.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import headless RunEngine setup (sets matplotlib backend before other imports)
from bluesky_config.run_engine_setup import create_headless_run_engine

from bluesky_config.devices import GNURadioSignalGenerator, PowerMeter, MockDetector
from bluesky_config.plans import grid_scan_2d
from bluesky_config.callbacks import (StatisticsCallback, ProgressCallback,
                                       DocumentLogger)
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run 2D grid scan experiment."""

    # Create headless RunEngine (no GUI/plotting)
    RE, bec = create_headless_run_engine()
    RE.subscribe(bec)

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
        tx_gen = Signal(name='tx_gen', value=98.5e6)
        rx_gen = Signal(name='rx_gen', value=98.5e6)
        use_mock = True

    # Create detector
    if use_mock:
        # MockDetector will show maximum when TX and RX are close
        detector = MockDetector(name='det', noise_level=0.1)
    else:
        detector = PowerMeter(name='det')

    # Grid scan parameters
    # TX frequency range
    tx_start = 98.0e6      # 98.0 MHz
    tx_stop = 99.0e6       # 99.0 MHz
    tx_num = 15            # 15 points (67 kHz steps)

    # RX frequency range
    rx_start = 98.0e6      # 98.0 MHz
    rx_stop = 99.0e6       # 99.0 MHz
    rx_num = 15            # 15 points (67 kHz steps)

    total_points = tx_num * rx_num

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='GRID-2D-001',
        purpose='Map TX/RX frequency response surface',
        plan_type='grid_scan_2d',
        temperature=22.5,
        tx_start=tx_start,
        tx_stop=tx_stop,
        tx_num=tx_num,
        rx_start=rx_start,
        rx_stop=rx_stop,
        rx_num=rx_num,
        total_points=total_points,
        notes='2D grid scan to map response across TX and RX frequencies',
    )

    print("\n" + "="*70)
    print("2D GRID SCAN EXPERIMENT")
    print("="*70)
    print(f"Experiment ID: {md['experiment_id']}")
    print(f"Operator: {md['operator']}")
    print(f"Purpose: {md['purpose']}")
    print(f"\nTX Frequency:")
    print(f"  Range: {tx_start/1e6:.2f} - {tx_stop/1e6:.2f} MHz")
    print(f"  Points: {tx_num}")
    print(f"  Step: {(tx_stop-tx_start)/tx_num/1e3:.1f} kHz")
    print(f"\nRX Frequency:")
    print(f"  Range: {rx_start/1e6:.2f} - {rx_stop/1e6:.2f} MHz")
    print(f"  Points: {rx_num}")
    print(f"  Step: {(rx_stop-rx_start)/rx_num/1e3:.1f} kHz")
    print(f"\nTotal measurements: {total_points}")
    print(f"Estimated time: {total_points * 2.5 / 60:.1f} minutes")
    print("  (2.5s per point including 2s settling time)")
    print("\nThis experiment:")
    print("  • Creates a 2D grid across TX and RX frequencies")
    print("  • Uses snake pattern for efficient scanning")
    print("  • Results can be visualized as a heat map")
    print("  • Useful for finding optimal TX/RX frequency pairs")
    print("="*70 + "\n")

    # Run the 2D grid scan
    uid = RE(grid_scan_2d([detector],
                           tx_gen.frequency if hasattr(tx_gen, 'frequency') else tx_gen,
                           tx_start, tx_stop, tx_num,
                           rx_gen.frequency if hasattr(rx_gen, 'frequency') else rx_gen,
                           rx_start, rx_stop, rx_num), **md)

    print("\n" + "="*70)
    print("GRID SCAN COMPLETE")
    print("="*70)
    print(f"Run UID: {uid[0][:8]}")
    print(f"\nDocuments saved to: data/documents/{uid[0][:8]}_*.json")
    print("\nTo analyze and visualize this data:")
    print(f"  from databroker import Broker")
    print(f"  import matplotlib.pyplot as plt")
    print(f"  import numpy as np")
    print(f"  db = Broker.named('temp')")
    print(f"  run = db['{uid[0][:8]}']")
    print(f"  table = run.table()")
    print(f"  # Reshape data for 2D heat map")
    print(f"  tx_freq = table['tx_gen_frequency'].values.reshape({tx_num}, {rx_num})")
    print(f"  rx_freq = table['rx_gen_frequency'].values.reshape({tx_num}, {rx_num})")
    print(f"  signal = table['det_value'].values.reshape({tx_num}, {rx_num})")
    print(f"  # Create heat map")
    print(f"  plt.pcolormesh(tx_freq/1e6, rx_freq/1e6, signal, shading='auto')")
    print(f"  plt.colorbar(label='Signal Strength')")
    print(f"  plt.xlabel('TX Frequency (MHz)')")
    print(f"  plt.ylabel('RX Frequency (MHz)')")
    print(f"  plt.title('2D Frequency Response Map')")
    print(f"  plt.show()")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
