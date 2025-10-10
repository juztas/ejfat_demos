#!/usr/bin/env python3
"""
FM Band Survey Experiment

Performs a comprehensive survey of the FM band (88-108 MHz) to identify
active stations in the Ottawa area. Uses the FM SHM beamline with automatic
station detection and signal quality monitoring.

This experiment demonstrates:
- Full band frequency sweep
- Automatic station detection
- Buffer health monitoring
- Data persistence via DataBroker
- Live feedback callbacks

Usage:
    python experiments/fm_band_survey.py [--num-points NUM] [--dwell-time SEC]

Example:
    # Quick survey (100 points, 0.3s dwell)
    python experiments/fm_band_survey.py --num-points 100 --dwell-time 0.3

    # Detailed survey (500 points, 1.0s dwell)
    python experiments/fm_band_survey.py --num-points 500 --dwell-time 1.0
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from databroker import Broker

from bluesky_config.devices_fm_shm import FMSHMBeamline
from bluesky_config.plans_fm_shm import fm_band_sweep
from bluesky_config.callbacks_fm_shm import (
    BufferHealthCallback,
    StationFinderCallback,
    ScanProgressCallback,
)
from bluesky_config.metadata import create_experiment_metadata
from config import CATALOG_NAME


def run_fm_band_survey(num_points=200, dwell_time=0.5, start_rx=False):
    """
    Run FM band survey experiment.

    Parameters
    ----------
    num_points : int
        Number of frequency points to scan
    dwell_time : float
        Time to dwell at each frequency (seconds)
    start_rx : bool
        Whether to start receiver (for audio monitoring)

    Returns
    -------
    str
        Run UID for data retrieval
    """
    print("=" * 70)
    print("FM BAND SURVEY EXPERIMENT")
    print("=" * 70)
    print(f"\nParameters:")
    print(f"  Frequency range: 88.0 - 108.0 MHz")
    print(f"  Number of points: {num_points}")
    print(f"  Dwell time: {dwell_time}s per point")
    print(f"  Total duration: ~{num_points * dwell_time:.0f}s ({num_points * dwell_time / 60:.1f} min)")
    print(f"  Receiver: {'enabled' if start_rx else 'disabled (TX only)'}")
    print()

    # Setup RunEngine
    print("[1/6] Setting up Bluesky RunEngine...")
    RE = RunEngine({})

    # Setup DataBroker
    print("[2/6] Setting up DataBroker...")
    try:
        db = Broker.named(CATALOG_NAME)
        RE.subscribe(db.insert)
        print(f"  ✓ Using catalog: {CATALOG_NAME}")
    except Exception as e:
        print(f"  ⚠️  Could not load catalog '{CATALOG_NAME}': {e}")
        print("  ✓ Using temporary in-memory catalog")
        db = Broker.named('temp')
        RE.subscribe(db.insert)

    # Setup callbacks
    print("[3/6] Setting up live callbacks...")

    # Best effort callback for basic feedback (disable plots on macOS to avoid threading issues)
    bec = BestEffortCallback()
    bec.disable_plots()  # Disable matplotlib plots to avoid NSWindow threading crashes on macOS
    RE.subscribe(bec)
    print("  ✓ BestEffortCallback (plots disabled for macOS compatibility)")

    # Buffer health monitoring
    buffer_health = BufferHealthCallback(
        overrun_threshold=10,
        underrun_threshold=10,
        fill_high_threshold=90,
        fill_low_threshold=10,
    )
    RE.subscribe(buffer_health)
    print("  ✓ BufferHealthCallback")

    # Station finder with lower threshold for detection
    station_finder = StationFinderCallback(
        power_threshold=-60,  # dBm
        show_live=True,
    )
    RE.subscribe(station_finder)
    print("  ✓ StationFinderCallback")

    # Progress tracking
    progress = ScanProgressCallback(
        expected_points=num_points,
        update_interval=max(1, num_points // 20),  # 5% updates
    )
    RE.subscribe(progress)
    print("  ✓ ScanProgressCallback")

    # Create FM beamline
    print("\n[4/6] Initializing FM SHM Beamline...")
    beamline = FMSHMBeamline(name='fm_shm')

    try:
        # Start beamline
        print("[5/6] Starting beamline flowgraphs...")
        beamline.startup(start_rx=start_rx)

        if not beamline.ready:
            print("\n⚠️  WARNING: Beamline not ready!")
            print("  Transmitter may not be running or connected.")
            print("  Continuing anyway (simulation mode)...")

        # Create metadata
        md = create_experiment_metadata(
            experiment_id='FM-SURVEY-001',
            purpose='Survey Ottawa FM band for active stations',
            plan_type='fm_band_sweep',
            num_points=num_points,
            dwell_time=dwell_time,
            beamline='fm_shm',
            location='Ottawa',
        )

        # Run the experiment
        print("\n[6/6] Running FM band sweep...")
        print("=" * 70)

        uid = RE(fm_band_sweep(
            beamline,
            start=88e6,
            stop=108e6,
            num=num_points,
            dwell_time=dwell_time
        ), **md)

        print("\n" + "=" * 70)
        print("EXPERIMENT COMPLETE!")
        print("=" * 70)

        # Print summary
        print(f"\nRun UID: {uid[0][:8]}...")
        print(f"Stations found: {len(station_finder.stations_found)}")

        if station_finder.stations_found:
            print("\nDetected Stations:")
            for station in sorted(station_finder.stations_found,
                                key=lambda x: x['frequency']):
                name = station.get('name', 'Unknown')
                freq_mhz = station['frequency_mhz']
                power = station['power']
                print(f"  {freq_mhz:6.1f} MHz  ({power:+6.1f} dBm)  - {name}")

        print(f"\nData saved to catalog: {CATALOG_NAME}")
        print(f"Retrieve with: db['{uid[0][:8]}']")

        return uid[0]

    except KeyboardInterrupt:
        print("\n\n⚠️  Experiment interrupted by user")
        return None

    except Exception as e:
        print(f"\n\n✗ Experiment failed: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        # Cleanup
        print("\n" + "=" * 70)
        print("CLEANUP")
        print("=" * 70)
        beamline.shutdown()
        print("\nBeamline shutdown complete.")


def main():
    """Main entry point with command-line arguments."""
    parser = argparse.ArgumentParser(
        description='FM Band Survey Experiment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick survey (default)
  python experiments/fm_band_survey.py

  # Detailed survey
  python experiments/fm_band_survey.py --num-points 500 --dwell-time 1.0

  # Fast survey
  python experiments/fm_band_survey.py --num-points 100 --dwell-time 0.2

  # Survey with receiver enabled (for audio monitoring)
  python experiments/fm_band_survey.py --with-receiver
        """
    )

    parser.add_argument(
        '--num-points',
        type=int,
        default=200,
        help='Number of frequency points to scan (default: 200)'
    )

    parser.add_argument(
        '--dwell-time',
        type=float,
        default=0.5,
        help='Dwell time at each frequency in seconds (default: 0.5)'
    )

    parser.add_argument(
        '--with-receiver',
        action='store_true',
        help='Start receiver flowgraph (enables audio output)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.num_points < 10:
        print("Error: --num-points must be at least 10")
        return 1

    if args.dwell_time < 0.1:
        print("Error: --dwell-time must be at least 0.1 seconds")
        return 1

    # Run experiment
    uid = run_fm_band_survey(
        num_points=args.num_points,
        dwell_time=args.dwell_time,
        start_rx=args.with_receiver,
    )

    return 0 if uid else 1


if __name__ == "__main__":
    sys.exit(main())
