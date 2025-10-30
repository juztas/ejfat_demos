# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a particle collider simulation demo that models particle physics with visualization, interactive controls, remote control via XML-RPC, and comprehensive data logging. The simulation includes a pixel detector (6400 pixels) and calorimeter detector (64 segments) arranged around the collision point.

## Running the Simulation

### Basic Usage

```bash
# Run the simulation with visualization
python particle_collider.py
```

The simulation will:
- Display real-time particle animation with matplotlib
- Start an XML-RPC server on port 8000 for remote control
- Log particle data to timestamped CSV/JSON files on exit

### Web Interface

```bash
# Terminal 1: Start the simulation
python particle_collider.py

# Terminal 2: Start the web server
python web_server.py

# Open browser to: http://localhost:8001/collider_control.html
```

### Testing

```bash
# Test XML-RPC connectivity and basic commands
python test_xmlrpc.py

# Test slider synchronization (manual test with live simulation)
python test_slider_sync.py
```

### Bluesky Integration

For automated data acquisition and parameter scans:

```bash
# Terminal 1: Start the simulation
python particle_collider.py

# Terminal 2: Run Bluesky examples
python bluesky_examples.py

# Or use the device directly in Python
python -c "from bluesky_examples import simple_count_example; simple_count_example()"
```

**What Bluesky Records:**
- Control parameters: speed_min, speed_max, interval_min, interval_max
- Measurements: time_elapsed, active_particles, total_particles

**What is NOT in Bluesky:**
- Calorimeter hits (saved separately by simulation to CSV/JSON)
- Pixel detector hits (saved separately by simulation to CSV/JSON)
- Per-particle data (saved separately by simulation to CSV/JSON)

See `BLUESKY_README.md` for detailed documentation.

## Architecture

### Core Components

**`Particle` class**: Individual particle with physics simulation
- Tracks position, velocity, injection/deflection/exit times
- Handles detector hits (pixel detector at radius ~1.8, calorimeter at radius ~2.15)
- Manages particle lifecycle: injection → deflection → pixel detector → calorimeter → fade out
- Each particle has unique ID and collects comprehensive event data

**`DataLogger` class**: Handles all data output
- CSV export with per-particle data (ID, speed, times, angles, positions, detector hits)
- JSON export with summary statistics
- Text summary with human-readable report
- Files timestamped: `collider_data_YYYYMMDD_HHMMSS.*`

**`ParticleCollider` class**: Core simulation engine
- Manages particle injection at random intervals (configurable range)
- Updates all particles each frame
- Tracks statistics (speed, deflection angles, lifetimes, detector hits)
- Provides XML-RPC methods for remote control

**`ColliderVisualizer` class**: Matplotlib visualization
- Real-time animation with color-coded particles (blue→orange after deflection)
- Particle trails for trajectory visualization
- Interactive sliders for speed/interval parameters
- Pause/Resume/Reset/Save buttons
- Status display (time, particle counts)
- Detector visualization (pixel detector ring, calorimeter segments)

### XML-RPC Server

Runs in background thread on `localhost:8000`. Available methods:

**Control:**
- `set_speed_min(value)`, `set_speed_max(value)` - Particle speed range [0.1, 1.5]
- `set_interval_min(value)`, `set_interval_max(value)` - Injection timing [0.1, 2.0s]
- `pause()`, `resume()`, `reset()` - Simulation control

**Query:**
- `get_status()` - Current state (time, counts, parameters, paused status)
- `get_statistics()` - Aggregated statistics (speed, deflection angles, detector hits)

### Physics Model

1. **Injection**: Particles spawn at (-1, 0) with random speed (within configured range)
2. **Approach**: Particles travel toward origin (0, 0) in straight line
3. **Deflection**: At origin, particles deflect at random angle (135° to -135°, i.e., ±135° from original direction)
4. **Pixel Detector**: Particles hit pixel detector at radius ~1.8 (6400 pixels total, 100 per calorimeter segment)
5. **Calorimeter**: Particles hit calorimeter at radius ~2.15 (64 segments covering ±135°)
6. **Fade Out**: Particles fade to transparent over 0.2 seconds after hitting calorimeter

### Web Interface Architecture

