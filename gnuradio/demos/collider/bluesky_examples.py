#!/usr/bin/env python3
"""
Example Bluesky plans for the Particle Collider

Demonstrates how to use the ParticleColliderDevice with Bluesky
for automated data acquisition and parameter scans.
"""

from bluesky import RunEngine
from bluesky.plans import count, scan, grid_scan
from bluesky.callbacks import LiveTable, LivePlot
from bluesky.callbacks.best_effort import BestEffortCallback
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from databroker import Broker
import matplotlib.pyplot as plt

from bluesky_collider import create_collider_device


def simple_count_example():
    """
    Example 1: Simple counting - monitor particle production over time

    Takes 10 readings at 1-second intervals, recording:
    - Time elapsed
    - Active particles
    - Total particles
    - Current speed and interval settings
    """
    print("\n" + "=" * 60)
    print("Example 1: Simple Count - Monitor Particle Production")
    print("=" * 60)

    # Create RunEngine and device
    RE = RunEngine({})
    collider = create_collider_device()

    # Set up live table display
    live_table = LiveTable([
        collider.time_elapsed,
        collider.active_particles,
        collider.total_particles
    ])

    # Run the plan
    print("\nCollecting 10 data points at 1-second intervals...")
    RE(count([collider], num=10, delay=1), live_table)

    print("\nExample 1 complete!")


def speed_scan_example():
    """
    Example 2: Speed scan - vary particle speed and observe particle production

    Scans speed_min from 0.3 to 0.9 in 7 steps, recording particle counts
    at each setting. Useful for understanding how speed affects injection rate.
    """
    print("\n" + "=" * 60)
    print("Example 2: Speed Scan - Vary Minimum Particle Speed")
    print("=" * 60)

    # Create RunEngine and device
    RE = RunEngine({})
    collider = create_collider_device()

    # Set up best effort callback (auto-generates plots)
    bec = BestEffortCallback()
    RE.subscribe(bec)

    # Set fixed parameters
    collider.speed_max.put(1.0)
    collider.interval_min.put(0.5)
    collider.interval_max.put(1.0)

    # Scan speed_min from 0.3 to 0.9 with delay between points
    print("\nScanning speed_min from 0.3 to 0.9...")
    print("At each point, collecting data (1s delay between changes)...")

    # Custom plan with sleep between each scan point
    @bpp.run_decorator()
    def slow_scan():
        """Scan with delay between points for visible slider movement"""
        import numpy as np
        for value in np.linspace(0.3, 0.9, 7):
            yield from bps.mov(collider.speed_min, value)
            yield from bps.sleep(1.0)  # Delay to see slider move
            yield from bps.trigger_and_read([collider])

    RE(slow_scan())

    print("\nExample 2 complete!")


def interval_scan_example():
    """
    Example 3: Interval scan - vary injection timing

    Scans interval_min to see how injection rate affects particle accumulation.
    """
    print("\n" + "=" * 60)
    print("Example 3: Interval Scan - Vary Injection Timing")
    print("=" * 60)

    # Create RunEngine and device
    RE = RunEngine({})
    collider = create_collider_device()

    # Set up live display
    live_table = LiveTable([
        collider.interval_min,
        collider.time_elapsed,
        collider.active_particles,
        collider.total_particles
    ])

    # Fix speed parameters
    collider.speed_min.put(0.5)
    collider.speed_max.put(1.0)
    collider.interval_max.put(2.0)  # Set max high enough for scan range

    # Scan interval_min with delay between points
    print("\nScanning interval_min from 0.2 to 1.4 (1s delay between changes)...")

    # Custom plan with sleep between each scan point
    @bpp.run_decorator()
    def slow_interval_scan():
        """Scan with delay between points for visible slider movement"""
        import numpy as np
        for value in np.linspace(0.2, 1.4, 8):  # Stop at 1.4 to stay below max (2.0)
            yield from bps.mov(collider.interval_min, value)
            yield from bps.sleep(1.0)  # Delay to see slider move
            yield from bps.trigger_and_read([collider])

    RE(slow_interval_scan(), live_table)

    print("\nExample 3 complete!")


