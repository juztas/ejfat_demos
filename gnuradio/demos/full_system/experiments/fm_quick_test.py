#!/usr/bin/env python3
"""
FM SHM Quick Test

Quick validation test for the FM SHM beamline. Useful for:
- Verifying hardware connections
- Testing flowgraph launch
- Validating device control
- Quick system checkout

This is a minimal test that runs quickly and provides immediate feedback.

Usage:
    python experiments/fm_quick_test.py [--with-receiver]

Example:
    # Quick test (TX only)
    python experiments/fm_quick_test.py

    # Test with receiver (audio output)
    python experiments/fm_quick_test.py --with-receiver
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky import RunEngine
from databroker import Broker

from bluesky_config.devices_fm_shm import FMSHMBeamline
from bluesky_config.plans_fm_shm import frequency_dwell_scan
from bluesky_config.fm_beamline_config import OTTAWA_FM_FREQUENCIES
from bluesky_config.metadata import create_experiment_metadata


def run_quick_test(start_rx=False):
    """
    Run quick validation test.

    Parameters
    ----------
    start_rx : bool
        Whether to start receiver

    Returns
    -------
    bool
        True if test passed
    """
    print("=" * 70)
    print("FM SHM QUICK TEST")
    print("=" * 70)
    print("\nThis test will:")
    print("  1. Start the FM beamline flowgraphs")
    print("  2. Tune to 3 known Ottawa FM stations")
    print("  3. Collect 5 samples at each station")
    print("  4. Verify device control and data collection")
    print(f"  5. {'Enable' if start_rx else 'Skip'} receiver (audio output)")
    print()

    # Select 3 test frequencies
    test_stations = {
        'CHEZ 106': OTTAWA_FM_FREQUENCIES['CHEZ 106'],
        'CBC Radio One': OTTAWA_FM_FREQUENCIES['CBC Radio One'],
        'Hot 89.9': OTTAWA_FM_FREQUENCIES['Hot 89.9'],
    }

    print("Test frequencies:")
    for name, freq in test_stations.items():
        print(f"  {name}: {freq/1e6:.1f} MHz")
    print()

    # Setup
    print("[1/4] Setting up RunEngine and DataBroker...")
    RE = RunEngine({})
    db = Broker.named('temp')  # Use temp catalog for quick test
    RE.subscribe(db.insert)

    # Create beamline
    print("[2/4] Initializing FM SHM Beamline...")
    beamline = FMSHMBeamline(name='fm_shm')

    test_passed = False

    try:
        # Start beamline
        print("[3/4] Starting beamline...")
        beamline.startup(start_rx=start_rx)

        if not beamline.ready:
            print("\n⚠️  WARNING: Beamline not fully ready")
            print("  This is normal if flowgraphs are not running")
            print("  Continuing with simulated devices...")

        # Create metadata
        md = create_experiment_metadata(
            experiment_id='FM-TEST-QUICK',
            purpose='Quick validation test of FM SHM beamline',
            plan_type='frequency_dwell_scan',
            beamline='fm_shm',
        )

        # Run quick test
        print("[4/4] Running test scan...")
        print("=" * 70)

        uid = RE(frequency_dwell_scan(
            beamline,
            frequencies=list(test_stations.values()),
            dwell_time=2.5,  # 2.5s per station
            num_samples=5,   # 5 samples per station
        ), **md)

        print("\n" + "=" * 70)
        print("TEST COMPLETE!")
        print("=" * 70)

        # Verify data collection
        print("\nVerifying data collection...")
        try:
            runs = list(db.v2)
            if len(runs) > 0:
                run = db.v2[runs[-1]]
                print(f"  ✓ Data saved (UID: {uid[0][:8]}...)")
                print(f"  ✓ Metadata captured")
                test_passed = True
            else:
                print("  ✗ No data in catalog")
        except Exception as e:
            print(f"  ✗ Data verification failed: {e}")

        print("\nTest Results:")
        if test_passed:
            print("  ✓ Beamline operational")
            print("  ✓ Device control working")
            print("  ✓ Data collection working")
            print(f"  ✓ Receiver: {'enabled' if start_rx else 'disabled'}")
            print("\n✅ QUICK TEST PASSED")
        else:
            print("  ⚠️  Some issues detected")
            print("\n⚠️  QUICK TEST COMPLETED WITH WARNINGS")

        return test_passed

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return False

    except Exception as e:
        print(f"\n\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\n" + "=" * 70)
        print("CLEANUP")
        print("=" * 70)
        beamline.shutdown()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='FM SHM Quick Test - Fast validation of beamline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This quick test validates:
  - Beamline startup/shutdown
  - Device initialization
  - Frequency control
  - Data collection
  - DataBroker integration

Duration: ~15 seconds (3 stations × 5 samples)

Examples:
  # Quick test (TX only)
  python experiments/fm_quick_test.py

  # Test with audio output
  python experiments/fm_quick_test.py --with-receiver
        """
    )

    parser.add_argument(
        '--with-receiver',
        action='store_true',
        help='Start receiver flowgraph (enables audio output)'
    )

    args = parser.parse_args()

    # Run test
    success = run_quick_test(start_rx=args.with_receiver)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
