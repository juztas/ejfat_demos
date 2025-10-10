#!/usr/bin/env python3
"""
FM Station Monitoring Experiment

Monitors a specific FM station over time to characterize signal quality,
stability, and shared memory buffer performance. Useful for long-term
monitoring and quality assessment.

This experiment demonstrates:
- Time-series data collection
- Signal quality tracking
- Buffer health monitoring over extended periods
- Statistical analysis of station characteristics

Usage:
    python experiments/fm_station_monitor.py STATION [OPTIONS]

Examples:
    # Monitor CHEZ 106.1 for 5 minutes
    python experiments/fm_station_monitor.py "CHEZ 106" --duration 300

    # Monitor specific frequency for 10 minutes with fast sampling
    python experiments/fm_station_monitor.py 98.5 --duration 600 --interval 0.5

    # Monitor CBC Radio One for 1 hour
    python experiments/fm_station_monitor.py "CBC Radio One" --duration 3600
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from databroker import Broker

from bluesky_config.devices_fm_shm import FMSHMBeamline
from bluesky_config.plans_fm_shm import characterize_fm_station
from bluesky_config.callbacks_fm_shm import (
    BufferHealthCallback,
    SignalQualityCallback,
    ScanProgressCallback,
)
from bluesky_config.metadata import create_experiment_metadata
from bluesky_config.fm_beamline_config import (
    get_station_frequency,
    get_station_info,
    OTTAWA_FM_STATIONS,
)
from config import CATALOG_NAME


def parse_station_input(station_input):
    """
    Parse station input (name or frequency).

    Parameters
    ----------
    station_input : str
        Station name (e.g., "CHEZ 106") or frequency in MHz (e.g., "106.1")

    Returns
    -------
    tuple
        (frequency_hz, station_name, station_info)
    """
    # Try to parse as frequency first
    try:
        freq_mhz = float(station_input)
        freq_hz = freq_mhz * 1e6

        # Check if it's in FM band
        if not (88e6 <= freq_hz <= 108e6):
            raise ValueError(f"Frequency {freq_mhz} MHz outside FM band (88-108 MHz)")

        # Try to find station info
        station_info = get_station_info(freq_hz, tolerance=100e3)
        station_name = station_info['name'] if station_info else f"{freq_mhz:.1f} MHz"

        return freq_hz, station_name, station_info

    except ValueError:
        # Not a number, try as station name
        try:
            freq_hz = get_station_frequency(station_input)
            station_info = OTTAWA_FM_STATIONS[station_input]
            return freq_hz, station_input, station_info

        except KeyError:
            # List available stations
            available = ', '.join(OTTAWA_FM_STATIONS.keys())
            raise ValueError(
                f"Unknown station: '{station_input}'\n"
                f"Available stations: {available}\n"
                f"Or provide frequency in MHz (e.g., 98.5)"
            )


def run_station_monitor(station_input, duration=300, sample_interval=1.0, start_rx=True):
    """
    Run FM station monitoring experiment.

    Parameters
    ----------
    station_input : str
        Station name or frequency (MHz)
    duration : float
        Monitoring duration (seconds)
    sample_interval : float
        Time between samples (seconds)
    start_rx : bool
        Whether to start receiver for audio monitoring

    Returns
    -------
    str
        Run UID for data retrieval
    """
    # Parse station input
    try:
        frequency, station_name, station_info = parse_station_input(station_input)
    except ValueError as e:
        print(f"Error: {e}")
        return None

    print("=" * 70)
    print("FM STATION MONITORING EXPERIMENT")
    print("=" * 70)
    print(f"\nTarget Station:")
    print(f"  Name: {station_name}")
    print(f"  Frequency: {frequency/1e6:.1f} MHz")

    if station_info:
        print(f"  Format: {station_info.get('format', 'Unknown')}")
        if 'callsign' in station_info:
            print(f"  Callsign: {station_info['callsign']}")

    num_samples = int(duration / sample_interval)
    print(f"\nMonitoring Parameters:")
    print(f"  Duration: {duration}s ({duration/60:.1f} min)")
    print(f"  Sample interval: {sample_interval}s")
    print(f"  Number of samples: {num_samples}")
    print(f"  Receiver: {'enabled' if start_rx else 'disabled (measurements only)'}")
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
    except Exception:
        print("  ✓ Using temporary in-memory catalog")
        db = Broker.named('temp')
        RE.subscribe(db.insert)

    # Setup callbacks
    print("[3/6] Setting up live callbacks...")

    bec = BestEffortCallback()
    RE.subscribe(bec)
    print("  ✓ BestEffortCallback")

    buffer_health = BufferHealthCallback()
    RE.subscribe(buffer_health)
    print("  ✓ BufferHealthCallback")

    signal_quality = SignalQualityCallback(
        window_size=min(100, num_samples),
        report_interval=max(1, num_samples // 10),  # Report every 10%
    )
    RE.subscribe(signal_quality)
    print("  ✓ SignalQualityCallback")

    progress = ScanProgressCallback(
        expected_points=num_samples,
        update_interval=max(1, num_samples // 20),
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

        # Create metadata
        md = create_experiment_metadata(
            experiment_id='FM-MONITOR-001',
            purpose=f'Monitor {station_name} signal quality over time',
            plan_type='fm_station_characterization',
            station_name=station_name,
            station_frequency=frequency,
            duration=duration,
            sample_interval=sample_interval,
            beamline='fm_shm',
        )

        # Run the experiment
        print(f"\n[6/6] Monitoring {station_name} ({frequency/1e6:.1f} MHz)...")
        print("=" * 70)

        uid = RE(characterize_fm_station(
            beamline,
            frequency=frequency,
            duration=duration,
            sample_interval=sample_interval,
        ), **md)

        print("\n" + "=" * 70)
        print("MONITORING COMPLETE!")
        print("=" * 70)

        print(f"\nRun UID: {uid[0][:8]}...")
        print(f"Samples collected: {num_samples}")
        print(f"Data saved to catalog: {CATALOG_NAME}")

        return uid[0]

    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring interrupted by user")
        return None

    except Exception as e:
        print(f"\n\n✗ Monitoring failed: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        # Cleanup
        print("\n" + "=" * 70)
        print("CLEANUP")
        print("=" * 70)
        beamline.shutdown()


def main():
    """Main entry point with command-line arguments."""
    parser = argparse.ArgumentParser(
        description='FM Station Monitoring Experiment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor CHEZ 106 for 5 minutes
  python experiments/fm_station_monitor.py "CHEZ 106" --duration 300

  # Monitor 98.5 MHz for 10 minutes with fast sampling
  python experiments/fm_station_monitor.py 98.5 --duration 600 --interval 0.5

  # Long-term monitoring without receiver
  python experiments/fm_station_monitor.py "CBC Radio One" --duration 3600 --no-receiver

Available stations:
{}
        """.format('\n'.join(f"  - {name}" for name in OTTAWA_FM_STATIONS.keys()))
    )

    parser.add_argument(
        'station',
        help='Station name (e.g., "CHEZ 106") or frequency in MHz (e.g., 98.5)'
    )

    parser.add_argument(
        '--duration',
        type=float,
        default=300,
        help='Monitoring duration in seconds (default: 300 = 5 minutes)'
    )

    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        help='Sample interval in seconds (default: 1.0)'
    )

    parser.add_argument(
        '--no-receiver',
        action='store_true',
        help='Do not start receiver (measurements only, no audio)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.duration < 10:
        print("Error: --duration must be at least 10 seconds")
        return 1

    if args.interval < 0.1:
        print("Error: --interval must be at least 0.1 seconds")
        return 1

    # Run experiment
    uid = run_station_monitor(
        station_input=args.station,
        duration=args.duration,
        sample_interval=args.interval,
        start_rx=not args.no_receiver,
    )

    return 0 if uid else 1


if __name__ == "__main__":
    sys.exit(main())
