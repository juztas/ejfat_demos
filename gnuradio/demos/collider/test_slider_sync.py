#!/usr/bin/env python3
"""
Test script to demonstrate slider synchronization between
XML-RPC remote control and matplotlib GUI
"""

import xmlrpc.client
import time
import sys

def main():
    try:
        # Connect to the collider RPC server
        proxy = xmlrpc.client.ServerProxy("http://localhost:8000/")

        print("=" * 60)
        print("Slider Synchronization Demo")
        print("=" * 60)
        print("\nThis script will remotely change parameters via XML-RPC.")
        print("Watch the matplotlib GUI - the sliders should update!")
        print()
        print("Make sure you can see the matplotlib window.")
        print("=" * 60)
        print()

        # Test 1: Speed Min
        print("Test 1: Setting Speed Min to 0.8...")
        result = proxy.set_speed_min(0.8)
        print(f"  Result: {result}")
        print("  → Check the 'Speed Min' slider in the GUI - it should move to 0.8")
        time.sleep(3)

        # Test 2: Speed Max
        print("\nTest 2: Setting Speed Max to 1.3...")
        result = proxy.set_speed_max(1.3)
        print(f"  Result: {result}")
        print("  → Check the 'Speed Max' slider in the GUI - it should move to 1.3")
        time.sleep(3)

        # Test 3: Interval Min
        print("\nTest 3: Setting Interval Min to 0.3...")
        result = proxy.set_interval_min(0.3)
        print(f"  Result: {result}")
        print("  → Check the 'Interval Min' slider in the GUI - it should move to 0.3")
        time.sleep(3)

        # Test 4: Interval Max
        print("\nTest 4: Setting Interval Max to 1.5...")
        result = proxy.set_interval_max(1.5)
        print(f"  Result: {result}")
        print("  → Check the 'Interval Max' slider in the GUI - it should move to 1.5")
        time.sleep(3)

        # Test 5: Pause
        print("\nTest 5: Pausing simulation...")
        result = proxy.pause()
        print(f"  Result: {result}")
        print("  → Check the 'Pause' button in the GUI - it should change to 'Resume'")
        time.sleep(3)

        # Test 6: Resume
        print("\nTest 6: Resuming simulation...")
        result = proxy.resume()
        print(f"  Result: {result}")
        print("  → Check the button in the GUI - it should change back to 'Pause'")
        time.sleep(2)

        # Animate: Cycle through speeds
        print("\nBonus: Animating speed changes...")
        print("(Watch the Speed Min slider move!)")
        for speed in [0.5, 0.6, 0.7, 0.8, 0.9, 0.8, 0.7, 0.6, 0.5]:
            proxy.set_speed_min(speed)
            print(f"  Speed Min: {speed:.1f}")
            time.sleep(0.5)

        print("\n" + "=" * 60)
        print("✓ Slider synchronization test complete!")
        print("\nAll sliders in the matplotlib GUI should have updated")
        print("in response to the XML-RPC commands.")
        print("=" * 60)

    except ConnectionRefusedError:
        print("ERROR: Could not connect to XML-RPC server")
        print("Make sure the particle collider simulation is running!")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
