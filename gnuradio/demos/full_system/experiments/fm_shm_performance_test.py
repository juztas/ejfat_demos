#!/usr/bin/env python3
"""
FM SHM Performance Test Experiment

Tests the EJFAT shared memory buffer performance under various load conditions.
Useful for characterizing buffer behavior, detecting overruns/underruns, and
validating system performance.

This experiment demonstrates:
- Shared memory buffer stress testing
- Performance characterization at different sweep rates
- Overrun/underrun detection
- Long-duration stability testing

Usage:
    python experiments/fm_shm_performance_test.py [OPTIONS]

Examples:
    # Normal 5-minute test
    python experiments/fm_shm_performance_test.py

    # Stress test with rapid frequency changes
    python experiments/fm_shm_performance_test.py --sweep-rate stress --duration 600

    # Long-duration stability test
    python experiments/fm_shm_performance_test.py --sweep-rate slow --duration 3600
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from databroker import Broker

from bluesky_config.devices_fm_shm import FMSHMBeamline
from bluesky_config.plans_fm_shm import shm_performance_test
from bluesky_config.callbacks_fm_shm import BufferHealthCallback
from bluesky_config.metadata import create_experiment_metadata
from config import CATALOG_NAME


def run_performance_test(duration=300, sweep_rate='normal'):
    """
    Run SHM performance test experiment.

    Parameters
    ----------
    duration : float
        Test duration (seconds)
    sweep_rate : str
        Sweep rate: 'slow', 'normal', 'fast', 'stress'

    Returns
    -------
    str
        Run UID for data retrieval
    """
    # Sweep rate descriptions
    rate_descriptions = {
        'slow': '10 frequencies, 1.0s dwell - Light load',
        'normal': '20 frequencies, 0.5s dwell - Normal operation',
        'fast': '50 frequencies, 0.2s dwell - High load',
        'stress': '100 frequencies, 0.1s dwell - Maximum stress',
    }

    print("=" * 70)
    print("FM SHM PERFORMANCE TEST")
    print("=" * 70)
    print(f"\nTest Parameters:")
    print(f"  Duration: {duration}s ({duration/60:.1f} min)")
    print(f"  Sweep rate: {sweep_rate}")
    print(f"  Description: {rate_descriptions[sweep_rate]}")
    print()

    # Setup RunEngine
    print("[1/5] Setting up Bluesky RunEngine...")
    RE = RunEngine({})

    # Setup DataBroker
    print("[2/5] Setting up DataBroker...")
    try:
        db = Broker.named(CATALOG_NAME)
        RE.subscribe(db.insert)
        print(f"  ✓ Using catalog: {CATALOG_NAME}")
    except Exception:
        print("  ✓ Using temporary in-memory catalog")
        db = Broker.named('temp')
        RE.subscribe(db.insert)

    # Setup callbacks
    print("[3/5] Setting up live callbacks...")

    bec = BestEffortCallback()
    RE.subscribe(bec)
    print("  ✓ BestEffortCallback")

    # Buffer health with strict thresholds for performance test
    buffer_health = BufferHealthCallback(
        overrun_threshold=1,  # Alert on first overrun
        underrun_threshold=1,  # Alert on first underrun
        fill_high_threshold=85,  # Alert if >85% full
        fill_low_threshold=15,  # Alert if <15% full
    )
    RE.subscribe(buffer_health)
    print("  ✓ BufferHealthCallback (strict thresholds)")

    # Create FM beamline
    print("\n[4/5] Initializing FM SHM Beamline...")
    beamline = FMSHMBeamline(name='fm_shm')

    try:
        # Start beamline (TX only for performance test)
        print("[5/5] Starting beamline flowgraphs...")
        beamline.startup(start_rx=False)

        # Create metadata
        md = create_experiment_metadata(
            experiment_id='FM-PERF-001',
            purpose='Test shared memory buffer performance',
            plan_type='shm_performance_test',
            duration=duration,
            sweep_rate=sweep_rate,
            beamline='fm_shm',
        )

        # Run the experiment
        print("\n[6/6] Running performance test...")
        print("=" * 70)
        print("\n⚠️  MONITOR FOR:")
        print("  - Buffer overruns (data loss)")
        print("  - Buffer underruns (starvation)")
        print("  - Abnormal buffer fill levels")
        print()

        uid = RE(shm_performance_test(
            beamline,
            test_duration=duration,
            sweep_rate=sweep_rate,
        ), **md)

        print("\n" + "=" * 70)
        print("PERFORMANCE TEST COMPLETE!")
        print("=" * 70)

        print(f"\nRun UID: {uid[0][:8]}...")
        print(f"Data saved to catalog: {CATALOG_NAME}")

        return uid[0]

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return None

    except Exception as e:
        print(f"\n\n✗ Test failed: {e}")
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
        description='FM SHM Performance Test Experiment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Sweep Rates:
  slow    - 10 frequencies, 1.0s dwell (light load)
  normal  - 20 frequencies, 0.5s dwell (normal operation)
  fast    - 50 frequencies, 0.2s dwell (high load)
  stress  - 100 frequencies, 0.1s dwell (maximum stress)

Examples:
  # Normal 5-minute test
  python experiments/fm_shm_performance_test.py

  # 10-minute stress test
  python experiments/fm_shm_performance_test.py --sweep-rate stress --duration 600

  # 1-hour stability test
  python experiments/fm_shm_performance_test.py --sweep-rate slow --duration 3600
        """
    )

    parser.add_argument(
        '--duration',
        type=float,
        default=300,
        help='Test duration in seconds (default: 300 = 5 minutes)'
    )

    parser.add_argument(
        '--sweep-rate',
        choices=['slow', 'normal', 'fast', 'stress'],
        default='normal',
        help='Sweep rate for load testing (default: normal)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.duration < 10:
        print("Error: --duration must be at least 10 seconds")
        return 1

    # Run experiment
    uid = run_performance_test(
        duration=args.duration,
        sweep_rate=args.sweep_rate,
    )

    return 0 if uid else 1


if __name__ == "__main__":
    sys.exit(main())
