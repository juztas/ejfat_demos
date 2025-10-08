#!/usr/bin/env python3
"""
Simple startup script for Bluesky control of GNU Radio sine wave demo.

Prerequisites:
    1. Start GNU Radio flowgraph first:
       python sine_wave_demo.py

    2. Make sure Bluesky is installed:
       pip install bluesky ophyd

Usage:
    python run_bluesky_demo.py

    This will drop you into IPython with everything pre-loaded.
"""

import sys
import os

# Add current directory to Python path so we can import the bluesky module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bluesky import RunEngine
    from bluesky import plan_stubs as bps
    from gnuradio_bluesky.gnuradio_device import GNURadioSignalGenerator
    from gnuradio_bluesky.sine_control_plan import (
        set_sine_frequency,
        frequency_sweep,
        frequency_steps,
        frequency_ramp,
        frequency_scan,
        frequency_list_scan,
        characterize_sine_wave,
        frequency_sweep_and_return
    )
except ImportError as e:
    print("ERROR: Failed to import required modules")
    print(f"Details: {e}")
    print("\nPlease install Bluesky:")
    print("  pip install bluesky ophyd")
    sys.exit(1)

# Test connection to GNU Radio
import xmlrpc.client
try:
    rpc = xmlrpc.client.ServerProxy('http://localhost:8080')
    current_freq = rpc.get_frequency()
    print(f"✓ Connected to GNU Radio (current frequency: {current_freq} Hz)")
except Exception as e:
    print("ERROR: Cannot connect to GNU Radio XML-RPC server")
    print(f"Details: {e}")
    print("\nMake sure GNU Radio flowgraph is running:")
    print("  python sine_wave_demo.py")
    sys.exit(1)

# Create RunEngine and device
print("\nInitializing Bluesky...")
RE = RunEngine({})
sig_gen = GNURadioSignalGenerator('', name='sig_gen', host='localhost', port=8080)
print("✓ RunEngine and signal generator device created")

print("\n" + "=" * 70)
print("Bluesky + GNU Radio Demo Ready!")
print("=" * 70)
print("\nAvailable objects:")
print("  RE       - RunEngine for running plans")
print("  sig_gen  - GNU Radio signal generator device")
print("\nAvailable plans:")
print("  set_sine_frequency(sig_gen, freq)")
print("  frequency_sweep(sig_gen, start, stop, num_points, dwell_time=0.5)")
print("  frequency_steps(sig_gen, frequencies, dwell_time=1.0)")
print("  frequency_ramp(sig_gen, start, stop, duration, step_size=100)")
print("  frequency_scan(detectors, sig_gen, start, stop, num_points)")
print("\nExample commands:")
print("  RE(set_sine_frequency(sig_gen, 2500))")
print("  RE(frequency_sweep(sig_gen, 100, 5000, 50, dwell_time=0.5))")
print("  RE(frequency_steps(sig_gen, [440, 880, 1320, 1760], dwell_time=1.0))")
print("=" * 70)
print()

# Start IPython with everything loaded
try:
    from IPython import embed
    embed(colors='neutral')
except ImportError:
    print("IPython not found. Starting standard Python shell...")
    import code
    code.interact(local=locals())
