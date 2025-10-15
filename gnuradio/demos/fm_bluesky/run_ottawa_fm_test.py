#!/usr/bin/env python3
"""
Ottawa FM Radio Station Test Script

This script:
1. Starts the GNU Radio FM transmitter (waits for startup)
2. Starts the GNU Radio FM receiver
3. Sweeps through actual Ottawa FM radio station frequencies
4. Each frequency dwells for 5 seconds
5. Uses Bluesky for robust control

Ottawa FM Radio Stations:
"""

import subprocess
import time
import sys
import os
import signal
import xmlrpc.client
import argparse
from pathlib import Path

# Ottawa FM Radio Stations (frequencies in MHz)
OTTAWA_FM_STATIONS = [
    {"freq": 88.5, "name": "CILV Live 88.5", "format": "Adult Contemporary"},
    {"freq": 89.1, "name": "CHUO", "format": "Campus/Community"},
    {"freq": 89.9, "name": "CIHT Hot 89.9", "format": "Top 40"},
    {"freq": 90.7, "name": "CBOF ICI Première", "format": "CBC French"},
    {"freq": 91.5, "name": "CBO CBC Radio One", "format": "CBC English"},
    {"freq": 92.3, "name": "CJET Wow FM", "format": "Adult Hits"},
    {"freq": 93.1, "name": "CKCU", "format": "Community Radio"},
    {"freq": 93.9, "name": "CIMF FREQ 93.9", "format": "Francophone"},
    {"freq": 94.5, "name": "CBOX-FM CBC Music", "format": "Classical"},
    {"freq": 95.7, "name": "CKBY Y95.7", "format": "Country"},
    {"freq": 96.3, "name": "CJOT Majic 96.3", "format": "Adult Contemporary"},
    {"freq": 97.1, "name": "CHLX Rythme FM", "format": "Adult Contemporary French"},
    {"freq": 97.9, "name": "CKQB BIG 97.9", "format": "Classic Hits"},
    {"freq": 98.5, "name": "CFMO EZ Rock", "format": "Adult Contemporary"},
    {"freq": 99.7, "name": "CKKL Bob FM", "format": "Adult Hits"},
    {"freq": 100.3, "name": "CHEZ The Bear", "format": "Classic Rock"},
    {"freq": 101.1, "name": "CKBY Kiss FM", "format": "Hot AC"},
    {"freq": 102.5, "name": "CIDV Move 102.5", "format": "Rhythmic CHR"},
    {"freq": 103.3, "name": "CHUO", "format": "Campus"},
    {"freq": 104.7, "name": "CFFX The New", "format": "Country"},
    {"freq": 105.3, "name": "CKSI K105.3", "format": "Hits"},
    {"freq": 106.1, "name": "CHEZ-FM", "format": "Classic Rock"},
    {"freq": 106.9, "name": "CJOT Star 106.9", "format": "Hot AC"},
]

# Default Configuration
TRANSMITTER_STARTUP_TIME = 5  # seconds to wait for transmitter
RECEIVER_STARTUP_TIME = 3     # seconds to wait for receiver
DEFAULT_DWELL_TIME = 5        # seconds per frequency (default)
XMLRPC_HOST = "localhost"
XMLRPC_PORT = 8080

# Process tracking
transmitter_proc = None
receiver_proc = None


def cleanup_processes():
    """Kill any running GNU Radio processes."""
    print("\n" + "="*70)
    print("Cleaning up existing GNU Radio processes...")
    print("="*70)

    subprocess.run(["pkill", "-9", "-f", "fm_transmitter_shm.py"],
                   stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "-f", "fm_receiver_shm.py"],
                   stderr=subprocess.DEVNULL)
    time.sleep(1)
    print("✓ Cleanup complete\n")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n" + "="*70)
    print("Interrupted by user - cleaning up...")
    print("="*70)
    stop_gnuradio()
    sys.exit(0)