```
┌─────────────────────┐
│  Browser            │
│  (port 8001)        │
│  collider_control   │
│  .html              │
└──────────┬──────────┘
           │ HTTP (web_server.py)
           │
           │ XML-RPC calls
           ▼
┌─────────────────────┐
│  Particle Collider  │
│  (port 8000)        │
│  - Simulation       │
│  - XML-RPC Server   │
│  - Matplotlib GUI   │
└─────────────────────┘
```

## Data Output

### Files Generated

All files use timestamp format `YYYYMMDD_HHMMSS`:

- **`collider_data_*.csv`**: Per-particle data with columns:
  - particle_id, speed, injection_time, deflection_time, deflection_angle, deflection_x, deflection_y
  - exit_time, lifetime, pixel_number, pixel_hit_time, calorimeter_segment, calorimeter_hit_time

- **`collider_data_*.json`**: Summary statistics in JSON format
  - Simulation metadata (start/end times, duration, total particles)
  - Speed statistics (mean, std, min, max)
  - Deflection angle statistics
  - Particle lifetime statistics
  - Detector hit statistics (pixel and calorimeter distributions)

- **`collider_data_*_summary.txt`**: Human-readable summary report

### When Files Are Saved

- Automatically on simulation exit (closing window)
- Manually via "Save" button during simulation
- Files always use timestamp from simulation start time

## Important Implementation Details

### Detector Geometry

- **Pixel Detector**: 6400 pixels total at radius ~1.8
  - 64 calorimeter segments × 100 pixels per segment
  - Angular coverage: -135° to +135° (270° total)
  - Pixels numbered 0-6399

- **Calorimeter**: 64 segments at radius ~2.15
  - Angular coverage: -135° to +135° (270° total)
  - Segments numbered 0-63
  - Each segment spans 270°/64 = 4.21875°

### Thread Safety

The XML-RPC server runs in a background daemon thread. Parameter updates from remote clients are thread-safe because:
- Python's GIL ensures atomic reads/writes of simple types (float, bool)
- Parameter changes are validated before being applied
- Simulation reads parameters during each update cycle

### Particle Lifecycle Management

- Active particles are updated each frame
- Inactive particles (after calorimeter fade) are kept in memory for the last 20 particles (for trail visualization)
- All particles are tracked in statistics regardless of active state

## Remote Control Examples

### Python Client

```python
import xmlrpc.client
proxy = xmlrpc.client.ServerProxy("http://localhost:8000/")

# Set parameters
proxy.set_speed_min(0.6)
proxy.set_speed_max(1.2)

# Control simulation
proxy.pause()
status = proxy.get_status()
print(f"Paused: {status['paused']}, Particles: {status['particle_count']}")
proxy.resume()

# Get statistics
stats = proxy.get_statistics()
print(f"Mean deflection angle: {stats['deflection_angle']['mean']:.2f}°")
```

### GNU Radio Integration

The XML-RPC interface allows GNU Radio flowgraphs to control the simulation:

```python
# In a GNU Radio Python block or embedded Python block
import xmlrpc.client
collider = xmlrpc.client.ServerProxy("http://localhost:8000/")
collider.set_speed_min(0.8)  # Adjust based on signal processing
```

## Customization Points

### Default Parameters

Edit `ParticleCollider.__init__()` to change defaults:
- `speed_min`, `speed_max`: Particle speed range
- `interval_min`, `interval_max`: Injection timing range

### Detector Geometry

Edit `Particle.__init__()` to adjust:
- `pixel_radius`: Pixel detector distance from origin
- `calorimeter_radius`: Calorimeter distance from origin
- `fade_duration`: How long particles fade after calorimeter hit

### Visualization

Edit `ColliderVisualizer` properties:
- Trail length: `maxlen` in `Particle.trail`
- Inactive particle retention: `maxlen` in `ColliderVisualizer.inactive_particles`
- Update rate: `interval` in `animation.FuncAnimation`

## Dependencies

### Basic Simulation

```bash
pip install numpy matplotlib
```

No additional dependencies required - uses Python standard library for XML-RPC and HTTP servers.

### Bluesky Integration (Optional)

```bash
pip install -r bluesky_requirements.txt
# Or manually:
pip install bluesky ophyd databroker
```
