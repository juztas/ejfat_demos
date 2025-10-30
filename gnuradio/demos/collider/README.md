# Particle Collider Simulation

A Python-based particle collider simulation with visualization, interactive controls, and comprehensive data logging.

## Overview

This simulation models a particle collider with:
- **Target**: Circle of radius 1 at the origin (0, 0)
- **Injection Point**: Particles spawn from (-1, 0)
- **Random Timing**: Particles injected at random intervals (0.5-1.0 seconds by default)
- **Random Speed**: Each particle has a random speed (0.5-1.0 by default)
- **Deflection Physics**: Particles deflect when reaching the target area, with deflection angle (-270° to 270°) and magnitude proportional to particle speed

## Features

### Visualization
- Real-time particle animation
- Color-coded particles (blue before deflection, orange after)
- Particle trajectory trails
- Live statistics display (time, active particles, total count)

### Interactive Controls
- **Speed Min/Max Sliders**: Adjust the range of particle speeds (0.1-1.5)
- **Interval Min/Max Sliders**: Adjust injection timing range (0.1-2.0 seconds)
- **Pause/Resume Button**: Pause or resume the simulation
- **Reset Button**: Clear all particles and restart from time 0
- **Save Button**: Manually save summary statistics at any time

### Data Collection & Logging

The simulation automatically logs comprehensive data for each particle:

**Per-Particle Data:**
- Particle ID
- Speed
- Injection time
- Deflection time
- Deflection angle (degrees)
- Deflection position (x, y)
- Exit time (when particle leaves simulation area)
- Lifetime (total time in simulation)

**Output Files** (timestamped, e.g., `collider_data_20250129_143022.*`):

1. **CSV File** (`*.csv`): Raw particle data for spreadsheet analysis
2. **JSON File** (`*.json`): Summary statistics in structured format
3. **Summary Text** (`*_summary.txt`): Human-readable statistics report

**Statistics Calculated:**
- Speed statistics (mean, std, min, max)
- Deflection angle distribution
- Particle lifetime distribution
- Simulation parameters used

## Requirements

```bash
pip install numpy matplotlib
```

## Usage

### Run the Simulation

```bash
python particle_collider.py
```

### During Simulation

1. **Adjust Parameters**: Use sliders to change particle speed and injection timing in real-time
2. **Pause/Resume**: Click the Pause button to freeze the simulation
3. **Reset**: Click Reset to clear particles and start fresh
4. **Save**: Click Save to generate summary files at any time
5. **Exit**: Close the window to automatically save final summary

### Output Files

All data files are saved in the current directory with timestamps:
- `collider_data_YYYYMMDD_HHMMSS.csv` - Particle data
- `collider_data_YYYYMMDD_HHMMSS.json` - Summary statistics (JSON)
- `collider_data_YYYYMMDD_HHMMSS_summary.txt` - Summary report (text)

## Example Output

```
Particle Collider Simulation Summary
==================================================

Simulation Start: 2025-01-29T14:30:22.123456
Simulation End: 2025-01-29T14:35:45.654321
Total Time: 315.53 seconds
Total Particles: 423

Speed Statistics:
  Mean: 0.752
  Std:  0.142
  Min:  0.503
  Max:  0.998

Deflection Angle Statistics (degrees):
  Mean: -12.34
  Std:  156.78
  Min:  -269.87
  Max:  268.45

Particle Lifetime Statistics (seconds):
  Mean: 2.456
  Std:  0.823
  Min:  1.234
  Max:  4.567
```

## Code Structure

- **`Particle`**: Represents individual particles with physics and data tracking
- **`DataLogger`**: Handles CSV, JSON, and text file generation
- **`ParticleCollider`**: Core simulation engine with configurable parameters
- **`ColliderVisualizer`**: Matplotlib-based visualization with interactive controls

## Customization

You can modify default parameters by editing the `ParticleCollider.__init__()` method:

```python
self.speed_min = 0.5      # Minimum particle speed
self.speed_max = 1.0      # Maximum particle speed
self.interval_min = 0.5   # Minimum injection interval (seconds)
self.interval_max = 1.0   # Maximum injection interval (seconds)
```

Or adjust them in real-time using the interactive sliders!

## Tips

- **Long Runs**: For extended simulations, periodically click "Save" to preserve data
- **Performance**: The simulation keeps the last 20 inactive particles for visualization
- **Analysis**: Import the CSV file into Excel, pandas, or other tools for detailed analysis
- **Parameter Exploration**: Use the sliders to explore how different speed and timing ranges affect particle behavior