def start_transmitter():
    """Start the FM transmitter."""
    global transmitter_proc

    print("="*70)
    print("Starting FM Transmitter...")
    print("="*70)

    fm_dir = Path(__file__).parent.parent / "fm"
    tx_script = fm_dir / "fm_transmitter_shm.py"

    if not tx_script.exists():
        print(f"✗ Transmitter script not found: {tx_script}")
        sys.exit(1)

    # Start transmitter in background
    transmitter_proc = subprocess.Popen(
        ["python", str(tx_script)],
        cwd=str(fm_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid  # Create new process group for clean killall
    )

    print(f"Started transmitter (PID: {transmitter_proc.pid})")
    print(f"Waiting {TRANSMITTER_STARTUP_TIME} seconds for initialization...")

    for i in range(TRANSMITTER_STARTUP_TIME):
        time.sleep(1)
        if transmitter_proc.poll() is not None:
            print(f"\n✗ Transmitter crashed during startup!")
            _, stderr = transmitter_proc.communicate()
            print(stderr.decode()[-500:])  # Last 500 chars
            sys.exit(1)
        print(f"  {i+1}/{TRANSMITTER_STARTUP_TIME}...", end="\r")

    print(f"\n✓ Transmitter ready\n")
    return transmitter_proc


def start_receiver():
    """Start the FM receiver."""
    global receiver_proc

    print("="*70)
    print("Starting FM Receiver...")
    print("="*70)

    fm_dir = Path(__file__).parent.parent / "fm"
    rx_script = fm_dir / "fm_receiver_shm.py"

    if not rx_script.exists():
        print(f"✗ Receiver script not found: {rx_script}")
        sys.exit(1)

    # Start receiver in background
    receiver_proc = subprocess.Popen(
        ["python", str(rx_script)],
        cwd=str(fm_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )

    print(f"Started receiver (PID: {receiver_proc.pid})")
    print(f"Waiting {RECEIVER_STARTUP_TIME} seconds for initialization...")

    for i in range(RECEIVER_STARTUP_TIME):
        time.sleep(1)
        if receiver_proc.poll() is not None:
            print(f"\n✗ Receiver crashed during startup!")
            _, stderr = receiver_proc.communicate()
            print(stderr.decode()[-500:])
            sys.exit(1)
        print(f"  {i+1}/{RECEIVER_STARTUP_TIME}...", end="\r")

    print(f"\n✓ Receiver ready\n")
    return receiver_proc


def test_connection():
    """Test XML-RPC connection to transmitter."""
    print("="*70)
    print("Testing XML-RPC Connection...")
    print("="*70)

    try:
        rpc = xmlrpc.client.ServerProxy(f'http://{XMLRPC_HOST}:{XMLRPC_PORT}')
        current_freq = rpc.get_freq()
        print(f"✓ Connected to transmitter at http://{XMLRPC_HOST}:{XMLRPC_PORT}")
        print(f"✓ Current frequency: {current_freq/1e6:.1f} MHz\n")
        return rpc
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nMake sure the FM transmitter has an XML-RPC server block configured.")
        sys.exit(1)


def run_bluesky_sweep(stations, dwell_time):
    """Run frequency sweep using Bluesky."""
    print("="*70)
    print("Running Bluesky FM Station Sweep")
    print("="*70)
    print(f"Sweeping through {len(stations)} Ottawa FM stations")
    print(f"Dwell time: {dwell_time} seconds per station")
    print(f"Total time: ~{len(stations) * dwell_time} seconds")
    print("\nPress Ctrl+C to stop")
    print("="*70)
    print()

    try:
        # Try importing Bluesky
        from bluesky import RunEngine
        from bluesky import plan_stubs as bps
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "widget"))
        from gnuradio_bluesky.gnuradio_device import GNURadioSignalGenerator

        print("✓ Bluesky modules imported")

        # Create FM transmitter device
        class FMTransmitter(GNURadioSignalGenerator):
            """Ophyd device for FM transmitter with freq instead of frequency."""
            def _connect(self):
                """Override to test get_freq instead of get_frequency."""
                try:
                    url = f'http://{self._host}:{self._port}'
                    self._rpc_client = xmlrpc.client.ServerProxy(url)
                    # Test connection with get_freq (FM transmitter uses this)
                    current_freq = self._rpc_client.get_freq()
                    self._connected = True
                    print(f"  Current frequency: {current_freq/1e6:.1f} MHz")
                except Exception as e:
                    self._connected = False
                    raise ConnectionError(
                        f"Failed to connect to GNU Radio XML-RPC server at "
                        f"{self._host}:{self._port}: {e}"
                    )

            def __init__(self, *args, **kwargs):
                # Store host/port before calling parent __init__
                self._host = kwargs.get('host', 'localhost')
                self._port = kwargs.get('port', 8080)
                self._timeout = kwargs.get('timeout', 5.0)
                self._rpc_client = None
                self._connected = False

                # Connect first
                self._connect()

                # Now call parent __init__ but skip its _connect call
                # by temporarily replacing _connect
                original_connect = self._connect
                self._connect = lambda: None

                # Import needed for parent __init__
                import xmlrpc.client
                from gnuradio_bluesky.xml_rpc_signal import XMLRPCSignal

                # Initialize Device parent
                from ophyd import Device
                Device.__init__(self, '', name=kwargs.get('name', 'fm_tx'))

                # Create frequency signal with get_freq/set_freq
                freq_signal = XMLRPCSignal(
                    self._rpc_client,
                    'get_freq',  # Use get_freq instead of get_frequency
                    'set_freq',  # Use set_freq instead of set_frequency
                    name=f"{kwargs.get('name', 'fm_tx')}_frequency",
                    value=self._rpc_client.get_freq(),
                    kind='hinted'
                )
                freq_signal._parent = self
                self.frequency = freq_signal

                # Restore original _connect
                self._connect = original_connect

        fm_tx = FMTransmitter('', name='fm_tx',
                             host=XMLRPC_HOST, port=XMLRPC_PORT)
        print(f"✓ Connected to FM transmitter")

        # Create RunEngine
        RE = RunEngine({})
        print("✓ RunEngine created\n")

        # Run the sweep
        print("Starting sweep...\n")

        for i, station in enumerate(stations, 1):
            freq_hz = station['freq'] * 1e6

            print(f"[{i:3d}/{len(stations)}]  {station['freq']:6.1f} MHz  "
                  f"{station['name']:30s}  ({station['format']})")

            # Set frequency using Bluesky
            RE(bps.abs_set(fm_tx.frequency, freq_hz, wait=True))

            # Dwell
            time.sleep(dwell_time)

        print("\n✓ Bluesky sweep completed!\n")

    except ImportError as e:
        print(f"✗ Bluesky not available: {e}")
        print("\nFalling back to simple XML-RPC sweep...\n")
        run_simple_sweep(stations, dwell_time)


