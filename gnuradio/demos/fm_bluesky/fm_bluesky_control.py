#!/usr/bin/env python3
"""
Bluesky control demo for FM transmitter (fm_transmitter_shm.grc).

This script demonstrates using Bluesky to control the FM radio frequency
on the GNU Radio SDR transmitter. It can sweep through FM radio stations
and control the center frequency via XML-RPC.

Prerequisites:
    1. Start the FM transmitter flowgraph:
       cd fm/
       python fm_transmitter_shm.py
       (or open fm_transmitter_shm.grc in GNU Radio Companion)

    2. Ensure XML-RPC server is running on localhost:8080

Usage:
    # Run a frequency sweep through FM band
    python fm_bluesky_control.py --sweep

    # Set to a specific frequency
    python fm_bluesky_control.py --freq 98.5e6

    # Test the connection
    python fm_bluesky_control.py --test
"""

import sys
import time
import argparse
import xmlrpc.client
from pathlib import Path

# Add the widget directory to path to import the bluesky device
widget_path = Path(__file__).parent / "widget"
sys.path.insert(0, str(widget_path))


def test_connection(host='localhost', port=8080):
    """
    Test XML-RPC connection to FM transmitter.

    Parameters
    ----------
    host : str
        Hostname of GNU Radio XML-RPC server
    port : int
        Port of GNU Radio XML-RPC server

    Returns
    -------
    bool
        True if connection successful
    """
    print("=" * 70)
    print("Testing connection to FM transmitter...")
    print("=" * 70)

    try:
        url = f'http://{host}:{port}'
        rpc = xmlrpc.client.ServerProxy(url)

        # Read current frequency
        current_freq = rpc.get_freq()
        print(f"✓ Connected to GNU Radio at {url}")
        print(f"✓ Current FM frequency: {current_freq / 1e6:.1f} MHz")

        return True

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nMake sure the FM transmitter flowgraph is running:")
        print("  cd fm/")
        print("  python fm_transmitter_shm.py")
        return False


def set_fm_frequency(freq_mhz, host='localhost', port=8080):
    """
    Set FM transmitter frequency.

    Parameters
    ----------
    freq_mhz : float
        Frequency in MHz (e.g., 98.5)
    host : str
        Hostname of GNU Radio XML-RPC server
    port : int
        Port of GNU Radio XML-RPC server
    """
    try:
        rpc = xmlrpc.client.ServerProxy(f'http://{host}:{port}')
        freq_hz = freq_mhz * 1e6

        print(f"\nSetting FM frequency to {freq_mhz:.1f} MHz ({freq_hz:.0f} Hz)...")
        rpc.set_freq(freq_hz)
        time.sleep(0.5)  # Allow time for tuning

        # Verify
        actual_freq = rpc.get_freq()
        print(f"✓ Frequency set to {actual_freq / 1e6:.1f} MHz")

    except Exception as e:
        print(f"✗ Failed to set frequency: {e}")


def fm_band_sweep(start_mhz=88.0, stop_mhz=108.0, step_mhz=0.2,
                  dwell_time=2.0, host='localhost', port=8080):
    """
    Sweep through FM radio band.

    This will tune through the FM broadcast band, dwelling at each frequency
    to allow you to hear what's being broadcast.

    Parameters
    ----------
    start_mhz : float
        Starting frequency in MHz (default: 88.0)
    stop_mhz : float
        Ending frequency in MHz (default: 108.0)
    step_mhz : float
        Step size in MHz (default: 0.2)
    dwell_time : float
        Time to dwell at each frequency in seconds (default: 2.0)
    host : str
        Hostname of GNU Radio XML-RPC server
    port : int
        Port of GNU Radio XML-RPC server
    """
    print("=" * 70)
    print("FM Band Sweep")
    print("=" * 70)
    print(f"Frequency range: {start_mhz:.1f} - {stop_mhz:.1f} MHz")
    print(f"Step size: {step_mhz:.1f} MHz")
    print(f"Dwell time: {dwell_time:.1f} seconds")
    print("\nWatch/listen to the GNU Radio GUI!")
    print("Press Ctrl+C to stop the sweep")
    print("=" * 70)

    try:
        rpc = xmlrpc.client.ServerProxy(f'http://{host}:{port}')

        # Save initial frequency
        initial_freq = rpc.get_freq()

        # Calculate number of steps
        num_steps = int((stop_mhz - start_mhz) / step_mhz) + 1

        print(f"\nStarting sweep ({num_steps} steps)...\n")

        for i in range(num_steps):
            freq_mhz = start_mhz + i * step_mhz
            freq_hz = freq_mhz * 1e6

            rpc.set_freq(freq_hz)
            print(f"[{i+1:3d}/{num_steps}] {freq_mhz:6.1f} MHz", end='', flush=True)

            time.sleep(dwell_time)
            print()  # New line after dwell

        print("\n✓ Sweep completed!")

        # Return to initial frequency
        print(f"\nReturning to initial frequency: {initial_freq / 1e6:.1f} MHz")
        rpc.set_freq(initial_freq)

    except KeyboardInterrupt:
        print("\n\n⚠ Sweep interrupted by user")
        print(f"Returning to initial frequency: {initial_freq / 1e6:.1f} MHz")
        rpc.set_freq(initial_freq)

    except Exception as e:
        print(f"\n✗ Sweep failed: {e}")


