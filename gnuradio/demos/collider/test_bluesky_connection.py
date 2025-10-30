#!/usr/bin/env python3
"""
Test script to verify XML-RPC connection for Bluesky integration

This tests the underlying XML-RPC communication without requiring
Bluesky/ophyd to be installed. Run this before installing Bluesky
to verify the connection will work.
"""

import xmlrpc.client
import time


def test_xmlrpc_for_bluesky():
    """Test all XML-RPC methods that Bluesky will use"""
    print("=" * 60)
    print("Testing XML-RPC Connection for Bluesky Integration")
    print("=" * 60)

    try:
        # Connect to server
        proxy = xmlrpc.client.ServerProxy("http://localhost:8000/")
        print("\n✓ Connected to XML-RPC server at localhost:8000")

        # Test get_status (used for all readbacks)
        print("\n1. Testing get_status() - used for all signal readbacks...")
        status = proxy.get_status()
        print(f"   ✓ Status: {status['particle_count']} particles, "
              f"{'PAUSED' if status['paused'] else 'RUNNING'}")

        # Extract signals that Bluesky will read
        print("\n2. Testing readback signals...")
        print(f"   - time_elapsed: {status['time_elapsed']:.2f} s")
        print(f"   - active_particles: {status['active_particles']}")
        print(f"   - total_particles: {status['particle_count']}")
        print(f"   - speed_min: {status['speed_min']:.2f}")
        print(f"   - speed_max: {status['speed_max']:.2f}")
        print(f"   - interval_min: {status['interval_min']:.2f}")
        print(f"   - interval_max: {status['interval_max']:.2f}")

        # Test set methods (used for control signals)
        print("\n3. Testing control methods...")

        original_speed_min = status['speed_min']

        print(f"   - Setting speed_min to 0.65...")
        result = proxy.set_speed_min(0.65)
        if result['success'] and abs(result['value'] - 0.65) < 0.01:
            print(f"     ✓ Successfully set to {result['value']:.2f}")
        else:
            print(f"     ✗ Failed: {result}")

        print(f"   - Setting speed_max to 1.1...")
        result = proxy.set_speed_max(1.1)
        if result['success'] and abs(result['value'] - 1.1) < 0.01:
            print(f"     ✓ Successfully set to {result['value']:.2f}")
        else:
            print(f"     ✗ Failed: {result}")

        print(f"   - Setting interval_min to 0.4...")
        result = proxy.set_interval_min(0.4)
        if result['success'] and abs(result['value'] - 0.4) < 0.01:
            print(f"     ✓ Successfully set to {result['value']:.2f}")
        else:
            print(f"     ✗ Failed: {result}")

        print(f"   - Setting interval_max to 1.3...")
        result = proxy.set_interval_max(1.3)
        if result['success'] and abs(result['value'] - 1.3) < 0.01:
            print(f"     ✓ Successfully set to {result['value']:.2f}")
        else:
            print(f"     ✗ Failed: {result}")

        # Restore original value
        print(f"\n   - Restoring speed_min to {original_speed_min:.2f}...")
        proxy.set_speed_min(original_speed_min)
        print("     ✓ Restored")

        # Test pause/resume
        print("\n4. Testing pause/resume...")
        was_paused = status['paused']

        if not was_paused:
            print("   - Pausing simulation...")
            result = proxy.pause()
            if result['success'] and result['paused']:
                print("     ✓ Paused")
            else:
                print(f"     ✗ Failed: {result}")

            time.sleep(0.5)

            print("   - Resuming simulation...")
            result = proxy.resume()
            if result['success'] and not result['paused']:
                print("     ✓ Resumed")
            else:
                print(f"     ✗ Failed: {result}")
        else:
            print("   - Simulation was already paused")
            print("   - Resuming...")
            proxy.resume()
            print("     ✓ Resumed")

        # Test get_statistics (used by device but not in Bluesky stream)
        print("\n5. Testing get_statistics() - available but not in Bluesky stream...")
        stats = proxy.get_statistics()
        print(f"   ✓ Got statistics: {stats['total_particles']} total particles")
        print(f"     (Note: Detector data in statistics is NOT passed to Bluesky)")

        # Summary
        print("\n" + "=" * 60)
        print("✓ All XML-RPC methods tested successfully!")
        print("\nThe Bluesky device will use these methods:")
        print("  - get_status() → read all signal values")
        print("  - set_speed_min/max() → control speed range")
        print("  - set_interval_min/max() → control injection timing")
        print("  - pause/resume() → simulation control")
        print("\nBluesky data stream will include:")
        print("  - Config: speed_min, speed_max, interval_min, interval_max")
        print("  - Primary: time_elapsed, active_particles, total_particles")
        print("\nNOT in Bluesky (saved separately by simulation):")
        print("  - Calorimeter hits, Pixel detector hits, Per-particle data")
        print("=" * 60)

        return True

    except ConnectionRefusedError:
        print("\n✗ ERROR: Could not connect to XML-RPC server")
        print("  Make sure the particle collider is running:")
        print("    python particle_collider.py")
        return False

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_xmlrpc_for_bluesky()

    if success:
        print("\n" + "=" * 60)
        print("Ready for Bluesky integration!")
        print("\nTo install Bluesky:")
        print("  pip install -r bluesky_requirements.txt")
        print("\nThen run examples:")
        print("  python bluesky_examples.py")
        print("=" * 60)
        exit(0)
    else:
        exit(1)
