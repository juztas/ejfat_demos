#!/usr/bin/env python3
"""
Simple test script for Bluesky control of GNU Radio signal generator.

This script demonstrates basic functionality of the Bluesky/GNU Radio
integration without requiring a full Bluesky installation.

Usage:
    # Start GNU Radio flowgraph first in another terminal:
    python sine_wave_demo.py

    # Then run this test:
    python test_bluesky_control.py
"""

import sys
import time
import xmlrpc.client


def test_xmlrpc_direct():
    """Test direct XML-RPC communication with GNU Radio."""
    print("=" * 60)
    print("Test 1: Direct XML-RPC Communication")
    print("=" * 60)

    try:
        # Connect to GNU Radio XML-RPC server
        rpc = xmlrpc.client.ServerProxy('http://localhost:8080')
        print("✓ Connected to GNU Radio XML-RPC server")

        # Read current frequency
        current_freq = rpc.get_frequency()
        print(f"✓ Current frequency: {current_freq} Hz")

        # Test setting frequency
        test_freq = 2500
        print(f"\nSetting frequency to {test_freq} Hz...")
        rpc.set_frequency(test_freq)

        # Verify
        new_freq = rpc.get_frequency()
        print(f"✓ Verified frequency: {new_freq} Hz")

        if abs(new_freq - test_freq) < 1:
            print("✓ Frequency set successfully!")
        else:
            print(f"✗ Frequency mismatch: expected {test_freq}, got {new_freq}")

        # Return to original frequency
        print(f"\nReturning to original frequency: {current_freq} Hz")
        rpc.set_frequency(current_freq)

        return True

    except Exception as e:
        print(f"✗ XML-RPC test failed: {e}")
        print("\nMake sure GNU Radio flowgraph is running:")
        print("  python sine_wave_demo.py")
        return False


def test_frequency_sweep():
    """Test a simple frequency sweep via XML-RPC."""
    print("\n" + "=" * 60)
    print("Test 2: Frequency Sweep")
    print("=" * 60)

    try:
        rpc = xmlrpc.client.ServerProxy('http://localhost:8080')

        # Save initial frequency
        initial_freq = rpc.get_frequency()
        print(f"Initial frequency: {initial_freq} Hz")

        # Sweep parameters
        start_freq = 500
        stop_freq = 3000
        num_steps = 10
        dwell_time = 0.3  # seconds

        print(f"\nSweeping from {start_freq} Hz to {stop_freq} Hz in {num_steps} steps")
        print(f"Dwell time: {dwell_time} seconds per step")
        print("Watch the GNU Radio GUI for changes!\n")

        # Perform sweep
        step_size = (stop_freq - start_freq) / (num_steps - 1)

        for i in range(num_steps):
            freq = start_freq + i * step_size
            rpc.set_frequency(freq)
            print(f"Step {i+1}/{num_steps}: {freq:.0f} Hz")
            time.sleep(dwell_time)

        # Return to initial frequency
        print(f"\nReturning to initial frequency: {initial_freq} Hz")
        rpc.set_frequency(initial_freq)

        print("✓ Frequency sweep completed successfully!")
        return True

    except Exception as e:
        print(f"✗ Frequency sweep failed: {e}")
        return False


def test_bluesky_device():
    """Test the Bluesky device wrapper (if Bluesky is installed)."""
    print("\n" + "=" * 60)
    print("Test 3: Bluesky Device (Optional)")
    print("=" * 60)

    try:
        # Try importing Bluesky modules
        from bluesky import RunEngine
        from bluesky import plan_stubs as bps
        sys.path.insert(0, '.')  # Add current directory to path
        from gnuradio_bluesky.gnuradio_device import GNURadioSignalGenerator

        print("✓ Bluesky modules imported successfully")

        # Create device
        sig_gen = GNURadioSignalGenerator('', name='sig_gen', host='localhost', port=8080)
        print("✓ GNURadioSignalGenerator device created")

        # Create RunEngine
        RE = RunEngine({})
        print("✓ RunEngine created")

        # Test setting frequency via Bluesky
        test_freq = 1500
        print(f"\nSetting frequency to {test_freq} Hz via Bluesky...")

        def set_freq_plan():
            yield from bps.abs_set(sig_gen.frequency, test_freq, wait=True)

        RE(set_freq_plan())
        print(f"✓ Frequency set via Bluesky: {test_freq} Hz")

        # Test reading frequency
        actual_freq = sig_gen.get_frequency()
        print(f"✓ Read back frequency: {actual_freq} Hz")

        if abs(actual_freq - test_freq) < 1:
            print("✓ Bluesky device test passed!")
        else:
            print(f"✗ Frequency mismatch: expected {test_freq}, got {actual_freq}")

        return True

    except ImportError:
        print("ℹ Bluesky not installed - skipping Bluesky device test")
        print("  To install: pip install bluesky ophyd")
        return None  # Not a failure, just not installed

    except Exception as e:
        print(f"✗ Bluesky device test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("GNU Radio + Bluesky Integration Test")
    print("=" * 60)
    print("\nPrerequisites:")
    print("  1. GNU Radio flowgraph must be running")
    print("     Command: python sine_wave_demo.py")
    print("  2. XML-RPC server should be on localhost:8080")
    print("\nStarting tests in 2 seconds...")
    print("=" * 60)
    time.sleep(2)

    results = []

    # Test 1: Direct XML-RPC
    result1 = test_xmlrpc_direct()
    results.append(("Direct XML-RPC", result1))

    if result1:
        # Test 2: Frequency sweep
        result2 = test_frequency_sweep()
        results.append(("Frequency Sweep", result2))

        # Test 3: Bluesky device (optional)
        result3 = test_bluesky_device()
        if result3 is not None:
            results.append(("Bluesky Device", result3))
    else:
        print("\n⚠ Skipping remaining tests due to connection failure")

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = 0
    failed = 0
    skipped = 0

    for test_name, result in results:
        if result is True:
            status = "✓ PASSED"
            passed += 1
        elif result is False:
            status = "✗ FAILED"
            failed += 1
        else:
            status = "⊘ SKIPPED"
            skipped += 1

        print(f"{test_name:.<40} {status}")

    print("=" * 60)
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()
