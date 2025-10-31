#!/usr/bin/env python3
"""
Bluesky Streaming DAQ Examples for Particle Collider

Demonstrates how to use the StreamingColliderDevice with Resource/Datum
documents for streaming detector data to disk during Bluesky runs.

These examples show the recommended methodology for experiments where:
- DAQ data streams directly to disk (high throughput)
- Bluesky metadata and run documents synchronize with DAQ files
- Data files are timestamped for post-run joining and analysis
"""

from bluesky import RunEngine
from bluesky.plans import count, scan
from bluesky.callbacks import LiveTable
from bluesky.callbacks.best_effort import BestEffortCallback
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from databroker import Broker
import matplotlib.pyplot as plt
import pandas as pd

from bluesky_streaming_collider import create_streaming_collider_device


def streaming_simple_run():
    """
    Example 1: Simple streaming run

    Records control parameters and status in Bluesky documents,
    while detector hits stream to CSV files on disk.

    Document flow:
    - Start Document: Run metadata
    - Resource Documents: Point to pixel/calorimeter CSV files
    - Event Documents: Periodic status readings
    - Datum Documents: Pointers to data within CSV files
    - Stop Document: Run completion
    """
    print("\n" + "=" * 60)
    print("Example 1: Simple Streaming Run")
    print("=" * 60)

    # Create RunEngine and device
    RE = RunEngine({})
    collider = create_streaming_collider_device(data_dir='./streaming_data')

    # Set up live table display
    live_table = LiveTable([
        collider.time_elapsed,
        collider.active_particles,
        collider.total_particles
    ])

    print("\nRunning 10-second data collection...")
    print("  - Bluesky: Recording control parameters and status")
    print("  - DAQ: Streaming pixel and calorimeter hits to CSV files")

    # Run for 10 seconds, reading status every 1 second
    RE(count([collider], num=10, delay=1), live_table)

    print("\nExample 1 complete!")
    print("\nWhat was recorded:")
    print("  - Bluesky documents: Control parameters, run metadata, timestamps")
    print("  - Pixel detector CSV: All pixel hits with timestamps")
    print("  - Calorimeter CSV: All calorimeter hits with timestamps")
    print("\nData files are in: ./streaming_data/")


def streaming_parameter_scan():
    """
    Example 2: Parameter scan with streaming DAQ

    Scans a control parameter while DAQ streams data to disk.
    Each run gets separate data files linked via Resource/Datum documents.
    """
    print("\n" + "=" * 60)
    print("Example 2: Parameter Scan with Streaming DAQ")
    print("=" * 60)

    # Create RunEngine and device
    RE = RunEngine({})
    collider = create_streaming_collider_device(data_dir='./streaming_data')

    # Set up callbacks
    bec = BestEffortCallback()
    RE.subscribe(bec)

    # Set fixed parameters
    collider.speed_max.put(1.0)
    collider.interval_min.put(0.5)
    collider.interval_max.put(1.0)

    # Scan speed_min from 0.3 to 0.9
    print("\nScanning speed_min from 0.3 to 0.9...")
    print("  - Each scan point creates new DAQ files")
    print("  - Resource/Datum documents link files to run")

    @bpp.run_decorator()
    def slow_scan():
        """Scan with delay between points"""
        import numpy as np
        for value in np.linspace(0.3, 0.9, 5):
            yield from bps.mov(collider.speed_min, value)
            yield from bps.sleep(2.0)  # Collect data for 2 seconds
            yield from bps.trigger_and_read([collider])

    RE(slow_scan())

    print("\nExample 2 complete!")