def bluesky_fm_sweep(start_mhz=88.0, stop_mhz=108.0, num_points=100,
                     dwell_time=0.5, host='localhost', port=8080):
    """
    Use Bluesky to sweep FM band (requires Bluesky installation).

    Parameters
    ----------
    start_mhz : float
        Starting frequency in MHz
    stop_mhz : float
        Ending frequency in MHz
    num_points : int
        Number of frequency points
    dwell_time : float
        Dwell time at each frequency in seconds
    host : str
        Hostname of GNU Radio XML-RPC server
    port : int
        Port of GNU Radio XML-RPC server
    """
    print("=" * 70)
    print("Bluesky FM Band Sweep")
    print("=" * 70)

    try:
        # Import Bluesky modules
        from bluesky import RunEngine
        from bluesky import plan_stubs as bps
        from bluesky.preprocessors import run_decorator
        from gnuradio_bluesky.gnuradio_device import GNURadioSignalGenerator

        print("✓ Bluesky modules imported")

        # Create device for FM transmitter
        # Note: The device expects get_frequency/set_frequency methods,
        # but the FM transmitter uses get_freq/set_freq
        # We'll use a custom wrapper

        class FMTransmitter(GNURadioSignalGenerator):
            """Custom device for FM transmitter with freq (not frequency) variable."""

            def __init__(self, prefix='', **kwargs):
                # Override parent init to use different method names
                self._host = kwargs.get('host', 'localhost')
                self._port = kwargs.get('port', 8080)
                self._timeout = kwargs.get('timeout', 5.0)
                self._connected = False

                # Connect to XML-RPC server
                self._connect_fm()

                # Initialize Device (skip GNURadioSignalGenerator.__init__)
                from ophyd import Device
                Device.__init__(self, prefix, name=kwargs.get('name'))

                # Create frequency signal with custom method names
                from gnuradio_bluesky.gnuradio_device import XMLRPCSignal
                freq_signal = XMLRPCSignal(
                    self._rpc_client,
                    'get_freq',      # FM uses 'freq' not 'frequency'
                    'set_freq',
                    name=f"{kwargs.get('name')}_frequency",
                    value=self._rpc_client.get_freq(),
                    kind='hinted'
                )
                freq_signal._parent = self
                self.frequency = freq_signal

            def _connect_fm(self):
                """Connect to FM transmitter XML-RPC server."""
                url = f'http://{self._host}:{self._port}'
                self._rpc_client = xmlrpc.client.ServerProxy(url)

                # Test connection
                current_freq = self._rpc_client.get_freq()
                self._connected = True

                print(f"✓ Connected to FM transmitter at {url}")
                print(f"  Current frequency: {current_freq / 1e6:.1f} MHz")

        # Create FM transmitter device
        fm_tx = FMTransmitter('', name='fm_tx', host=host, port=port)

        # Create RunEngine
        RE = RunEngine({})
        print("✓ RunEngine created")

        # Define sweep plan
        @run_decorator(md={'plan_name': 'fm_band_sweep',
                          'start_mhz': start_mhz,
                          'stop_mhz': stop_mhz,
                          'num_points': num_points})
        def fm_sweep():
            start_hz = start_mhz * 1e6
            stop_hz = stop_mhz * 1e6
            step_hz = (stop_hz - start_hz) / (num_points - 1)

            print(f"\nSweeping {start_mhz:.1f} - {stop_mhz:.1f} MHz")
            print(f"Points: {num_points}, Dwell: {dwell_time}s\n")

            for i in range(num_points):
                freq_hz = start_hz + i * step_hz
                freq_mhz = freq_hz / 1e6

                yield from bps.abs_set(fm_tx.frequency, freq_hz, wait=True)
                print(f"[{i+1:3d}/{num_points}] {freq_mhz:6.1f} MHz")
                yield from bps.sleep(dwell_time)

        # Run the sweep
        print("\nStarting Bluesky FM sweep...")
        RE(fm_sweep())

        print("\n✓ Bluesky sweep completed!")

    except ImportError as e:
        print(f"✗ Bluesky not installed: {e}")
        print("\nTo install Bluesky:")
        print("  pip install bluesky ophyd")
        print("\nFalling back to direct XML-RPC sweep...")
        fm_band_sweep(start_mhz, stop_mhz,
                     step_mhz=(stop_mhz - start_mhz) / num_points,
                     dwell_time=dwell_time, host=host, port=port)

    except Exception as e:
        print(f"✗ Bluesky sweep failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Bluesky control for FM transmitter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connection
  %(prog)s --test

  # Set to WGBH Boston (89.7 MHz)
  %(prog)s --freq 89.7

  # Sweep FM band (simple)
  %(prog)s --sweep

  # Sweep FM band with Bluesky
  %(prog)s --bluesky-sweep

  # Custom sweep range
  %(prog)s --sweep --start 95.0 --stop 100.0 --step 0.1 --dwell 1.0

  # Connect to remote GNU Radio instance
  %(prog)s --test --host 192.168.1.100 --port 8080
        """
    )

    parser.add_argument('--test', action='store_true',
                       help='Test connection to FM transmitter')
    parser.add_argument('--freq', type=float, metavar='MHZ',
                       help='Set FM frequency in MHz (e.g., 98.5)')
    parser.add_argument('--sweep', action='store_true',
                       help='Sweep through FM band')
    parser.add_argument('--bluesky-sweep', action='store_true',
                       help='Use Bluesky for FM band sweep (requires Bluesky)')

    parser.add_argument('--start', type=float, default=88.0, metavar='MHZ',
                       help='Sweep start frequency in MHz (default: 88.0)')
    parser.add_argument('--stop', type=float, default=108.0, metavar='MHZ',
                       help='Sweep stop frequency in MHz (default: 108.0)')
    parser.add_argument('--step', type=float, default=0.2, metavar='MHZ',
                       help='Sweep step size in MHz (default: 0.2)')
    parser.add_argument('--num-points', type=int, default=100, metavar='N',
                       help='Number of points for Bluesky sweep (default: 100)')
    parser.add_argument('--dwell', type=float, default=2.0, metavar='SEC',
                       help='Dwell time per frequency in seconds (default: 2.0)')

    parser.add_argument('--host', default='localhost',
                       help='XML-RPC server hostname (default: localhost)')
    parser.add_argument('--port', type=int, default=8080,
                       help='XML-RPC server port (default: 8080)')

    args = parser.parse_args()

    # If no action specified, show help
    if not any([args.test, args.freq, args.sweep, args.bluesky_sweep]):
        parser.print_help()
        print("\n⚠ No action specified. Use --test, --freq, --sweep, or --bluesky-sweep")
        sys.exit(1)

    # Test connection if requested (or before any other action)
    if args.test or args.freq or args.sweep or args.bluesky_sweep:
        if not test_connection(args.host, args.port):
            sys.exit(1)

    # Set frequency
    if args.freq:
        if not (88.0 <= args.freq <= 108.0):
            print(f"⚠ Warning: {args.freq:.1f} MHz is outside FM broadcast band (88-108 MHz)")
        set_fm_frequency(args.freq, args.host, args.port)

    # Sweep
    if args.sweep:
        fm_band_sweep(args.start, args.stop, args.step, args.dwell,
                     args.host, args.port)

    # Bluesky sweep
    if args.bluesky_sweep:
        bluesky_fm_sweep(args.start, args.stop, args.num_points, args.dwell,
                        args.host, args.port)

    print("\n✓ Done!")


if __name__ == '__main__':
    main()
