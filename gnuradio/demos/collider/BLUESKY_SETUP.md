# Bluesky Setup for Particle Collider

## Architecture

```
Bluesky RunEngine → XML-RPC (port 8000) → Particle Collider Simulation
```

## Ophyd Device: `ParticleColliderDevice`

**Control Parameters (settable):**
- `speed_min`, `speed_max`: Particle speed range [0.1-1.5]
- `interval_min`, `interval_max`: Injection timing range [0.1-2.0s]

**Measurements (read-only):**
- `time_elapsed`: Simulation time (seconds)
- `active_particles`: Currently active particles
- `total_particles`: Total particles created

## Running Bluesky Examples

```bash
# Start simulation first
python particle_collider.py

# In separate terminal, run examples
python bluesky_examples.py
```

## Key Features

1. **Custom XML-RPC Signals**: Ophyd signals backed by XML-RPC calls to simulation
2. **Scan Rate**: 1 second delay between parameter changes for visible slider updates
3. **Sequential Updates**: Grid scans set parameters sequentially to avoid Ophyd state conflicts
4. **Constraint Validation**: All scans ensure `min < max` for parameters

## Example Scans

- **Example 2**: Speed scan (7 points, ~7s)
- **Example 3**: Interval scan (8 points, ~8s)
- **Example 4**: 2D grid scan (16 points, ~16s)
- **Example 8**: Comprehensive study with metadata (9 points, ~9s)

## Implementation Details

- **File**: `bluesky_collider.py` - Ophyd device definition
- **Examples**: `bluesky_examples.py` - Pre-built scan examples
- **Communication**: XML-RPC over HTTP (same as browser interface)
- **Thread Safety**: Slider synchronization handled in animation loop (main thread)

## Limitations

- Detector data (calorimeter/pixel hits) NOT stored in Bluesky databroker
- Detector data saved separately by simulation to CSV/JSON files
- Simultaneous parameter setting requires sequential `bps.mov()` calls