def streaming_with_databroker():
    """
    Example 3: Streaming DAQ with Databroker integration

    Shows how Bluesky's Resource/Datum model integrates with Databroker
    to provide unified access to both metadata and detector data.
    """
    print("\n" + "=" * 60)
    print("Example 3: Streaming DAQ with Databroker")
    print("=" * 60)

    # Create temporary databroker
    db = Broker.named('temp')

    # Create RunEngine and subscribe to databroker
    RE = RunEngine({})
    RE.subscribe(db.insert)

    # Create device
    collider = create_streaming_collider_device(data_dir='./streaming_data')

    # Configure experiment
    md = {
        'purpose': 'Streaming DAQ demonstration',
        'operator': 'Bluesky User',
        'sample': 'Particle Collider Simulation',
        'notes': 'Testing Resource/Datum model for streaming detector data'
    }

    print("\nRunning experiment with metadata...")

    # Simple count plan with metadata
    uid = RE(count([collider], num=5, delay=2, md=md))

    # Retrieve run from databroker
    print("\n" + "-" * 60)
    print("Retrieving data from Databroker...")

    run = db[uid]

    # Show start document (metadata)
    print("\nStart Document (metadata):")
    for key in ['time', 'plan_name', 'purpose', 'operator']:
        if key in run.start:
            print(f"  {key}: {run.start[key]}")

    # Show baseline readings (control parameters at start)
    print("\nBaseline Configuration:")
    baseline = run.baseline.read()
    for signal in ['speed_min', 'speed_max', 'interval_min', 'interval_max']:
        if signal in baseline:
            print(f"  {signal}: {baseline[signal]['value']}")

    # Show event data (periodic readings)
    print("\nEvent Data (status readings):")
    table = run.primary.read()
    print(table[['time_elapsed', 'active_particles', 'total_particles']].to_string(index=False))

    # Show external data references
    print("\nExternal Data Files (via Resource/Datum documents):")
    print("  Note: Actual file access would use databroker's file retrieval")
    print("  Files contain:")
    print("    - Pixel detector: wall_time, simulation_time, particle_id, pixel_number, hit_time")
    print("    - Calorimeter: wall_time, simulation_time, particle_id, segment_number, hit_time, speed, angle")

    print("\nExample 3 complete!")


def streaming_multi_run_experiment():
    """
    Example 4: Multi-run experiment with streaming DAQ

    Demonstrates a realistic experiment workflow:
    - Multiple runs with different parameters
    - Each run gets separate DAQ files
    - All runs linked via Bluesky documents
    - Post-analysis can join data using timestamps
    """
    print("\n" + "=" * 60)
    print("Example 4: Multi-Run Experiment")
    print("=" * 60)

    # Create databroker for persistent storage
    db = Broker.named('temp')

    # Create RunEngine
    RE = RunEngine({})
    RE.subscribe(db.insert)

    # Create device
    collider = create_streaming_collider_device(data_dir='./streaming_data')

    # Experiment parameters to scan
    speed_values = [0.4, 0.6, 0.8]

    print(f"\nRunning {len(speed_values)} experimental conditions...")
    print("Each run will:")
    print("  1. Create separate pixel and calorimeter DAQ files")
    print("  2. Record metadata and control parameters in Bluesky")
    print("  3. Stream detector hits to disk in real-time")
    print("  4. Link files to run via Resource/Datum documents")

    run_uids = []

    for i, speed in enumerate(speed_values):
        print(f"\n--- Run {i+1}/{len(speed_values)}: speed_min = {speed:.1f} ---")

        # Configure this run
        collider.speed_min.put(speed)
        collider.speed_max.put(speed + 0.2)

        # Run metadata
        md = {
            'purpose': 'Speed study',
            'run_number': i + 1,
            'speed_setting': speed,
            'notes': f'Testing speed_min = {speed:.1f}'
        }

        # Execute run (5 seconds of data collection)
        uid = RE(count([collider], num=5, delay=1, md=md))
        run_uids.append(uid)

    # Post-run analysis
    print("\n" + "-" * 60)
    print("Post-Run Analysis")
    print("-" * 60)

    print("\nRun Summary:")
    for i, uid in enumerate(run_uids):
        run = db[uid]
        speed = run.start['speed_setting']
        duration = run.stop['time'] - run.start['time']

        # Get final particle count from last event
        final_particles = run.primary.read()['total_particles'].iloc[-1]

        print(f"\nRun {i+1} (speed={speed:.1f}):")
        print(f"  UID: {uid}")
        print(f"  Duration: {duration:.1f}s")
        print(f"  Total particles: {final_particles}")
        print(f"  DAQ files: pixel_detector_{uid[:8]}.csv, calorimeter_detector_{uid[:8]}.csv")

    print("\n" + "=" * 60)
    print("Example 4 complete!")
    print("\nAll data files are in: ./streaming_data/")
    print("\nFor post-analysis:")
    print("  1. Load Bluesky runs from databroker to get metadata")
    print("  2. Load CSV files to get detector hits")
    print("  3. Join data using timestamps (wall_time and simulation_time)")


