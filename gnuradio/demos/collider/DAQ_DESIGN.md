# Calorimeter DAQ Design

## Overview

Add realistic Data Acquisition (DAQ) modeling to the particle collider simulation with proper signal processing characteristics.

## Requirements

### Calorimeter DAQ Specifications
- **Channels**: 64 (one per calorimeter segment)
- **Sample Rate**: 10,000 samples/second (10 kHz)
- **Pulse Characteristics** (when particle hits):
  - Rise time: 10 samples (1 ms at 10 kHz)
  - Decay time: 100 samples (10 ms exponential decay)
  - Amplitude: Proportional to particle speed
  - Total pulse duration: ~110 samples (11 ms)

### Sample Rate vs Simulation Time
- Simulation timestep: 50 ms (dt = 0.05s in update_frame)
- DAQ sample period: 0.1 ms (1/10000 s)
- Samples per simulation frame: 500 samples

## Implementation Stages

### Stage 1: Pulse Shape Design and Testing ✓
**Goal**: Create and verify the pulse waveform function

**Deliverables**:
- `test_daq_pulse.py` - Test script to visualize pulse shapes
- `generate_calorimeter_pulse()` function
- Plots showing:
  - Single pulse with different amplitudes
  - Multiple overlapping pulses (pile-up scenario)
  - Rise time verification (10 samples)
  - Decay time verification (100 samples)

**Pulse Shape Formula**:
```python
# Rise phase (0 to 10 samples): linear ramp
if t <= rise_time:
    pulse[t] = amplitude * (t / rise_time)

# Decay phase (10 to ~110 samples): exponential
else:
    pulse[t] = amplitude * exp(-(t - rise_time) / decay_time)
```

### Stage 2: CalorimeterDAQ Class
**Goal**: Create data structure to manage 64-channel streaming data

**Class Structure**:
```python
class CalorimeterDAQ:
    def __init__(self, sample_rate=10000, num_channels=64):
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.sample_period = 1.0 / sample_rate

        # Ring buffer for continuous data (e.g., last 10 seconds)
        self.buffer_duration = 10.0  # seconds
        self.buffer_size = int(sample_rate * buffer_duration)
        self.data = np.zeros((num_channels, self.buffer_size))
        self.write_index = 0

        # Time tracking
        self.current_time = 0.0
        self.sample_count = 0

    def update(self, dt):
        """Advance DAQ time by dt seconds, generating new samples"""

    def inject_pulse(self, channel, time, amplitude):
        """Inject a pulse into specified channel at given time"""

    def get_channel_data(self, channel, duration=0.1):
        """Get recent data from a channel"""

    def export_data(self, filename):
        """Export DAQ data to file"""
```

**Key Features**:
- Circular buffer to store recent data without unbounded growth
- Time-synchronization with simulation clock
- Pulse injection with proper time alignment
- Multi-pulse handling (overlapping pulses add linearly)

### Stage 3: Integration with Particle Collider
**Goal**: Connect DAQ to particle hit events

**Integration Points**:
1. **Add DAQ to ParticleCollider**:
   ```python
   class ParticleCollider:
       def __init__(self, ...):
           # Existing code...
           self.calorimeter_daq = CalorimeterDAQ()
   ```

2. **Inject pulses on hits** (in `Particle.update()`):
   ```python
   # When particle hits calorimeter
   if self.deflected and distance >= self.calorimeter_radius:
       # Existing hit detection code...

       # NEW: Inject DAQ pulse
       amplitude = self.speed * AMPLITUDE_SCALE  # Scale factor TBD
       collider.calorimeter_daq.inject_pulse(
           channel=self.calorimeter_segment,
           time=current_time,
           amplitude=amplitude
       )
   ```

3. **Update DAQ each frame** (in `ParticleCollider.update()`):
   ```python
   def update(self, dt):
       # Existing particle updates...

       # Update DAQ
       self.calorimeter_daq.update(dt)
   ```

### Stage 4: Data Export and Storage
**Goal**: Save DAQ data for offline analysis

**Export Formats**:
1. **Binary format** (HDF5):
   - Efficient storage for large datasets
   - Structure: `{channel_0: array, channel_1: array, ...}`
   - Metadata: sample_rate, start_time, simulation_parameters

2. **Text format** (CSV) for small datasets:
   - One file per channel or multiplexed format
   - Header with sample rate and timing info

**Export Strategy**:
- Continuous export during simulation (streaming)
- Final dump on simulation close
- Configurable buffer duration

### Stage 5: Visualization (Optional)
**Goal**: Real-time display of DAQ waveforms

**Options**:
1. **Add subplot to main figure**:
   - Show 4-8 selected channels
   - Scrolling waveform display (oscilloscope-style)
   - Highlight recent hits

2. **Separate DAQ viewer window**:
   - Independent matplotlib window
   - Channel selection controls
   - Zoom/pan for detailed inspection

## Technical Considerations

### Performance
- **Memory**: 64 channels × 10 seconds × 10 kHz = 6.4 million samples
  - Using float32: ~25 MB (manageable)
- **CPU**: Pulse injection is O(pulse_length) per hit
  - ~110 samples per pulse
  - Typical: <10 hits per 50ms frame → negligible overhead

### Time Synchronization
- Simulation time: discrete steps (dt = 0.05s)
- DAQ time: continuous samples (0.0001s period)
- Need to map simulation time to DAQ sample indices

### Pulse Pile-up
- Multiple particles can hit same segment before pulse decays
- Pulses should add linearly (realistic detector behavior)
- May need baseline tracking for high rates

## Implementation Order

1. ✓ Create test script (`test_daq_pulse.py`)
2. ✓ Verify pulse shape parameters
3. Create `CalorimeterDAQ` class in new file `calorimeter_daq.py`
4. Add unit tests for DAQ class
5. Integrate DAQ into `particle_collider.py`
6. Test with single particle hits
7. Test with multiple overlapping pulses
8. Add data export functionality
9. (Optional) Add visualization

## Testing Plan

### Unit Tests
- Pulse shape correctness (rise/decay times)
- Time synchronization accuracy
- Multi-pulse addition
- Buffer wraparound behavior

### Integration Tests
- Single particle → single pulse
- Rapid hits → pulse pile-up
- Different particle speeds → different amplitudes
- Long simulations → no memory leaks

## Configuration Parameters

```python
# DAQ Configuration
DAQ_SAMPLE_RATE = 10000      # Hz
DAQ_BUFFER_DURATION = 10.0   # seconds
PULSE_RISE_TIME = 10         # samples (1 ms)
PULSE_DECAY_TIME = 100       # samples (10 ms)
AMPLITUDE_SCALE = 1000.0     # ADC units per speed unit (TBD)
```

## Future Enhancements

1. **Noise modeling**: Add realistic detector noise
2. **ADC quantization**: Discrete amplitude levels
3. **Trigger system**: Event detection and readout windows
4. **Pixel detector DAQ**: Extend to 6400-channel pixel system
5. **Rate-dependent effects**: Baseline shift, dead time
