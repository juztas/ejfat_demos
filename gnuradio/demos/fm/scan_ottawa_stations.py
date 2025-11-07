#!/usr/bin/env python3
"""
Scan all Ottawa FM stations using the digital detector.

This script assumes the digital detector flowgraph is already running
with XML-RPC server on localhost:8080.

Usage:
    python scan_ottawa_stations.py [--dwell SECONDS]
"""

import xmlrpc.client
import time
import argparse
import sys

# Ottawa FM Radio Stations (frequencies in MHz)
# Comprehensive list of Ottawa-Gatineau region FM stations
OTTAWA_FM_STATIONS = [
    # Canadian stations (88-108 MHz)
    {"freq": 88.5, "name": "CKCU-FM", "format": "Campus/Community", "location": "Ottawa"},
    {"freq": 89.9, "name": "CIHT-FM (Hot 89.9)", "format": "CHR/Top 40", "location": "Ottawa"},
    {"freq": 90.7, "name": "CFFX-FM (Move 90.7)", "format": "Hot AC", "location": "Kingston"},
    {"freq": 91.5, "name": "CBON-FM (CBC Radio One)", "format": "CBC French", "location": "Sudbury"},
    {"freq": 93.9, "name": "CJOT-FM (Boom 99.7)", "format": "Adult Contemporary", "location": "Ottawa"},
    {"freq": 94.5, "name": "CJMJ-FM (Majic 100)", "format": "Adult Contemporary", "location": "Ottawa"},
    {"freq": 95.7, "name": "CHEY-FM (Y95.7)", "format": "Country", "location": "Arnprior"},
    {"freq": 96.5, "name": "CKBY-FM (Y101)", "format": "Country", "location": "Smiths Falls"},
    {"freq": 97.9, "name": "CIMF-FM (NOW! 97.9)", "format": "Hot AC", "location": "Gatineau"},
    {"freq": 99.7, "name": "CKQB-FM (The Bear)", "format": "Classic Rock", "location": "Ottawa"},
    {"freq": 100.3, "name": "CKKL-FM (Bob FM)", "format": "Adult Hits", "location": "Ottawa"},
    {"freq": 101.1, "name": "CIBO-FM (CBC Radio One)", "format": "CBC English", "location": "Ottawa"},
    {"freq": 101.9, "name": "CKOI-FM", "format": "CHR/Top 40 French", "location": "Gatineau"},
    {"freq": 102.5, "name": "CFRA", "format": "News/Talk", "location": "Ottawa"},
    {"freq": 103.3, "name": "CJFO-FM (104.7 FM)", "format": "Hot AC French", "location": "Ottawa"},
    {"freq": 104.1, "name": "CJRC-FM (Rythme FM)", "format": "AC French", "location": "Gatineau"},
    {"freq": 104.7, "name": "CFFX-FM (104.7 The Wolf)", "format": "Rock", "location": "Pembroke"},
    {"freq": 105.3, "name": "CKBY-FM (Y101)", "format": "Country", "location": "Ottawa"},
    {"freq": 106.1, "name": "CHEZ-FM", "format": "Classic Rock", "location": "Ottawa"},
    {"freq": 106.9, "name": "CISS-FM (Kiss FM)", "format": "Hot AC", "location": "Ottawa"},
]

def scan_stations(dwell_time=20, host='localhost', port=8080):
    """
    Scan through all Ottawa FM stations.

    Parameters
    ----------
    dwell_time : float
        Seconds to dwell on each frequency
    host : str
        XML-RPC server hostname
    port : int
        XML-RPC server port
    """
    print("="*70)
    print("OTTAWA FM STATION SCAN - Digital Detector")
    print("="*70)
    print(f"Stations: {len(OTTAWA_FM_STATIONS)}")
    print(f"Dwell time: {dwell_time} seconds per station")
    print(f"Total time: ~{len(OTTAWA_FM_STATIONS) * dwell_time:.0f} seconds")
    print("="*70)
    print()

    # Connect to XML-RPC server
    try:
        url = f'http://{host}:{port}'
        rpc = xmlrpc.client.ServerProxy(url)

        # Test connection
        current_freq = rpc.get_freq()
        print(f"✓ Connected to digital detector at {host}:{port}")
        print(f"  Current frequency: {current_freq/1e6:.1f} MHz")
        print()
    except Exception as e:
        print(f"✗ Failed to connect to digital detector: {e}")
        print(f"\nMake sure the digital detector flowgraph is running")
        print(f"with XML-RPC server on {host}:{port}")
        sys.exit(1)

    # Scan through stations
    print("Starting scan...")
    print()

    for i, station in enumerate(OTTAWA_FM_STATIONS, 1):
        freq_hz = station['freq'] * 1e6

        print(f"[{i:2d}/{len(OTTAWA_FM_STATIONS)}]  "
              f"{station['freq']:6.1f} MHz  "
              f"{station['name']:35s}  "
              f"{station['format']:20s}  "
              f"{station['location']}")

        # Set frequency
        try:
            rpc.set_freq(freq_hz)
        except Exception as e:
            print(f"    ✗ Error setting frequency: {e}")
            continue

        # Dwell
        time.sleep(dwell_time)

    print()
    print("="*70)
    print("✓ Scan complete!")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Scan Ottawa FM stations for digital content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan_ottawa_stations.py                # Use default 20s dwell
  python scan_ottawa_stations.py --dwell 10     # Use 10s dwell
  python scan_ottawa_stations.py --dwell 30     # Use 30s dwell
        """
    )

    parser.add_argument('--dwell', type=float, default=20,
                       metavar='SECONDS',
                       help='Dwell time per frequency in seconds (default: 20)')
    parser.add_argument('--host', type=str, default='localhost',
                       help='XML-RPC server hostname (default: localhost)')
    parser.add_argument('--port', type=int, default=8080,
                       help='XML-RPC server port (default: 8080)')

    args = parser.parse_args()

    try:
        scan_stations(args.dwell, args.host, args.port)
    except KeyboardInterrupt:
        print("\n\n✗ Scan interrupted by user")
        sys.exit(0)


if __name__ == '__main__':
    main()
