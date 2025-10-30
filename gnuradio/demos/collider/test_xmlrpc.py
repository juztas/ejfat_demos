#!/usr/bin/env python3
"""Test script to verify XML-RPC server is working"""

import xmlrpc.client
import sys

try:
    # Connect to the collider RPC server
    proxy = xmlrpc.client.ServerProxy("http://localhost:8000/")

    print("Testing XML-RPC Connection to Particle Collider...")
    print("=" * 60)

    # Get status
    print("\n1. Getting status...")
    status = proxy.get_status()
    print(f"   Time Elapsed: {status['time_elapsed']:.1f}s")
    print(f"   Total Particles: {status['particle_count']}")
    print(f"   Active Particles: {status['active_particles']}")
    print(f"   Paused: {status['paused']}")
    print(f"   Speed Range: {status['speed_min']:.2f} - {status['speed_max']:.2f}")
    print(f"   Interval Range: {status['interval_min']:.2f} - {status['interval_max']:.2f}")

    # Set speed min
    print("\n2. Setting speed_min to 0.7...")
    result = proxy.set_speed_min(0.7)
    print(f"   Result: {result}")

    # Set speed max
    print("\n3. Setting speed_max to 1.2...")
    result = proxy.set_speed_max(1.2)
    print(f"   Result: {result}")

    # Get statistics
    print("\n4. Getting statistics...")
    stats = proxy.get_statistics()
    print(f"   Total Particles: {stats['total_particles']}")
    if 'speed' in stats:
        print(f"   Speed - Mean: {stats['speed']['mean']:.3f}, Min: {stats['speed']['min']:.3f}, Max: {stats['speed']['max']:.3f}")
    if 'deflection_angle' in stats:
        print(f"   Angle - Mean: {stats['deflection_angle']['mean']:.2f}°")

    print("\n" + "=" * 60)
    print("✓ XML-RPC server is working correctly!")
    print("\nWeb interface available at:")
    print("  http://localhost:8001/collider_control.html")
    print("=" * 60)

except ConnectionRefusedError:
    print("ERROR: Could not connect to XML-RPC server")
    print("Make sure the particle collider simulation is running!")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
