#!/usr/bin/env python3
"""
Calorimeter DAQ System

64-channel data acquisition with realistic pulse shapes, bandwidth limiting,
and noise modeling.

Sample rate: 10,000 Hz (10 kHz)
Channels: 64 (one per calorimeter segment)
Pulse characteristics:
  - Rise time: 10 samples (1 ms)
  - Decay time: 100 samples (10 ms exponential)
  - Bandwidth: 1 kHz (10% of sample rate)
  - Noise floor: -80 dB
"""

import numpy as np
from scipy import signal
from collections import deque
import h5py
from datetime import datetime


class CalorimeterDAQ:
    """
    Multi-channel data acquisition system for calorimeter detector

    Manages 64 channels of continuous data acquisition with realistic
    pulse shapes, bandwidth limiting, and noise.
    """

    def __init__(self, sample_rate=10000, num_channels=64, buffer_duration=10.0,
                 noise_floor_db=-80, filter_cutoff_fraction=0.1):
        """
        Initialize DAQ system

        Parameters:
        -----------
        sample_rate : int
            Samples per second (default: 10000 Hz)
        num_channels : int
            Number of channels (default: 64 for calorimeter segments)
        buffer_duration : float
            Buffer duration in seconds (default: 10.0)
        noise_floor_db : float
            Noise floor in dB (default: -80)
        filter_cutoff_fraction : float
            Low-pass filter cutoff as fraction of sample rate (default: 0.1)
        """
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.sample_period = 1.0 / sample_rate
        self.noise_floor_db = noise_floor_db
        self.filter_cutoff_fraction = filter_cutoff_fraction

        # Buffer configuration
        self.buffer_duration = buffer_duration
        self.buffer_size = int(sample_rate * buffer_duration)

        # Circular buffer for each channel (most recent N seconds)
        self.data = np.zeros((num_channels, self.buffer_size), dtype=np.float32)
        self.write_index = 0

        # Time tracking
        self.current_time = 0.0
        self.sample_count = 0

        # Pulse parameters (from test_daq_pulse.py)
        self.rise_samples = 10
        self.decay_samples = 100

        # Pre-generate filter coefficients for efficiency
        cutoff_freq = sample_rate * filter_cutoff_fraction
        nyquist = sample_rate / 2.0
        normalized_cutoff = cutoff_freq / nyquist
        self.filter_b, self.filter_a = signal.butter(4, normalized_cutoff, btype='low', analog=False)

        # Noise amplitude (convert dB to linear)
        self.noise_amplitude = 10 ** (noise_floor_db / 20.0)

        # Track pending pulses for each channel
        # Each entry: {'start_sample': int, 'pulse': ndarray}
        self.pending_pulses = [[] for _ in range(num_channels)]

        # Statistics
        self.total_hits = np.zeros(num_channels, dtype=int)

        # Waterfall display decimation (10 FPS visualization)
        self.waterfall_decimation = 1000  # Peak-hold over 1000 samples per waterfall row
        self.waterfall_peak_hold = np.zeros(num_channels, dtype=np.float32)
        self.waterfall_sample_count = 0
        self.waterfall_rows = 200  # History depth
        self.waterfall_buffer = np.zeros((self.waterfall_rows, num_channels), dtype=np.float32)

        # Oscilloscope trigger system (sparklines)
        self.trigger_level = 0.01  # Threshold for triggering
        self.trigger_capture_length = 1000  # Samples to capture per trigger
        self.trigger_armed = np.ones(num_channels, dtype=bool)  # Ready to trigger
        self.trigger_capturing = np.zeros(num_channels, dtype=bool)  # Currently capturing
        self.trigger_samples = np.zeros((num_channels, self.trigger_capture_length), dtype=np.float32)
        self.trigger_sample_count = np.zeros(num_channels, dtype=int)
        self.trigger_has_data = np.zeros(num_channels, dtype=bool)  # Has captured data to display

        # Free-running mode (continuous display)
        self.free_running = False
        self.free_running_decimation = 500  # Display at 20 Hz (10000/500)
        self.free_running_display_samples = 20  # Show 1 second of data at 20 Hz
        self.free_running_buffer = np.zeros((num_channels, self.free_running_display_samples), dtype=np.float32)
        self.free_running_sample_count = 0

        print(f"CalorimeterDAQ initialized:")
        print(f"  Channels: {num_channels}")
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Buffer: {buffer_duration:.1f} s ({self.buffer_size} samples)")
        print(f"  Filter cutoff: {cutoff_freq:.0f} Hz")
        print(f"  Noise floor: {noise_floor_db} dB")
        print(f"  Waterfall: {self.waterfall_rows} rows @ {sample_rate/self.waterfall_decimation:.0f} FPS")

    def _generate_pulse(self, amplitude):
        """
        Generate single pulse waveform

        Parameters:
        -----------
        amplitude : float
            Peak amplitude (proportional to particle speed)

        Returns:
        --------
        pulse : ndarray
            Pulse waveform
        """
        # Total pulse length
        total_samples = self.rise_samples + 5 * self.decay_samples
        pulse = np.zeros(total_samples, dtype=np.float32)

        # Rise phase: linear ramp
        for i in range(self.rise_samples):
            pulse[i] = amplitude * (i / self.rise_samples)

        # Decay phase: exponential
        for i in range(self.rise_samples, total_samples):
            t_decay = i - self.rise_samples
            pulse[i] = amplitude * np.exp(-t_decay / self.decay_samples)

        # Apply bandwidth limiting
        pulse = signal.filtfilt(self.filter_b, self.filter_a, pulse).astype(np.float32)

        return pulse

    def inject_pulse(self, channel, time, amplitude):
        """
        Inject a pulse into specified channel at given time

        Parameters:
        -----------
        channel : int
            Channel number (0 to num_channels-1)
        time : float
            Injection time in seconds
        amplitude : float
            Pulse amplitude (proportional to particle speed)
        """
        if channel < 0 or channel >= self.num_channels:
            print(f"Warning: Invalid channel {channel}, ignoring pulse")
            return

        # Generate pulse
        pulse = self._generate_pulse(amplitude)

        # Calculate starting sample index
        start_sample = int(time * self.sample_rate)

        # Store pending pulse
        self.pending_pulses[channel].append({
            'start_sample': start_sample,
            'pulse': pulse
        })

        # Update statistics
        self.total_hits[channel] += 1

    def update(self, dt):
        """
        Advance DAQ time by dt seconds, generating new samples

        Parameters:
        -----------
        dt : float
            Time step in seconds
        """
        # Calculate number of new samples to generate
        num_samples = int(dt * self.sample_rate)

        for _ in range(num_samples):
            # Generate noise for all channels
            noise = np.random.normal(0, self.noise_amplitude, self.num_channels).astype(np.float32)

            # Start with noise baseline
            new_samples = noise

            # Add pulses for each channel
            for ch in range(self.num_channels):
                pulse_sum = 0.0

                # Check all pending pulses for this channel
                pulses_to_remove = []
                for i, pulse_info in enumerate(self.pending_pulses[ch]):
                    start_sample = pulse_info['start_sample']
                    pulse = pulse_info['pulse']

                    # Calculate index within pulse
                    pulse_idx = self.sample_count - start_sample

                    # Add pulse value if within range
                    if 0 <= pulse_idx < len(pulse):
                        pulse_sum += pulse[pulse_idx]

                    # Mark for removal if complete
                    if pulse_idx >= len(pulse):
                        pulses_to_remove.append(i)

                # Remove completed pulses (in reverse order to preserve indices)
                for i in reversed(pulses_to_remove):
                    del self.pending_pulses[ch][i]

                # Add pulse contribution
                new_samples[ch] += pulse_sum

            # Write to circular buffer
            self.data[:, self.write_index] = new_samples
            self.write_index = (self.write_index + 1) % self.buffer_size

            # Peak-hold for waterfall display (track maximum value)
            self.waterfall_peak_hold = np.maximum(self.waterfall_peak_hold, new_samples)
            self.waterfall_sample_count += 1

            # Update waterfall when we have enough samples
            if self.waterfall_sample_count >= self.waterfall_decimation:
                # Use the peak value from this decimation period
                new_row = self.waterfall_peak_hold.copy()

                # Scroll waterfall up (shift rows up, newest at bottom)
                self.waterfall_buffer[1:] = self.waterfall_buffer[:-1]
                self.waterfall_buffer[0] = new_row

                # Reset peak hold to zero for next period
                self.waterfall_peak_hold.fill(0)
                self.waterfall_sample_count = 0

            # Oscilloscope trigger logic (process each channel independently)
            if not self.free_running:
                # Triggered mode
                for ch in range(self.num_channels):
                    sample_value = new_samples[ch]

                    # Check for trigger condition
                    if self.trigger_armed[ch] and sample_value > self.trigger_level:
                        # Start capturing
                        self.trigger_armed[ch] = False
                        self.trigger_capturing[ch] = True
                        self.trigger_sample_count[ch] = 0
                        self.trigger_has_data[ch] = False

                    # Capture samples if triggered
                    if self.trigger_capturing[ch]:
                        idx = self.trigger_sample_count[ch]
                        if idx < self.trigger_capture_length:
                            self.trigger_samples[ch, idx] = sample_value
                            self.trigger_sample_count[ch] += 1
                        else:
                            # Capture complete - re-arm for next trigger
                            self.trigger_capturing[ch] = False
                            self.trigger_armed[ch] = True
                            self.trigger_has_data[ch] = True
            else:
                # Free-running mode - continuously update buffer
                # Decimate to 20 Hz (every 500th sample)
                if self.free_running_sample_count % self.free_running_decimation == 0:
                    # Shift buffer right and add new sample at left (newest data at time=0)
                    self.free_running_buffer[:, 1:] = self.free_running_buffer[:, :-1]
                    self.free_running_buffer[:, 0] = new_samples
                self.free_running_sample_count += 1

            # Update counters
            self.sample_count += 1
            self.current_time += self.sample_period

    def get_channel_data(self, channel, duration=None, num_samples=None):
        """
        Get recent data from a channel

        Parameters:
        -----------
        channel : int
            Channel number
        duration : float, optional
            Duration in seconds (alternative to num_samples)
        num_samples : int, optional
            Number of samples to retrieve

        Returns:
        --------
        time : ndarray
            Time array
        data : ndarray
            Channel data
        """
        if channel < 0 or channel >= self.num_channels:
            raise ValueError(f"Invalid channel {channel}")

        # Determine number of samples
        if num_samples is None:
            if duration is None:
                num_samples = self.buffer_size
            else:
                num_samples = int(duration * self.sample_rate)

        num_samples = min(num_samples, self.buffer_size)

        # Extract data (handling circular buffer wraparound)
        if self.write_index >= num_samples:
            # Simple case: data is contiguous
            data = self.data[channel, self.write_index - num_samples:self.write_index]
        else:
            # Wraparound case
            samples_from_end = num_samples - self.write_index
            data = np.concatenate([
                self.data[channel, -samples_from_end:],
                self.data[channel, :self.write_index]
            ])

        # Generate time array
        end_time = self.current_time
        start_time = end_time - (num_samples * self.sample_period)
        time = np.linspace(start_time, end_time, num_samples, endpoint=False)

        return time, data

    def get_all_channels(self, duration=None):
        """
        Get recent data from all channels

        Parameters:
        -----------
        duration : float, optional
            Duration in seconds (default: entire buffer)

        Returns:
        --------
        time : ndarray
            Time array
        data : ndarray
            Multi-channel data (num_channels × num_samples)
        """
        if duration is None:
            num_samples = self.buffer_size
        else:
            num_samples = int(duration * self.sample_rate)

        num_samples = min(num_samples, self.buffer_size)

        # Extract data for all channels
        data = np.zeros((self.num_channels, num_samples), dtype=np.float32)

        for ch in range(self.num_channels):
            _, ch_data = self.get_channel_data(ch, num_samples=num_samples)
            data[ch, :] = ch_data

        # Generate time array
        end_time = self.current_time
        start_time = end_time - (num_samples * self.sample_period)
        time = np.linspace(start_time, end_time, num_samples, endpoint=False)

        return time, data

    def export_hdf5(self, filename, duration=None):
        """
        Export DAQ data to HDF5 file

        Parameters:
        -----------
        filename : str
            Output filename
        duration : float, optional
            Duration to export (default: entire buffer)
        """
        time, data = self.get_all_channels(duration=duration)

        with h5py.File(filename, 'w') as f:
            # Metadata
            f.attrs['sample_rate'] = self.sample_rate
            f.attrs['num_channels'] = self.num_channels
            f.attrs['start_time'] = time[0]
            f.attrs['end_time'] = time[-1]
            f.attrs['duration'] = time[-1] - time[0]
            f.attrs['timestamp'] = datetime.now().isoformat()
            f.attrs['noise_floor_db'] = self.noise_floor_db
            f.attrs['filter_cutoff_hz'] = self.sample_rate * self.filter_cutoff_fraction

            # Time array
            f.create_dataset('time', data=time, compression='gzip', compression_opts=4)

            # Channel data
            f.create_dataset('channels', data=data, compression='gzip', compression_opts=4)

            # Hit counts
            f.create_dataset('hit_counts', data=self.total_hits)

        print(f"Exported {len(time)} samples ({duration if duration else self.buffer_duration:.1f}s) to {filename}")

    def get_statistics(self):
        """
        Get DAQ statistics

        Returns:
        --------
        stats : dict
            Statistics dictionary
        """
        return {
            'current_time': self.current_time,
            'sample_count': self.sample_count,
            'total_hits': int(np.sum(self.total_hits)),
            'hits_per_channel': self.total_hits.tolist(),
            'max_hits_channel': int(np.argmax(self.total_hits)),
            'max_hits': int(np.max(self.total_hits)),
            'active_pulses': sum(len(pulses) for pulses in self.pending_pulses)
        }

    def reset(self):
        """Reset DAQ to initial state"""
        self.data.fill(0.0)
        self.write_index = 0
        self.current_time = 0.0
        self.sample_count = 0
        self.total_hits.fill(0)
        self.pending_pulses = [[] for _ in range(self.num_channels)]
        # Reset waterfall
        self.waterfall_buffer.fill(0.0)
        self.waterfall_peak_hold.fill(0.0)
        self.waterfall_sample_count = 0
        # Reset triggers
        self.trigger_armed.fill(True)
        self.trigger_capturing.fill(False)
        self.trigger_samples.fill(0.0)
        self.trigger_sample_count.fill(0)
        self.trigger_has_data.fill(False)
        print("DAQ reset")
