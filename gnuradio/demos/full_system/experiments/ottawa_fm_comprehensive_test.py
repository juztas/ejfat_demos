#!/usr/bin/env python3
"""
Comprehensive Ottawa FM Station Test

Plays 15-second samples from all known Ottawa FM stations.
Based on Wikipedia list of Ottawa FM radio stations (2025).

Usage:
    python experiments/ottawa_fm_comprehensive_test.py [--sample-time SECONDS]

Example:
    # Default 15-second samples
    python experiments/ottawa_fm_comprehensive_test.py

    # Custom 10-second samples
    python experiments/ottawa_fm_comprehensive_test.py --sample-time 10
"""

import sys
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky_config.devices_fm_shm import FMSHMBeamline

# Complete list of Ottawa FM stations from Wikipedia
# Source: https://en.wikipedia.org/wiki/List_of_radio_stations_in_Ontario
OTTAWA_FM_STATIONS_COMPREHENSIVE = [
    # Frequency, Call Sign, Format, Owner
    (88.5e6, "CILV-FM", "Live 88.5", "Modern Rock", "Stingray Digital"),
    (89.1e6, "CHUO-FM", "CHUO 89.1", "Campus Radio", "University of Ottawa"),
    (89.9e6, "CIHT-FM", "Hot 89.9", "CHR/Top 40", "Stingray Digital"),
    (90.7e6, "CBOF-FM", "Ici Première", "News/Talk (French)", "Radio-Canada"),
    (91.5e6, "CBO-FM", "CBC Radio One", "News/Talk", "CBC"),
    (92.7e6, "CJVN-FM", "CJVN 92.7", "Christian (French)", "OBCI"),
    (93.1e6, "CKCU-FM", "CKCU 93.1", "Campus Radio", "Carleton University"),
    (93.9e6, "CKKL-FM", "Bob FM", "Country", "Bell Media"),
    (94.5e6, "CJFO-FM", "TSN 1200", "Sports", "Bell Media"),
    (97.9e6, "CJLL-FM", "Radio Canada International", "Multilingual", "CHIN"),
    (98.5e6, "CITM-FM", "Move 98.5", "Adult Contemporary", "Rogers"),
    (99.1e6, "CHRI-FM", "CHRI 99.1", "Christian Radio", "Christian Hit Radio"),
    (99.7e6, "CJOT-FM", "Boom 99.7", "Classic Hits", "Corus Entertainment"),
    (100.3e6, "CJMJ-FM", "Majic 100", "Adult Contemporary", "Bell Media"),
    (101.7e6, "CIDG-FM", "Dawg FM 101.9", "Mainstream Rock", "Rogers"),
    (102.5e6, "CBOX-FM", "Ici Musique", "Music (French)", "Radio-Canada"),
    (103.3e6, "CBOQ-FM", "CBC Music", "Public Music", "CBC"),
    (105.3e6, "CISS-FM", "Kiss FM", "Hot AC", "Rogers Communications"),
    (106.1e6, "CHEZ-FM", "CHEZ 106", "Classic Rock", "Rogers Communications"),
    (106.9e6, "CKQB-FM", "Jump 106.9", "Top 40/CHR", "Corus Entertainment"),
    (107.9e6, "CKDJ-FM", "CKDJ 107.9", "Campus Radio", "Algonquin College"),
]