def grid_scan_example():
    """
    Example 4: 2D grid scan - speed vs interval

    Performs a 2D scan varying both speed_min and interval_min,
    creating a parameter space map of particle production.
    """
    print("\n" + "=" * 60)
    print("Example 4: 2D Grid Scan - Speed vs Interval")
    print("=" * 60)

    # Create RunEngine and device
    RE = RunEngine({})
    collider = create_collider_device()

    # Set up callbacks
    bec = BestEffortCallback()
    RE.subscribe(bec)

    # Fix max values
    collider.speed_max.put(1.0)
    collider.interval_max.put(1.5)

    # 2D grid scan with delay between points
    print("\nScanning speed_min (0.3-0.9) vs interval_min (0.3-1.2)...")
    print("(1s delay between changes)...")

    # Custom 2D grid scan with delays
    @bpp.run_decorator()
    def slow_grid_scan():
        """Grid scan with delay between points for visible slider movement"""
        import numpy as np
        speed_values = np.linspace(0.3, 0.9, 4)
        interval_values = np.linspace(0.3, 1.2, 4)

        for speed in speed_values:
            for interval in interval_values:
                # Set parameters sequentially to avoid Ophyd state machine issues
                yield from bps.mov(collider.speed_min, speed)
                yield from bps.mov(collider.interval_min, interval)
                yield from bps.sleep(1.0)  # Delay to see sliders move
                yield from bps.trigger_and_read([collider])

    RE(slow_grid_scan())

    print("\nExample 4 complete!")


def custom_plan_with_pause():
    """
    Example 5: Custom plan with pause/resume

    Demonstrates a custom plan that pauses the simulation,
    changes parameters, resumes, and records data.
    """
    print("\n" + "=" * 60)
    print("Example 5: Custom Plan - Pause, Configure, Resume")
    print("=" * 60)

    # Create RunEngine and device
    RE = RunEngine({})
    collider = create_collider_device()

    def pause_and_configure():
        """Custom plan that pauses, configures, resumes"""
        # Pause simulation
        yield from bps.mv(collider.pause, True)  # Note: using device method instead

        # Configure parameters
        print("\nConfiguring parameters while paused...")
        yield from bps.mv(collider.speed_min, 0.7)
        yield from bps.mv(collider.speed_max, 1.3)
        yield from bps.mv(collider.interval_min, 0.3)
        yield from bps.mv(collider.interval_max, 0.8)

        # Resume simulation
        yield from bps.mv(collider.resume, True)

        # Collect data
        print("\nCollecting data with new parameters...")
        yield from count([collider], num=10, delay=1)

    # Alternative: simpler custom plan using device methods directly
    def simple_configure_and_run():
        """Simpler approach using device methods"""
        # Pause
        collider.pause()
        print("\nSimulation paused")

        # Configure
        print("Setting new parameters...")
        yield from bps.mv(collider.speed_min, 0.7)
        yield from bps.mv(collider.speed_max, 1.3)

        # Resume
        collider.resume()
        print("Simulation resumed")

        # Acquire data
        yield from count([collider], num=10, delay=1)

    live_table = LiveTable([collider.time_elapsed, collider.total_particles])

    print("\nRunning custom plan...")
    RE(simple_configure_and_run(), live_table)

    print("\nExample 5 complete!")


def timed_acquisition_example():
    """
    Example 6: Time-based acquisition

    Run for a specific duration, recording at regular intervals.
    Useful for long-duration stability measurements.
    """
    print("\n" + "=" * 60)
    print("Example 6: Timed Acquisition - 30 seconds")
    print("=" * 60)

    # Create RunEngine and device
    RE = RunEngine({})
    collider = create_collider_device()

    # Set up live plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    live_plot1 = LivePlot(
        collider.total_particles.name,
        x=collider.time_elapsed.name,
        ax=ax1
    )
    ax1.set_ylabel('Total Particles')

    live_plot2 = LivePlot(
        collider.active_particles.name,
        x=collider.time_elapsed.name,
        ax=ax2
    )
    ax2.set_ylabel('Active Particles')
    ax2.set_xlabel('Time (s)')

    # Run for 30 seconds, sampling every 2 seconds
    print("\nAcquiring data for 30 seconds (15 points)...")
    RE(count([collider], num=15, delay=2), [live_plot1, live_plot2])

    plt.tight_layout()
    plt.savefig('collider_timed_acquisition.png')
    print("\nPlot saved to: collider_timed_acquisition.png")

    print("\nExample 6 complete!")


