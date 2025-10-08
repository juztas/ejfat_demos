#!/usr/bin/env python3
"""
Ottawa FM Radio Station Quick Test

Quick test with just 5 Ottawa FM stations to verify functionality.
"""

import subprocess
import time
import sys
import os
import signal
import xmlrpc.client
import argparse
from pathlib import Path

# Select 5 representative Ottawa FM stations
OTTAWA_FM_STATIONS = [
    {"freq": 89.9, "name": "CIHT Hot 89.9", "format": "Top 40"},
    {"freq": 93.9, "name": "CIMF FREQ 93.9", "format": "Francophone"},
    {"freq": 98.5, "name": "CFMO EZ Rock", "format": "Adult Contemporary"},
    {"freq": 102.5, "name": "CIDV Move 102.5", "format": "Rhythmic CHR"},
    {"freq": 106.1, "name": "CHEZ-FM", "format": "Classic Rock"},
]

# Default Configuration
TRANSMITTER_STARTUP_TIME = 5  # seconds
RECEIVER_STARTUP_TIME = 3     # seconds
DEFAULT_DWELL_TIME = 10       # seconds per frequency (default)
XMLRPC_HOST = "localhost"
XMLRPC_PORT = 8080

# Process tracking
transmitter_proc = None
receiver_proc = None


def cleanup():
    """Kill any running GNU Radio processes."""
    subprocess.run(["pkill", "-9", "-f", "fm_transmitter_shm.py"],
                   stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "-f", "fm_receiver_shm.py"],
                   stderr=subprocess.DEVNULL)
    time.sleep(1)


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\nInterrupted - cleaning up...")
    cleanup()
    sys.exit(0)


def start_transmitter():
    """Start FM transmitter."""
    global transmitter_proc

    print("\n" + "="*70)
    print("Starting FM Transmitter...")
    print("="*70)

    fm_dir = Path(__file__).parent / "fm"
    tx_script = fm_dir / "fm_transmitter_shm.py"

    transmitter_proc = subprocess.Popen(
        ["python", str(tx_script)],
        cwd=str(fm_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )

    print(f"Transmitter starting (PID: {transmitter_proc.pid})...")
    for i in range(TRANSMITTER_STARTUP_TIME):
        time.sleep(1)
        print(f"  {i+1}/{TRANSMITTER_STARTUP_TIME}", end="\r")
    print(f"\n✓ Transmitter ready")


def start_receiver():
    """Start FM receiver."""
    global receiver_proc

    print("\n" + "="*70)
    print("Starting FM Receiver...")
    print("="*70)

    fm_dir = Path(__file__).parent / "fm"
    rx_script = fm_dir / "fm_receiver_shm.py"

    receiver_proc = subprocess.Popen(
        ["python", str(rx_script)],
        cwd=str(fm_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )

    print(f"Receiver starting (PID: {receiver_proc.pid})...")
    for i in range(RECEIVER_STARTUP_TIME):
        time.sleep(1)
        print(f"  {i+1}/{RECEIVER_STARTUP_TIME}", end="\r")
    print(f"\n✓ Receiver ready")


def test_connection():
    """Test XML-RPC connection."""
    print("\n" + "="*70)
    print("Testing Connection...")
    print("="*70)

    try:
        rpc = xmlrpc.client.ServerProxy(f'http://{XMLRPC_HOST}:{XMLRPC_PORT}')
        current_freq = rpc.get_freq()
        print(f"✓ Connected to http://{XMLRPC_HOST}:{XMLRPC_PORT}")
        print(f"✓ Current frequency: {current_freq/1e6:.1f} MHz")
        return rpc
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)


def run_sweep(rpc, stations, dwell_time):
    """Run frequency sweep."""
    print("\n" + "="*70)
    print(f"Sweeping {len(stations)} Ottawa FM Stations")
    print("="*70)
    print(f"Dwell time: {dwell_time} seconds per station")
    print(f"Total time: ~{len(stations) * dwell_time} seconds\n")

    for i, station in enumerate(stations, 1):
        freq_hz = station['freq'] * 1e6

        print(f"[{i}/{len(stations)}]  {station['freq']:6.1f} MHz  "
              f"{station['name']:25s}  ({station['format']})")

        try:
            rpc.set_freq(freq_hz)
            time.sleep(dwell_time)
        except Exception as e:
            print(f"  ✗ Error: {e}")
            break

    print("\n✓ Sweep complete!")


def stop_processes():
    """Stop GNU Radio processes."""
    print("\n" + "="*70)
    print("Stopping Processes...")
    print("="*70)

    if transmitter_proc:
        try:
            os.killpg(os.getpgid(transmitter_proc.pid), signal.SIGTERM)
            transmitter_proc.wait(timeout=3)
        except:
            os.killpg(os.getpgid(transmitter_proc.pid), signal.SIGKILL)
        print("✓ Transmitter stopped")

    if receiver_proc:
        try:
            os.killpg(os.getpgid(receiver_proc.pid), signal.SIGTERM)
            receiver_proc.wait(timeout=3)
        except:
            os.killpg(os.getpgid(receiver_proc.pid), signal.SIGKILL)
        print("✓ Receiver stopped")


def main():
    """Main test sequence."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Ottawa FM Radio Station Quick Test',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Use default 10s dwell time
  %(prog)s --dwell 5          # Use 5s dwell time
  %(prog)s --dwell 15         # Use 15s dwell time
        """
    )
    parser.add_argument(
        '--dwell',
        type=float,
        default=DEFAULT_DWELL_TIME,
        metavar='SECONDS',
        help=f'Dwell time per frequency in seconds (default: {DEFAULT_DWELL_TIME})'
    )
    args = parser.parse_args()

    dwell_time = args.dwell

    signal.signal(signal.SIGINT, signal_handler)

    print("\n" + "="*70)
    print("        OTTAWA FM STATION TEST (Quick - 5 stations)")
    print("="*70)
    print(f"Dwell time: {dwell_time} seconds per station")
    print(f"Total test time: ~{len(OTTAWA_FM_STATIONS) * dwell_time + 15} seconds")

    try:
        cleanup()
        start_transmitter()
        start_receiver()
        rpc = test_connection()
        run_sweep(rpc, OTTAWA_FM_STATIONS, dwell_time)

        print("\n" + "="*70)
        print("                    TEST COMPLETE!")
        print("="*70)
        print(f"✓ Swept through {len(OTTAWA_FM_STATIONS)} Ottawa FM stations")
        print(f"✓ {dwell_time} seconds per frequency")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stop_processes()


if __name__ == "__main__":
    main()
