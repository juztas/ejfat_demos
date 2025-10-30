# Bluesky Examples Code Structure

## Module Organization

```python
# Bluesky core
from bluesky import RunEngine
from bluesky.plans import count, scan
import bluesky.plan_stubs as bps        # Low-level plan primitives
import bluesky.preprocessors as bpp    # Plan decorators

# Callbacks for live display
from bluesky.callbacks import LiveTable, LivePlot
from bluesky.callbacks.best_effort import BestEffortCallback

# Data persistence
from databroker import Broker

# Device interface
from bluesky_collider import create_collider_device
```

## Standard Example Pattern

Each example function follows this structure:

```python
def example_function():
    # 1. Create RunEngine (manages plan execution)
    RE = RunEngine({})

    # 2. Create device (Ophyd interface to collider)
    collider = create_collider_device()

    # 3. Set up callbacks (optional - for live display)
    live_table = LiveTable([collider.time_elapsed, ...])

    # 4. Configure fixed parameters
    collider.speed_max.put(1.0)

    # 5. Define and run plan
    RE(scan([collider], collider.speed_min, 0.3, 0.9, 7), live_table)
```

## Custom Plan Pattern

For scans requiring delays or special logic:

```python
@bpp.run_decorator()  # Wraps plan with open_run/close_run
def custom_scan():
    """Custom plan generator function"""
    for value in values:
        # Move motors/parameters
        yield from bps.mov(collider.speed_min, value)

        # Sleep between changes
        yield from bps.sleep(1.0)

        # Trigger and read detectors
        yield from bps.trigger_and_read([collider])

# Execute the plan
RE(custom_scan())
```

## Key Bluesky Concepts Used

### Plan Stubs (`bps`)
Low-level building blocks yielded in custom plans:
- `bps.mov()` - Move positioner to value
- `bps.sleep()` - Delay execution
- `bps.trigger_and_read()` - Acquire data point

### Preprocessors (`bpp`)
Decorators that modify plan behavior:
- `@bpp.run_decorator()` - Wraps plan with run start/stop documents
- `@bpp.run_decorator(md=metadata)` - Adds metadata to run

### RunEngine (`RE`)
- Executes generator-based plans
- Emits documents (start, descriptor, event, stop)
- Broadcasts to subscribed callbacks

### Callbacks
- `LiveTable` - Print data in table format
- `LivePlot` - Real-time plotting
- `BestEffortCallback` - Automatic plots and tables
- `Broker.insert` - Save to databroker

## Generator Functions (Plans)

Plans are Python generators that `yield from` messages:

```python
def my_plan():
    # Each yield from sends a message to RunEngine
    yield from bps.mov(motor, position)  # "Move motor"
    yield from bps.sleep(1.0)            # "Sleep 1 second"
    yield from bps.trigger_and_read([det])  # "Read detector"
```

RunEngine processes these messages and controls execution.

## Constraint Management

Parameter constraints enforced by:
1. Setting max values before scanning min values
2. Limiting scan ranges to stay within valid bounds
3. Sequential parameter updates to avoid conflicts

```python
# Set max high enough
collider.speed_max.put(1.2)

# Scan min below max
for value in np.linspace(0.3, 0.9, 7):  # 0.9 < 1.2 ✓
    yield from bps.mov(collider.speed_min, value)
```

## Main Function Structure

```python
def main():
    # Dictionary mapping choices to (name, function)
    examples = {
        '1': ('Simple Count', simple_count_example),
        '2': ('Speed Scan', speed_scan_example),
        # ...
    }

    # Interactive menu
    choice = input("Enter example number: ")

    # Execute selected example or all
    if choice == 'all':
        for key, (name, func) in examples.items():
            if func is not None:
                func()
    else:
        examples[choice][1]()  # Call the function
```

## Device Interface

```python
# Factory function returns configured device
collider = create_collider_device()

# Device has settable signals (controls)
collider.speed_min.put(0.5)

# And readable signals (measurements)
value = collider.time_elapsed.get()

# Bluesky plans use the device as a detector
yield from bps.trigger_and_read([collider])
```

## Error Handling

- Ophyd signals validate constraints in `put()` method
- Failed puts print error messages but don't crash
- Sequential `bps.mov()` calls avoid state machine conflicts
- 1-second delays allow time for XML-RPC round-trips
