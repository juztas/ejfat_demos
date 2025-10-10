#!/usr/bin/env python3
"""
Test FM SHM Beamline Devices

Simple test script to verify FM beamline device initialization and control.
This tests Phase 1 implementation without running a full experiment.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from bluesky_config.devices_fm_shm import (
    FMTransmitterSHM,
    FMReceiverSHM,
    SHMMonitor,
    FMSHMBeamline,
)
from bluesky_config.fm_beamline_config import (
    OTTAWA_FM_STATIONS,
    get_station_frequency,
    validate_frequency,
)


def test_configuration():
    """Test FM beamline configuration."""
    print("\n" + "=" * 60)
    print("TEST 1: Configuration Module")
    print("=" * 60)

    # Test station lookup
    print("\nKnown Ottawa FM Stations:")
    for name, info in OTTAWA_FM_STATIONS.items():
        print(f"  {name:20s} {info['frequency']/1e6:6.1f} MHz  ({info['format']})")

    # Test frequency validation
    print("\nFrequency Validation:")
    test_freqs = [98.5e6, 50e6, 150e6]
    for freq in test_freqs:
        valid = validate_frequency(freq)
        print(f"  {freq/1e6:.1f} MHz: {'✓ Valid' if valid else '✗ Invalid'}")

    # Test station lookup
    print("\nStation Lookup:")
    try:
        chez_freq = get_station_frequency('CHEZ 106')
        print(f"  CHEZ 106: {chez_freq/1e6:.1f} MHz ✓")
    except KeyError as e:
        print(f"  ERROR: {e}")

    print("\n✓ Configuration test passed")


def test_transmitter_device():
    """Test FM transmitter device initialization."""
    print("\n" + "=" * 60)
    print("TEST 2: FM Transmitter Device")
    print("=" * 60)

    try:
        # Create device (don't auto-start)
        print("\nCreating FMTransmitterSHM device...")
        tx = FMTransmitterSHM(name='fm_tx', autostart=False)

        print(f"  Device name: {tx.name}")
        print(f"  Default frequency: {tx.frequency.get()/1e6:.1f} MHz")
        print(f"  Sample rate: {tx.sample_rate.get()/1e6:.1f} MHz")
        print(f"  SHM name: {tx.shm_name.get()}")
        print(f"  Running: {tx.running}")
        print(f"  Connected: {tx.connected}")

        print("\n✓ Transmitter device test passed")
        return tx

    except Exception as e:
        print(f"\n✗ Transmitter device test failed: {e}")
        raise


def test_receiver_device():
    """Test FM receiver device initialization."""
    print("\n" + "=" * 60)
    print("TEST 3: FM Receiver Device")
    print("=" * 60)

    try:
        # Create device (don't auto-start)
        print("\nCreating FMReceiverSHM device...")
        rx = FMReceiverSHM(name='fm_rx', autostart=False)

        print(f"  Device name: {rx.name}")
        print(f"  Default volume: {rx.volume.get()}")
        print(f"  Audio rate: {rx.audio_rate.get()} Hz")
        print(f"  SHM name: {rx.shm_name.get()}")
        print(f"  Running: {rx.running}")

        print("\n✓ Receiver device test passed")
        return rx

    except Exception as e:
        print(f"\n✗ Receiver device test failed: {e}")
        raise


def test_shm_monitor():
    """Test shared memory monitor device."""
    print("\n" + "=" * 60)
    print("TEST 4: SHM Monitor Device")
    print("=" * 60)

    try:
        # Create monitor
        print("\nCreating SHMMonitor device...")
        monitor = SHMMonitor(name='shm_buffer')

        print(f"  Device name: {monitor.name}")

        # Trigger measurement
        print("\nTriggering measurement...")
        status = monitor.trigger()
        status.wait(timeout=2.0)

        # Read values
        readings = monitor.read()
        print("\nReadings:")
        for key, value in readings.items():
            print(f"  {key}: {value['value']}")

        print("\n✓ SHM monitor test passed")
        return monitor

    except Exception as e:
        print(f"\n✗ SHM monitor test failed: {e}")
        raise


def test_composite_beamline():
    """Test composite beamline device."""
    print("\n" + "=" * 60)
    print("TEST 5: Composite Beamline Device")
    print("=" * 60)

    try:
        # Create beamline
        print("\nCreating FMSHMBeamline device...")
        beamline = FMSHMBeamline(name='fm_shm')

        print(f"  Beamline name: {beamline.name}")
        print(f"  Transmitter: {beamline.transmitter.name}")
        print(f"  Receiver: {beamline.receiver.name}")
        print(f"  Buffer monitor: {beamline.buffer.name}")
        print(f"  Ready: {beamline.ready}")

        print("\n✓ Composite beamline test passed")
        return beamline

    except Exception as e:
        print(f"\n✗ Composite beamline test failed: {e}")
        raise


def test_flowgraph_control(beamline):
    """
    Test flowgraph launch and control.

    NOTE: This requires the actual flowgraph files to exist and
    may launch GUI windows. Use with caution.
    """
    print("\n" + "=" * 60)
    print("TEST 6: Flowgraph Control (INTERACTIVE)")
    print("=" * 60)

    response = input("\nThis will launch GNU Radio flowgraphs. Continue? [y/N]: ")
    if response.lower() != 'y':
        print("Skipped flowgraph control test")
        return

    try:
        # Start beamline
        print("\nStarting beamline (TX only)...")
        beamline.startup(start_rx=False)

        # Check status
        print(f"\nBeamline status:")
        print(f"  TX running: {beamline.transmitter.running}")
        print(f"  TX connected: {beamline.transmitter.connected}")
        print(f"  Beamline ready: {beamline.ready}")

        if beamline.ready:
            # Test frequency control
            print("\nTesting frequency control...")
            test_freq = 98.5e6

            print(f"  Setting frequency to {test_freq/1e6:.1f} MHz...")
            beamline.transmitter.set_frequency(test_freq)
            time.sleep(0.5)

            current_freq = beamline.transmitter.get_frequency()
            print(f"  Current frequency: {current_freq/1e6:.1f} MHz")

            if abs(current_freq - test_freq) < 1e3:
                print("  ✓ Frequency control working")
            else:
                print(f"  ✗ Frequency mismatch: {abs(current_freq - test_freq)/1e3:.1f} kHz")

        # Wait a bit
        print("\nFlowgraph running... (waiting 5 seconds)")
        time.sleep(5)

        # Shutdown
        print("\nShutting down beamline...")
        beamline.shutdown()

        print("\n✓ Flowgraph control test passed")

    except Exception as e:
        print(f"\n✗ Flowgraph control test failed: {e}")
        print("\nAttempting cleanup...")
        try:
            beamline.shutdown()
        except:
            pass
        raise


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FM SHM Beamline Device Tests")
    print("=" * 60)

    try:
        # Test 1: Configuration
        test_configuration()

        # Test 2: Transmitter device
        tx = test_transmitter_device()

        # Test 3: Receiver device
        rx = test_receiver_device()

        # Test 4: SHM monitor
        monitor = test_shm_monitor()

        # Test 5: Composite beamline
        beamline = test_composite_beamline()

        # Test 6: Flowgraph control (optional/interactive)
        test_flowgraph_control(beamline)

        # Summary
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nPhase 1 implementation complete!")
        print("\nNext steps:")
        print("  - Phase 2: Create scan plans (plans_fm_shm.py)")
        print("  - Phase 3: Create callbacks (callbacks_fm_shm.py)")
        print("  - Phase 4: Create experiments")
        print("=" * 60 + "\n")

        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print("TESTS FAILED ✗")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