def databroker_example():
    """
    Example 7: Using Databroker for persistent storage

    Demonstrates how to use Databroker to save and retrieve
    experimental data for later analysis.
    """
    print("\n" + "=" * 60)
    print("Example 7: Databroker Integration")
    print("=" * 60)

    # Create temporary databroker
    db = Broker.named('temp')

    # Create RunEngine and subscribe to databroker
    RE = RunEngine({})
    RE.subscribe(db.insert)

    # Create device
    collider = create_collider_device()

    # Run a scan
    print("\nRunning scan and storing in databroker...")
    collider.speed_max.put(1.2)  # Set max high enough for scan range

    # Use slow scan with delays for visible slider movement
    @bpp.run_decorator()
    def slow_databroker_scan():
        """Scan with delay between points for visible slider movement"""
        import numpy as np
        for value in np.linspace(0.3, 0.9, 5):
            yield from bps.mov(collider.speed_min, value)
            yield from bps.sleep(1.0)  # Delay to see slider move
            yield from bps.trigger_and_read([collider])

    uid = RE(slow_databroker_scan())

    # Retrieve and analyze data
    print("\nRetrieving data from databroker...")
    header = db[uid]
    table = header.table()

    print("\nData summary:")
    print(table[[
        collider.speed_min.name,
        collider.time_elapsed.name,
        collider.total_particles.name
    ]])

    print("\nExample 7 complete!")


def comprehensive_parameter_study():
    """
    Example 8: Comprehensive parameter study with metadata

    Performs a systematic study with proper metadata annotation,
    demonstrating best practices for experiment documentation.
    """
    print("\n" + "=" * 60)
    print("Example 8: Comprehensive Parameter Study")
    print("=" * 60)

    # Create RunEngine with metadata
    RE = RunEngine({})
    collider = create_collider_device()

    # Set up callbacks
    bec = BestEffortCallback()
    RE.subscribe(bec)

    # Define experiment metadata
    md = {
        'purpose': 'Speed sensitivity study',
        'operator': 'Bluesky User',
        'sample': 'Particle Collider Simulation',
        'notes': 'Investigating effect of speed_min on particle production rate'
    }

    # Reset simulation to known state
    print("\nResetting simulation to known state...")
    collider.reset()

    # Configure fixed parameters
    collider.speed_max.put(1.2)  # Set max high enough for scan range
    collider.interval_min.put(0.5)
    collider.interval_max.put(1.0)

    # Run scan with metadata and delays for visible slider movement
    print("\nRunning parameter study (1s delay between changes)...")

    @bpp.run_decorator(md=md)
    def slow_study_scan():
        """Scan with delay between points for visible slider movement"""
        import numpy as np
        for value in np.linspace(0.2, 0.9, 9):
            yield from bps.mov(collider.speed_min, value)
            yield from bps.sleep(1.0)  # Delay to see slider move
            yield from bps.trigger_and_read([collider])

    RE(slow_study_scan())

    print("\nExample 8 complete!")


def main():
    """Run all examples (interactive menu)"""
    examples = {
        '1': ('Simple Count', simple_count_example),
        '2': ('Speed Scan', speed_scan_example),
        '3': ('Interval Scan', interval_scan_example),
        '4': ('2D Grid Scan', grid_scan_example),
        '5': ('Custom Plan with Pause', custom_plan_with_pause),
        '6': ('Timed Acquisition', timed_acquisition_example),
        '7': ('Databroker Integration', databroker_example),
        '8': ('Comprehensive Study', comprehensive_parameter_study),
        'all': ('Run All Examples', None),
    }

    print("\n" + "=" * 60)
    print("Particle Collider Bluesky Examples")
    print("=" * 60)
    print("\nAvailable examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}: {name}")

    choice = input("\nEnter example number (or 'all'): ").strip()

    if choice == 'all':
        for key, (name, func) in examples.items():
            if key != 'all':
                func()
    elif choice in examples and examples[choice][1] is not None:
        examples[choice][1]()
    else:
        print("Invalid choice!")


if __name__ == '__main__':
    main()
