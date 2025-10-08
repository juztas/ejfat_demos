#!/usr/bin/env python3
"""
Quick test script to verify the XML-RPC signal fix.
Run this after starting sine_wave_demo.py
"""

import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test direct XML-RPC first
import xmlrpc.client
try:
    rpc = xmlrpc.client.ServerProxy('http://localhost:8080')
    print("Testing direct XML-RPC...")
    print(f"Initial frequency: {rpc.get_frequency()} Hz")

    print("Setting to 1500 Hz via XML-RPC...")
    rpc.set_frequency(1500)
    time.sleep(0.1)
    print(f"Readback: {rpc.get_frequency()} Hz")

    print("Setting to 2500 Hz via XML-RPC...")
    rpc.set_frequency(2500)
    time.sleep(0.1)
    print(f"Readback: {rpc.get_frequency()} Hz")

    print("\n✓ Direct XML-RPC works!\n")
except Exception as e:
    print(f"✗ XML-RPC test failed: {e}")
    sys.exit(1)

# Now test Bluesky integration
try:
    from bluesky import RunEngine
    from gnuradio_bluesky.gnuradio_device import GNURadioSignalGenerator

    print("Testing Bluesky integration...")
    RE = RunEngine({})
    sig_gen = GNURadioSignalGenerator('', name='sig_gen', host='localhost', port=8080)

    print(f"\nInitial frequency: {sig_gen.frequency.get()} Hz")

    print("Setting to 3000 Hz via Ophyd Signal.set()...")
    status = sig_gen.frequency.set(3000)
    status.wait()
    time.sleep(0.1)

    # Verify with direct XML-RPC readback
    actual_freq = rpc.get_frequency()
    print(f"GNU Radio readback (via XML-RPC): {actual_freq} Hz")

    if abs(actual_freq - 3000) < 1:
        print("\n✓ Bluesky integration works! Frequency changes are reaching GNU Radio.\n")
    else:
        print(f"\n✗ Mismatch! Expected 3000 Hz but GNU Radio shows {actual_freq} Hz\n")
        sys.exit(1)

except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("Make sure Bluesky is installed: pip install bluesky ophyd")
    sys.exit(1)
except Exception as e:
    print(f"✗ Bluesky test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("All tests passed!")