def run_simple_sweep(stations, dwell_time):
    """Run frequency sweep using simple XML-RPC (fallback)."""
    print("="*70)
    print("Running Simple XML-RPC FM Station Sweep")
    print("="*70)
    print(f"Sweeping through {len(stations)} Ottawa FM stations")
    print(f"Dwell time: {dwell_time} seconds per station")
    print("\nPress Ctrl+C to stop")
    print("="*70)
    print()

    rpc = xmlrpc.client.ServerProxy(f'http://{XMLRPC_HOST}:{XMLRPC_PORT}')

    for i, station in enumerate(stations, 1):
        freq_hz = station['freq'] * 1e6

        print(f"[{i:3d}/{len(stations)}]  {station['freq']:6.1f} MHz  "
              f"{station['name']:30s}  ({station['format']})")

        try:
            rpc.set_freq(freq_hz)
            time.sleep(dwell_time)
        except Exception as e:
            print(f"  ✗ Error setting frequency: {e}")
            break

    print("\n✓ Simple sweep completed!\n")


def stop_gnuradio():
    """Stop GNU Radio processes."""
    global transmitter_proc, receiver_proc

    print("="*70)
    print("Stopping GNU Radio Processes...")
    print("="*70)

    if transmitter_proc:
        print(f"Stopping transmitter (PID: {transmitter_proc.pid})...")
        try:
            os.killpg(os.getpgid(transmitter_proc.pid), signal.SIGTERM)
            transmitter_proc.wait(timeout=3)
        except:
            os.killpg(os.getpgid(transmitter_proc.pid), signal.SIGKILL)
        print("✓ Transmitter stopped")

    if receiver_proc:
        print(f"Stopping receiver (PID: {receiver_proc.pid})...")
        try:
            os.killpg(os.getpgid(receiver_proc.pid), signal.SIGTERM)
            receiver_proc.wait(timeout=3)
        except:
            os.killpg(os.getpgid(receiver_proc.pid), signal.SIGKILL)
        print("✓ Receiver stopped")

    print("✓ All processes stopped\n")


def main():
    """Main test sequence."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Ottawa FM Radio Station Test (Full 23 stations)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Use default 5s dwell time
  %(prog)s --dwell 10         # Use 10s dwell time
  %(prog)s --dwell 2          # Use 2s dwell time (fast sweep)
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

    # Enforce minimum dwell time to prevent GNU Radio segfaults
    if dwell_time < 1.0:
        print(f"\n⚠️  WARNING: Dwell time {dwell_time}s is too short!")
        print("   GNU Radio can segfault if frequency is changed faster than 1s")
        print("   Using minimum dwell time of 1.0s instead.\n")
        dwell_time = 1.0

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    print("\n" + "="*70)
    print(" "*15 + "OTTAWA FM RADIO STATION TEST")
    print("="*70)
    print()
    print(f"This test will sweep through {len(OTTAWA_FM_STATIONS)} Ottawa FM stations")
    print(f"Dwell time: {dwell_time} seconds per station")
    print(f"Total test time: ~{len(OTTAWA_FM_STATIONS) * dwell_time + 15} seconds")
    print()

    try:
        # Step 1: Clean up any existing processes
        cleanup_processes()

        # Step 2: Start transmitter
        start_transmitter()

        # Step 3: Start receiver
        start_receiver()

        # Step 4: Test connection
        test_connection()

        # Step 5: Run sweep
        run_bluesky_sweep(OTTAWA_FM_STATIONS, dwell_time)

        # Success!
        print("="*70)
        print(" "*20 + "TEST COMPLETE!")
        print("="*70)
        print(f"✓ Transmitter started successfully")
        print(f"✓ Receiver started successfully")
        print(f"✓ Swept through {len(OTTAWA_FM_STATIONS)} Ottawa FM stations")
        print(f"✓ {dwell_time} seconds per frequency")
        print("="*70)
        print()

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always clean up
        stop_gnuradio()


if __name__ == "__main__":
    main()