def run_comprehensive_test(sample_time=15):
    """
    Play samples from all Ottawa FM stations.

    Parameters
    ----------
    sample_time : float
        Duration to play each station (seconds)

    Returns
    -------
    int
        Number of stations tested
    """
    print("=" * 80)
    print("COMPREHENSIVE OTTAWA FM STATION TEST")
    print("=" * 80)
    print(f"\nTotal stations: {len(OTTAWA_FM_STATIONS_COMPREHENSIVE)}")
    print(f"Sample time: {sample_time} seconds per station")
    print(f"Total duration: ~{len(OTTAWA_FM_STATIONS_COMPREHENSIVE) * sample_time / 60:.1f} minutes")
    print()

    # List all stations
    print("Stations to test:")
    print(f"{'Freq':>8s}  {'Call Sign':<12s}  {'Name':<25s}  {'Format':<20s}")
    print("-" * 80)
    for freq, call, name, fmt, owner in OTTAWA_FM_STATIONS_COMPREHENSIVE:
        print(f"{freq/1e6:>7.1f}  {call:<12s}  {name:<25s}  {fmt:<20s}")
    print()

    # Start beamline
    print("Starting FM beamline...")
    beamline = FMSHMBeamline(name='fm_shm')

    try:
        beamline.startup(start_rx=True)

        if not beamline.ready:
            print("\n⚠️  WARNING: Beamline not fully ready")
            print("  Transmitter may not be connected.")
            print("  Audio may not work properly.")
            response = input("\nContinue anyway? [y/N]: ")
            if response.lower() != 'y':
                print("Aborted.")
                return 0

        print("\n" + "=" * 80)
        print("STARTING STATION TOUR")
        print("=" * 80)
        print("\nYou should hear audio from each station for 15 seconds...")
        print("Press Ctrl+C to stop early.\n")

        stations_tested = 0

        for i, (freq, call, name, fmt, owner) in enumerate(OTTAWA_FM_STATIONS_COMPREHENSIVE, 1):
            print(f"\n[{i}/{len(OTTAWA_FM_STATIONS_COMPREHENSIVE)}] " + "=" * 60)
            print(f"Station: {name}")
            print(f"  Frequency: {freq/1e6:.1f} MHz")
            print(f"  Call Sign: {call}")
            print(f"  Format: {fmt}")
            print(f"  Owner: {owner}")
            print(f"\nTuning... ", end='', flush=True)

            # Tune to frequency
            beamline.transmitter.set_frequency(freq)
            time.sleep(0.5)  # Let it settle

            # Verify frequency
            current_freq = beamline.transmitter.get_frequency()
            print(f"✓ Confirmed: {current_freq/1e6:.1f} MHz")

            # Listen
            print(f"Listening for {sample_time} seconds...")

            # Show countdown
            for sec in range(int(sample_time)):
                remaining = int(sample_time) - sec
                print(f"  {remaining:2d}s remaining...", end='\r', flush=True)
                time.sleep(1)

            print(f"  {'Complete!':<20s}")
            stations_tested += 1

        print("\n" + "=" * 80)
        print("STATION TOUR COMPLETE!")
        print("=" * 80)
        print(f"\nStations tested: {stations_tested}/{len(OTTAWA_FM_STATIONS_COMPREHENSIVE)}")
        print()

        return stations_tested

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        print(f"Stations tested: {stations_tested}/{len(OTTAWA_FM_STATIONS_COMPREHENSIVE)}")
        return stations_tested

    except Exception as e:
        print(f"\n\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0

    finally:
        # Cleanup
        print("\n" + "=" * 80)
        print("CLEANUP")
        print("=" * 80)
        beamline.shutdown()
        print("\nBeamline shutdown complete.")


def main():
    """Main entry point with command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Comprehensive Ottawa FM Station Test',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
This test plays samples from all {len(OTTAWA_FM_STATIONS_COMPREHENSIVE)} known Ottawa FM stations.

Station list source: Wikipedia (2025)
https://en.wikipedia.org/wiki/List_of_radio_stations_in_Ontario

Examples:
  # Default 15-second samples
  python experiments/ottawa_fm_comprehensive_test.py

  # Quick 5-second samples (for testing)
  python experiments/ottawa_fm_comprehensive_test.py --sample-time 5

  # Extended 30-second samples
  python experiments/ottawa_fm_comprehensive_test.py --sample-time 30
        """
    )

    parser.add_argument(
        '--sample-time',
        type=float,
        default=15.0,
        help='Duration to play each station in seconds (default: 15)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.sample_time < 1:
        print("Error: --sample-time must be at least 1 second")
        return 1

    if args.sample_time > 60:
        print("Warning: sample times over 60 seconds are quite long")
        response = input("Continue? [y/N]: ")
        if response.lower() != 'y':
            return 1

    # Run test
    stations_tested = run_comprehensive_test(sample_time=args.sample_time)

    return 0 if stations_tested > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
