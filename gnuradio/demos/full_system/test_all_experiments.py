#!/usr/bin/env python3
"""
Comprehensive Test Script for Phase 4 Experiment Types

This script demonstrates all experiment types from Phase 4:
1. Basic Scans (frequency_scan, frequency_characterization)
2. Adaptive Scans (adaptive_frequency_scan)
3. Time Series (time_series_acquisition)
4. Custom Plans (peak_finding_scan)
5. Multi-Device Coordination (synchronized_tx_rx_scan, grid_scan_2d)

Usage:
    # Run all experiments
    ./test_all_experiments.py --all

    # Run specific experiment type
    ./test_all_experiments.py --basic
    ./test_all_experiments.py --adaptive
    ./test_all_experiments.py --timeseries
    ./test_all_experiments.py --peaks
    ./test_all_experiments.py --multidevice
    ./test_all_experiments.py --grid

    # Run with mock devices (no GNU Radio required)
    ./test_all_experiments.py --all --mock

    # Interactive mode
    ./test_all_experiments.py
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from bluesky_config.run_engine_setup import create_headless_run_engine
from bluesky_config.devices import GNURadioSignalGenerator, PowerMeter, MockDetector
from bluesky_config.plans import (
    frequency_scan, frequency_characterization,
    adaptive_frequency_scan, time_series_acquisition,
    peak_finding_scan, synchronized_tx_rx_scan, grid_scan_2d
)
from bluesky_config.callbacks import (
    PeakDetectorCallback, StatisticsCallback,
    ProgressCallback, DocumentLogger
)
from bluesky_config.metadata import create_experiment_metadata


class MockSignalGenerator:
    """Simple mock signal generator for testing."""
    def __init__(self, name):
        from ophyd import Signal, Component as Cpt, Device
        self.name = name
        # Create a Signal that acts like a frequency attribute
        self.frequency = Signal(name=f'{name}_frequency', value=98.5e6)


def setup_environment(use_mock=False):
    """Setup RunEngine, devices, and callbacks."""
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
    if use_mock:
        print("Using mock devices (no hardware required)\n")
        sig_gen1 = MockSignalGenerator('sig_gen')
        sig_gen2 = MockSignalGenerator('sig_gen2')
        detector = MockDetector(name='det', noise_level=0.15)
    else:
        print("Attempting to connect to GNU Radio...")
        try:
            sig_gen1 = GNURadioSignalGenerator('', name='sig_gen',
                                               host='localhost', port=8080)
            sig_gen2 = GNURadioSignalGenerator('', name='sig_gen2',
                                               host='localhost', port=8081)
            detector = PowerMeter(name='det')
            print("✓ Connected to GNU Radio\n")
        except ConnectionError as e:
            print(f"\n⚠️  GNU Radio not available: {e}")
            print("   Falling back to mock devices\n")
            sig_gen1 = MockSignalGenerator('sig_gen')
            sig_gen2 = MockSignalGenerator('sig_gen2')
            detector = MockDetector(name='det', noise_level=0.15)

    return RE, sig_gen1, sig_gen2, detector


def run_basic_scans(RE, sig_gen, detector):
    """Test basic scan plans."""
    print("\n" + "="*70)
    print("PHASE 4 TEST: BASIC SCANS")
    print("="*70)

    # Test 1: Frequency Scan
    print("\nTest 1: Basic Frequency Scan")
    print("-" * 50)
    md = create_experiment_metadata(
        experiment_id='PHASE4-BASIC-1',
        purpose='Test basic frequency scan',
        plan_type='frequency_scan',
    )
    uid = RE(frequency_scan([detector], sig_gen, 88e6, 92e6, 10), **md)
    print(f"✓ Completed: {uid[0][:8]}")

    # Test 2: Frequency Characterization
    print("\nTest 2: Frequency Characterization (multiple samples)")
    print("-" * 50)
    md = create_experiment_metadata(
        experiment_id='PHASE4-BASIC-2',
        purpose='Test frequency characterization with multiple samples',
        plan_type='frequency_characterization',
    )
    freqs = [88e6, 90e6, 92e6, 94e6]
    uid = RE(frequency_characterization([detector], sig_gen, freqs, num_samples=5), **md)
    print(f"✓ Completed: {uid[0][:8]}")


def run_adaptive_scan(RE, sig_gen, detector):
    """Test adaptive scan plans."""
    print("\n" + "="*70)
    print("PHASE 4 TEST: ADAPTIVE SCANS")
    print("="*70)
    print("\nAdaptive Frequency Scan (variable step size)")
    print("-" * 50)

    md = create_experiment_metadata(
        experiment_id='PHASE4-ADAPTIVE-1',
        purpose='Test adaptive frequency scan',
        plan_type='adaptive_frequency_scan',
    )
    uid = RE(adaptive_frequency_scan([detector], sig_gen, 88e6, 98e6,
                                      target_delta=0.05,
                                      min_step=100e3,
                                      max_step=1e6), **md)
    print(f"✓ Completed: {uid[0][:8]}")


def run_time_series(RE, detector):
    """Test time series acquisition."""
    print("\n" + "="*70)
    print("PHASE 4 TEST: TIME SERIES")
    print("="*70)
    print("\nTime Series Acquisition")
    print("-" * 50)

    md = create_experiment_metadata(
        experiment_id='PHASE4-TIMESERIES-1',
        purpose='Test time series data acquisition',
        plan_type='time_series_acquisition',
    )
    uid = RE(time_series_acquisition([detector], num_points=20, delay=0.5), **md)
    print(f"✓ Completed: {uid[0][:8]}")


def run_peak_finding(RE, sig_gen, detector):
    """Test peak finding scan."""
    print("\n" + "="*70)
    print("PHASE 4 TEST: PEAK FINDING (CUSTOM PLAN)")
    print("="*70)
    print("\nTwo-Stage Peak Finding Scan")
    print("-" * 50)

    md = create_experiment_metadata(
        experiment_id='PHASE4-PEAKS-1',
        purpose='Test peak finding scan',
        plan_type='peak_finding_scan',
    )
    uid = RE(peak_finding_scan([detector], sig_gen, 88e6, 98e6,
                                 num_initial_points=15), **md)
    print(f"✓ Completed: {uid[0][:8]}")


def run_multidevice_scan(RE, sig_gen1, sig_gen2, detector):
    """Test multi-device coordination."""
    print("\n" + "="*70)
    print("PHASE 4 TEST: MULTI-DEVICE COORDINATION")
    print("="*70)
    print("\nSynchronized TX/RX Sweep")
    print("-" * 50)

    md = create_experiment_metadata(
        experiment_id='PHASE4-MULTIDEV-1',
        purpose='Test synchronized TX/RX scan',
        plan_type='synchronized_tx_rx_scan',
    )
    uid = RE(synchronized_tx_rx_scan(sig_gen1, sig_gen2, [detector],
                                      88e6, 92e6, 15), **md)
    print(f"✓ Completed: {uid[0][:8]}")


def run_grid_scan(RE, sig_gen1, sig_gen2, detector):
    """Test 2D grid scan."""
    print("\n" + "="*70)
    print("PHASE 4 TEST: 2D GRID SCAN")
    print("="*70)
    print("\n2D Grid Scan (TX freq vs RX freq)")
    print("-" * 50)

    md = create_experiment_metadata(
        experiment_id='PHASE4-GRID-1',
        purpose='Test 2D grid scan',
        plan_type='grid_scan_2d',
    )

    # Get the frequency attributes or use the signals directly
    motor1 = sig_gen1.frequency if hasattr(sig_gen1, 'frequency') else sig_gen1
    motor2 = sig_gen2.frequency if hasattr(sig_gen2, 'frequency') else sig_gen2

    uid = RE(grid_scan_2d([detector],
                           motor1, 98.0e6, 98.5e6, 8,
                           motor2, 98.0e6, 98.5e6, 8), **md)
    print(f"✓ Completed: {uid[0][:8]}")


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description='Test all Phase 4 experiment types',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--all', action='store_true',
                        help='Run all experiment types')
    parser.add_argument('--basic', action='store_true',
                        help='Run basic scans')
    parser.add_argument('--adaptive', action='store_true',
                        help='Run adaptive scans')
    parser.add_argument('--timeseries', action='store_true',
                        help='Run time series acquisition')
    parser.add_argument('--peaks', action='store_true',
                        help='Run peak finding scan')
    parser.add_argument('--multidevice', action='store_true',
                        help='Run multi-device coordination')
    parser.add_argument('--grid', action='store_true',
                        help='Run 2D grid scan')
    parser.add_argument('--mock', action='store_true',
                        help='Use mock devices (no GNU Radio required)')

    args = parser.parse_args()

    # Interactive mode if no arguments
    if not any([args.all, args.basic, args.adaptive, args.timeseries,
                args.peaks, args.multidevice, args.grid]):
        print("\n" + "="*70)
        print("PHASE 4 EXPERIMENT TYPES - INTERACTIVE TEST")
        print("="*70)
        print("\nSelect experiment types to test:")
        print("  1. Basic Scans (frequency_scan, frequency_characterization)")
        print("  2. Adaptive Scans (adaptive_frequency_scan)")
        print("  3. Time Series (time_series_acquisition)")
        print("  4. Peak Finding (peak_finding_scan)")
        print("  5. Multi-Device Coordination (synchronized_tx_rx_scan)")
        print("  6. 2D Grid Scan (grid_scan_2d)")
        print("  7. All of the above")
        print("\nEnter numbers separated by spaces (e.g., '1 2 3'), or '7' for all:")

        try:
            selection = input("> ").strip()
            choices = [int(x) for x in selection.split()]
        except (ValueError, KeyboardInterrupt):
            print("\nCancelled.")
            return 0

        args.basic = 1 in choices or 7 in choices
        args.adaptive = 2 in choices or 7 in choices
        args.timeseries = 3 in choices or 7 in choices
        args.peaks = 4 in choices or 7 in choices
        args.multidevice = 5 in choices or 7 in choices
        args.grid = 6 in choices or 7 in choices

    # Setup environment
    print("\n" + "="*70)
    print("PHASE 4: EXPERIMENT TYPES & PLANS - COMPREHENSIVE TEST")
    print("="*70 + "\n")

    RE, sig_gen1, sig_gen2, detector = setup_environment(use_mock=args.mock)

    # Run selected tests
    try:
        if args.all or args.basic:
            run_basic_scans(RE, sig_gen1, detector)

        if args.all or args.adaptive:
            run_adaptive_scan(RE, sig_gen1, detector)

        if args.all or args.timeseries:
            run_time_series(RE, detector)

        if args.all or args.peaks:
            run_peak_finding(RE, sig_gen1, detector)

        if args.all or args.multidevice:
            run_multidevice_scan(RE, sig_gen1, sig_gen2, detector)

        if args.all or args.grid:
            run_grid_scan(RE, sig_gen1, sig_gen2, detector)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Summary
    print("\n" + "="*70)
    print("PHASE 4 TESTS COMPLETE")
    print("="*70)
    print("\nAll selected experiment types executed successfully!")
    print("\nExperiment types tested:")
    if args.all or args.basic:
        print("  ✓ Basic Scans")
    if args.all or args.adaptive:
        print("  ✓ Adaptive Scans")
    if args.all or args.timeseries:
        print("  ✓ Time Series")
    if args.all or args.peaks:
        print("  ✓ Peak Finding")
    if args.all or args.multidevice:
        print("  ✓ Multi-Device Coordination")
    if args.all or args.grid:
        print("  ✓ 2D Grid Scan")

    print("\nData saved to: data/documents/")
    print("\nTo analyze the results:")
    print("  from databroker import Broker")
    print("  db = Broker.named('temp')")
    print("  runs = list(db.search(since='today'))")
    print("  print(f'Collected {len(runs)} runs')")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