def analyze_streaming_data_example():
    """
    Example 5: Post-run data analysis

    Shows how to load and analyze streaming DAQ data after the run,
    joining pixel and calorimeter data using timestamps.
    """
    print("\n" + "=" * 60)
    print("Example 5: Post-Run Data Analysis")
    print("=" * 60)

    print("\nThis example shows how to analyze streaming DAQ data")
    print("after a Bluesky run has completed.")
    print("\nTypical analysis workflow:")

    print("\n1. Load run metadata from Databroker:")
    print("   run = db[uid]")
    print("   metadata = run.start")
    print("   config = run.baseline.read()")

    print("\n2. Get DAQ file paths from Resource documents:")
    print("   # Databroker provides file paths from Resource/Datum documents")
    print("   pixel_file = run.get_resource_by_spec('CSV')[0]")
    print("   calo_file = run.get_resource_by_spec('CSV')[1]")

    print("\n3. Load detector data from CSV files:")
    print("   pixel_data = pd.read_csv(pixel_file)")
    print("   calo_data = pd.read_csv(calo_file)")

    print("\n4. Join data using timestamps:")
    print("   # Merge pixel and calorimeter data on particle_id")
    print("   combined = pd.merge(")
    print("       pixel_data,")
    print("       calo_data,")
    print("       on='particle_id',")
    print("       suffixes=('_pixel', '_calo')")
    print("   )")

    print("\n5. Analyze correlated measurements:")
    print("   # Example: Correlation between pixel position and calorimeter segment")
    print("   correlation = combined[['pixel_number', 'segment_number']].corr()")
    print("   ")
    print("   # Example: Time between pixel hit and calorimeter hit")
    print("   combined['time_diff'] = combined['hit_time_calo'] - combined['hit_time_pixel']")

    print("\n6. Visualize results:")
    print("   plt.scatter(combined['pixel_number'], combined['segment_number'])")
    print("   plt.xlabel('Pixel Number')")
    print("   plt.ylabel('Calorimeter Segment')")
    print("   plt.title(f\"Run {metadata['uid']}: Pixel vs Calorimeter\")")

    print("\nExample 5 complete!")


def main():
    """Run all examples (interactive menu)"""
    examples = {
        '1': ('Simple Streaming Run', streaming_simple_run),
        '2': ('Parameter Scan with Streaming', streaming_parameter_scan),
        '3': ('Databroker Integration', streaming_with_databroker),
        '4': ('Multi-Run Experiment', streaming_multi_run_experiment),
        '5': ('Post-Run Analysis', analyze_streaming_data_example),
    }

    print("\n" + "=" * 60)
    print("Particle Collider Streaming DAQ Examples")
    print("=" * 60)
    print("\nThese examples demonstrate the Resource/Datum methodology for")
    print("streaming detector data to disk during Bluesky runs.")
    print("\nAvailable examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}: {name}")

    choice = input("\nEnter example number (or press Enter for all): ").strip()

    if not choice:
        for key, (name, func) in examples.items():
            func()
    elif choice in examples:
        examples[choice][1]()
    else:
        print("Invalid choice!")


if __name__ == '__main__':
    main()
