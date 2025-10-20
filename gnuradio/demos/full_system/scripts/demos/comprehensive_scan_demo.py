#!/usr/bin/env python3
"""
Comprehensive Frequency Scan Demo

A complete experiment demonstrating:
1. Data collection from real GNU Radio device
2. Multiple samples per frequency for statistical analysis
3. Data persistence via DataBroker
4. Post-scan analysis and statistics
5. Data export and visualization
"""

import sys
from pathlib import Path
import numpy as np

# Set matplotlib backend before any imports
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add project root to path (2 levels up from scripts/demos/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from databroker import Broker

from bluesky_config.devices import GNURadioSignalGenerator, MockDetector
from bluesky_config.plans import frequency_characterization
from bluesky_config.metadata import create_experiment_metadata
from bluesky_config.callbacks import DocumentLogger, StatisticsCallback

from analysis.statistics import analyze_run, find_peaks
from analysis.export import export_to_csv, export_to_hdf5
from analysis.plotting import plot_run


def main():
    """Run comprehensive frequency scan experiment."""
    print("=" * 80)
    print("COMPREHENSIVE FREQUENCY SCAN EXPERIMENT")
    print("=" * 80)
    print()
    print("This experiment will:")
    print("  1. Connect to GNU Radio signal generator (real device)")
    print("  2. Scan 10 frequencies from 1 MHz to 10 MHz")
    print("  3. Take 5 samples at each frequency for statistical analysis")
    print("  4. Save all data to DataBroker")
    print("  5. Perform statistical analysis")
    print("  6. Export data to CSV and HDF5")
    print("  7. Generate plots")
    print("=" * 80)
    print()

    # =========================================================================
    # STEP 1: Setup experiment infrastructure
    # =========================================================================
    print("STEP 1: Setting up experiment infrastructure...")
    print("-" * 80)

    # Create RunEngine
    RE = RunEngine({})
    print("✓ RunEngine created")

    # Setup DataBroker for persistent storage
    db = Broker.named('temp')
    RE.subscribe(db.insert)
    print("✓ DataBroker connected (temp catalog)")

    # Add BestEffortCallback for live feedback
    bec = BestEffortCallback()
    RE.subscribe(bec)
    print("✓ BestEffortCallback subscribed")

    # Add document logger to save raw documents
    doc_logger = DocumentLogger('data/documents')
    RE.subscribe(doc_logger)
    print("✓ DocumentLogger subscribed (saving to data/documents/)")

    # Add statistics callback for live statistics
    stats = StatisticsCallback(['det_value', 'sig_gen_frequency'])
    RE.subscribe(stats)
    print("✓ StatisticsCallback subscribed")

    print()

    # =========================================================================
    # STEP 2: Create devices
    # =========================================================================
    print("STEP 2: Creating devices...")
    print("-" * 80)

    # Real GNU Radio signal generator
    sig_gen = GNURadioSignalGenerator('', name='sig_gen',
                                       host='localhost', port=8080)
    print(f"✓ Connected to GNU Radio signal generator")

    # Mock detector (in real experiment, this would be SDR receiver)
    detector = MockDetector(name='det', noise_level=0.15)
    print(f"✓ Mock detector created (noise_level=0.15)")

    print()

    # =========================================================================
    # STEP 3: Define experiment parameters
    # =========================================================================
    print("STEP 3: Defining experiment parameters...")
    print("-" * 80)

    frequencies = np.linspace(1e6, 10e6, 10)  # 10 frequencies from 1-10 MHz
    num_samples = 5  # 5 samples per frequency

    print(f"Frequencies to scan: {len(frequencies)} points")
    print(f"  Range: {frequencies[0]/1e6:.1f} - {frequencies[-1]/1e6:.1f} MHz")
    print(f"  Samples per frequency: {num_samples}")
    print(f"  Total measurements: {len(frequencies) * num_samples}")
    print(f"  Estimated time: ~{len(frequencies) * (1.0 + num_samples * 0.1):.0f} seconds")

    print()

    # =========================================================================
    # STEP 4: Create experiment metadata
    # =========================================================================
    print("STEP 4: Creating experiment metadata...")
    print("-" * 80)

    md = create_experiment_metadata(
        experiment_id='DEMO-COMPREHENSIVE-001',
        purpose='Comprehensive frequency scan demo with analysis',
        plan_type='frequency_characterization',
        operator='demo_user',
        sample='Mock Signal',
        temperature=22.5,
        humidity=45,
        notes='Demonstrating full workflow: collection -> analysis -> export',
    )
    print(f"✓ Metadata created: {md['experiment_id']}")
    print(f"  Purpose: {md['purpose']}")

    print()

    # =========================================================================
    # STEP 5: Run the scan
    # =========================================================================
    print("STEP 5: Running frequency characterization scan...")
    print("=" * 80)

    uid = RE(frequency_characterization(
        detectors=[detector],
        signal_gen=sig_gen,
        frequencies=frequencies,
        num_samples=num_samples
    ), **md)

    print("=" * 80)
    print("✓ Scan completed successfully!")
    print(f"  Scan UID: {uid[0][:8]}")

    print()

    # =========================================================================
    # STEP 6: Retrieve data from DataBroker
    # =========================================================================
    print("STEP 6: Retrieving data from DataBroker...")
    print("-" * 80)

    # Get the run we just completed
    run = db[uid[0]]
    print(f"✓ Retrieved run: {uid[0][:8]}")

    # Get data as pandas DataFrame
    table = run.table()
    print(f"✓ Data table created: {len(table)} rows × {len(table.columns)} columns")
    print(f"  Columns: {list(table.columns)}")
    print()
    print("Data preview:")
    print(table.head(10))

    print()

    # =========================================================================
    # STEP 7: Statistical Analysis
    # =========================================================================
    print()
    print("STEP 7: Performing statistical analysis...")
    print("-" * 80)

    # Analyze detector values
    det_stats = analyze_run(run, 'det_value')
    print("Detector Value Statistics:")
    print(f"  Mean:        {det_stats['mean']:.4f}")
    print(f"  Median:      {det_stats['median']:.4f}")
    print(f"  Std:         {det_stats['std']:.4f}")
    print(f"  Min:         {det_stats['min']:.4f}")
    print(f"  Max:         {det_stats['max']:.4f}")
    print(f"  Peak-to-Peak:{det_stats['peak_to_peak']:.4f}")

    # Note: frequency_characterization plan doesn't log sig_gen_frequency for each sample
    # so we can't do per-frequency grouping or peak detection by frequency
    # We can only look at time-series peaks
    print()
    print("Note: Using sequence number for peak detection (not frequency)")
    print("      The scan visited 10 frequencies with 5 samples each")

    print()

    # =========================================================================
    # STEP 8: Export data
    # =========================================================================
    print("STEP 8: Exporting data...")
    print("-" * 80)

    # Create export directory
    export_dir = Path('data/exports')
    export_dir.mkdir(parents=True, exist_ok=True)

    # Export to CSV (simple version without metadata header)
    csv_path = export_dir / f'scan_{uid[0][:8]}.csv'
    table.to_csv(csv_path, index=True)
    print(f"✓ Exported to CSV: {csv_path}")

    # Skip HDF5 export (requires pytables module)
    # hdf5_path = export_dir / f'scan_{uid[0][:8]}.h5'
    # table.to_hdf(hdf5_path, 'data', mode='w', complevel=9)
    # print(f"✓ Exported to HDF5: {hdf5_path}")

    print()

    # =========================================================================
    # STEP 9: Generate plots
    # =========================================================================
    print("STEP 9: Generating plots...")
    print("-" * 80)

    # Create plots directory
    plots_dir = Path('data/plots')
    plots_dir.mkdir(parents=True, exist_ok=True)

    # Note: Can't plot vs frequency since frequency_characterization doesn't log it per sample
    # Plot 1: Detector value time series instead

    # Plot 2: Detector value time series
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(table.index, table['det_value'], 'o-', alpha=0.7)
    ax.set_xlabel('Measurement Number')
    ax.set_ylabel('Detector Value')
    ax.set_title('Detector Value Time Series')
    ax.grid(True, alpha=0.3)
    plot2_path = plots_dir / f'scan_{uid[0][:8]}_timeseries.png'
    plt.savefig(plot2_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated plot: {plot2_path}")

    # Plot 3: Histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(table['det_value'], bins=20, alpha=0.7, edgecolor='black')
    ax.axvline(det_stats['mean'], color='r', linestyle='--', linewidth=2, label=f'Mean: {det_stats["mean"]:.3f}')
    ax.axvline(det_stats['median'], color='g', linestyle='--', linewidth=2, label=f'Median: {det_stats["median"]:.3f}')
    ax.set_xlabel('Detector Value')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Detector Values')
    ax.grid(True, alpha=0.3)
    ax.legend()
    plot3_path = plots_dir / f'scan_{uid[0][:8]}_histogram.png'
    plt.savefig(plot3_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated plot: {plot3_path}")

    print()

    # =========================================================================
    # STEP 10: Summary
    # =========================================================================
    print("=" * 80)
    print("EXPERIMENT COMPLETE!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  Scan UID: {uid[0][:8]}")
    print(f"  Total measurements: {len(table)}")
    print(f"  Frequencies scanned: {len(frequencies)}")
    print(f"  Samples per frequency: {num_samples}")
    print()
    print("Data saved to:")
    print(f"  CSV:  {csv_path}")
    print()
    print("Plots saved to:")
    print(f"  {plot2_path}")
    print(f"  {plot3_path}")
    print()
    print("To retrieve this data later:")
    print(f"  from databroker import Broker")
    print(f"  db = Broker.named('temp')")
    print(f"  run = db['{uid[0][:8]}']  # Use UID prefix")
    print(f"  table = run.table()")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
