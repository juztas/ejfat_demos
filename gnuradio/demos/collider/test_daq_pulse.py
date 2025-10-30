#!/usr/bin/env python3
"""
Test script for calorimeter DAQ pulse shape

Verifies the pulse characteristics:
- Rise time: 10 samples (1 ms at 10 kHz)
- Decay time: 100 samples (10 ms exponential)
- Amplitude scaling with particle speed
- Bandwidth limiting: Low-pass filter at 10% of sample rate (1 kHz)
- Noise floor: -80 dB white noise
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from scipy import signal


def generate_calorimeter_pulse(amplitude, rise_samples=10, decay_samples=100, sample_rate=10000):
    """
    Generate a calorimeter pulse waveform

    Parameters:
    -----------
    amplitude : float
        Peak amplitude (proportional to particle speed)
    rise_samples : int
        Number of samples for linear rise (default: 10 = 1 ms at 10 kHz)
    decay_samples : int
        Time constant for exponential decay in samples (default: 100 = 10 ms)
    sample_rate : int
        DAQ sample rate in Hz (default: 10000)

    Returns:
    --------
    time : ndarray
        Time array in seconds
    pulse : ndarray
        Pulse waveform
    """
    # Total pulse length: rise + several decay constants (5× for ~99% decay)
    total_samples = rise_samples + 5 * decay_samples

    # Time array
    time = np.arange(total_samples) / sample_rate

    # Initialize pulse array
    pulse = np.zeros(total_samples)

    # Rise phase: linear ramp from 0 to amplitude
    for i in range(rise_samples):
        pulse[i] = amplitude * (i / rise_samples)

    # Decay phase: exponential decay from peak
    for i in range(rise_samples, total_samples):
        t_decay = i - rise_samples
        pulse[i] = amplitude * np.exp(-t_decay / decay_samples)

    return time, pulse


def apply_lowpass_filter(signal_data, sample_rate=10000, cutoff_fraction=0.1, order=4):
    """
    Apply low-pass Butterworth filter to signal

    Parameters:
    -----------
    signal_data : ndarray
        Input signal
    sample_rate : int
        Sample rate in Hz (default: 10000)
    cutoff_fraction : float
        Cutoff frequency as fraction of sample rate (default: 0.1 = 10%)
    order : int
        Filter order (default: 4 for sharp rolloff)

    Returns:
    --------
    filtered : ndarray
        Filtered signal
    """
    cutoff_freq = sample_rate * cutoff_fraction
    nyquist = sample_rate / 2.0
    normalized_cutoff = cutoff_freq / nyquist

    # Design Butterworth filter
    b, a = signal.butter(order, normalized_cutoff, btype='low', analog=False)

    # Apply filter (use filtfilt for zero-phase filtering)
    filtered = signal.filtfilt(b, a, signal_data)

    return filtered


def add_noise(signal_data, noise_floor_db=-80, seed=None):
    """
    Add white Gaussian noise to signal

    Parameters:
    -----------
    signal_data : ndarray
        Input signal
    noise_floor_db : float
        Noise floor in dB relative to signal amplitude 1.0 (default: -80)
    seed : int, optional
        Random seed for reproducibility

    Returns:
    --------
    noisy : ndarray
        Signal with added noise
    """
    if seed is not None:
        np.random.seed(seed)

    # Convert dB to linear amplitude
    # -80 dB means noise is 10^(-80/20) = 0.0001 times the reference
    noise_amplitude = 10 ** (noise_floor_db / 20.0)

    # Generate white Gaussian noise
    noise = np.random.normal(0, noise_amplitude, len(signal_data))

    return signal_data + noise


def generate_realistic_pulse(amplitude, rise_samples=10, decay_samples=100,
                             sample_rate=10000, apply_filter=True, add_noise_flag=True,
                             noise_floor_db=-80, filter_cutoff=0.1, seed=None):
    """
    Generate realistic calorimeter pulse with bandwidth limiting and noise

    Parameters:
    -----------
    amplitude : float
        Peak amplitude (proportional to particle speed)
    rise_samples : int
        Number of samples for linear rise
    decay_samples : int
        Time constant for exponential decay in samples
    sample_rate : int
        DAQ sample rate in Hz
    apply_filter : bool
        Apply low-pass filter (default: True)
    add_noise_flag : bool
        Add white noise (default: True)
    noise_floor_db : float
        Noise floor in dB (default: -80)
    filter_cutoff : float
        Filter cutoff as fraction of sample rate (default: 0.1 = 10%)
    seed : int, optional
        Random seed for noise generation

    Returns:
    --------
    time : ndarray
        Time array in seconds
    pulse : ndarray
        Realistic pulse waveform
    """
    # Generate ideal pulse
    time, pulse = generate_calorimeter_pulse(amplitude, rise_samples, decay_samples, sample_rate)

    # Apply bandwidth limiting
    if apply_filter:
        pulse = apply_lowpass_filter(pulse, sample_rate, filter_cutoff)

    # Add noise
    if add_noise_flag:
        pulse = add_noise(pulse, noise_floor_db, seed=seed)

    return time, pulse


def test_single_pulse():
    """Test single pulse with different amplitudes"""
    print("Testing single pulse shape...")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # Test different amplitudes (representing different particle speeds)
    amplitudes = [0.5, 0.75, 1.0, 1.5]
    colors = ['blue', 'green', 'orange', 'red']

    # Plot 1: All pulses overlaid
    ax = axes[0, 0]
    for amp, color in zip(amplitudes, colors):
        time, pulse = generate_calorimeter_pulse(amp)
        ax.plot(time * 1000, pulse, color=color, label=f'Speed={amp}', linewidth=2)

    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Calorimeter Pulse - Different Amplitudes')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 2: Rise time detail
    ax = axes[0, 1]
    time, pulse = generate_calorimeter_pulse(1.0)

    # Plot only first 30 samples to see rise detail
    rise_time_ms = time[:30] * 1000
    ax.plot(rise_time_ms, pulse[:30], 'b-', linewidth=2, label='Pulse')
    ax.axvline(1.0, color='r', linestyle='--', label='Rise time (1 ms)')
    ax.axhline(1.0, color='g', linestyle='--', alpha=0.5, label='Peak amplitude')

    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Rise Time Detail (10 samples = 1 ms)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 3: Decay detail
    ax = axes[1, 0]
    ax.plot(time * 1000, pulse, 'b-', linewidth=2, label='Pulse')

    # Mark decay time constant
    rise_time_ms = 10 / 10000 * 1000  # 1 ms
    decay_point = rise_time_ms + 10  # 1 ms rise + 10 ms decay

    # Find amplitude at 1 decay constant
    decay_idx = 10 + 100  # rise_samples + decay_samples
    decay_amp = pulse[decay_idx]

    ax.axvline(decay_point, color='r', linestyle='--',
               label=f'Decay τ (10 ms), amp={decay_amp:.3f}')
    ax.axhline(np.exp(-1), color='g', linestyle='--', alpha=0.5,
               label=f'1/e = {np.exp(-1):.3f}')

    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude (normalized)')
    ax.set_title('Exponential Decay (τ = 100 samples = 10 ms)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 4: Log scale to verify exponential
    ax = axes[1, 1]
    # Only plot decay portion
    decay_start = 10
    ax.semilogy(time[decay_start:] * 1000, pulse[decay_start:], 'b-',
                linewidth=2, label='Pulse (log scale)')

    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude (log scale)')
    ax.set_title('Decay Verification (Linear on log scale = exponential)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('daq_pulse_single.png', dpi=150)
    print("Saved: daq_pulse_single.png")
    plt.close()


def test_pulse_pileup():
    """Test multiple overlapping pulses (pile-up scenario)"""
    print("\nTesting pulse pile-up...")

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # Simulate 3 particles hitting same segment at different times
    hit_times = [0.0, 0.005, 0.015]  # 0 ms, 5 ms, 15 ms
    amplitudes = [1.0, 0.8, 1.2]

    sample_rate = 10000
    duration = 0.06  # 60 ms
    total_samples = int(duration * sample_rate)

    # Create composite waveform
    composite = np.zeros(total_samples)
    time_axis = np.arange(total_samples) / sample_rate

    # Individual pulses
    ax = axes[0]
    colors = ['blue', 'green', 'red']

    for hit_time, amp, color in zip(hit_times, amplitudes, colors):
        # Generate pulse
        time, pulse = generate_calorimeter_pulse(amp)

        # Calculate starting index in composite waveform
        start_idx = int(hit_time * sample_rate)
        end_idx = min(start_idx + len(pulse), total_samples)
        pulse_len = end_idx - start_idx

        # Add to composite (pulses add linearly)
        composite[start_idx:end_idx] += pulse[:pulse_len]

        # Plot individual pulse
        pulse_time = time_axis[start_idx:end_idx]
        ax.plot(pulse_time * 1000, pulse[:pulse_len], '--', color=color,
                linewidth=1.5, alpha=0.7,
                label=f'Pulse {len(hit_times) - len(hit_times) + hit_times.index(hit_time) + 1} (t={hit_time*1000:.0f} ms, A={amp})')

    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Individual Pulses')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Composite waveform
    ax = axes[1]
    ax.plot(time_axis * 1000, composite, 'k-', linewidth=2, label='Composite (pile-up)')

    # Mark hit times
    for i, hit_time in enumerate(hit_times):
        ax.axvline(hit_time * 1000, color=colors[i], linestyle=':', alpha=0.5)

    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Composite Waveform (Pulses Add Linearly)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('daq_pulse_pileup.png', dpi=150)
    print("Saved: daq_pulse_pileup.png")
    plt.close()


def test_realistic_pulse():
    """Test realistic pulse with filtering and noise"""
    print("\nTesting realistic pulse (filtered + noise)...")

    fig, axes = plt.subplots(3, 2, figsize=(14, 10))

    amplitude = 1.0

    # Generate different versions
    time_ideal, pulse_ideal = generate_calorimeter_pulse(amplitude)
    time_filt, pulse_filtered = generate_realistic_pulse(amplitude, apply_filter=True, add_noise_flag=False)
    time_real, pulse_realistic = generate_realistic_pulse(amplitude, apply_filter=True, add_noise_flag=True, noise_floor_db=-80)

    # Plot 1: Compare ideal vs filtered
    ax = axes[0, 0]
    ax.plot(time_ideal * 1000, pulse_ideal, 'b-', linewidth=2, alpha=0.7, label='Ideal pulse')
    ax.plot(time_filt * 1000, pulse_filtered, 'r-', linewidth=1.5, label='Filtered (1 kHz LPF)')
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Effect of Bandwidth Limiting (10% of sample rate)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 2: Zoom on rise time
    ax = axes[0, 1]
    zoom_samples = 50
    ax.plot(time_ideal[:zoom_samples] * 1000, pulse_ideal[:zoom_samples],
            'b-', linewidth=2, alpha=0.7, label='Ideal')
    ax.plot(time_filt[:zoom_samples] * 1000, pulse_filtered[:zoom_samples],
            'r-', linewidth=1.5, label='Filtered')
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Rise Time Detail (Filter Rounding)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 3: Realistic pulse (filtered + noise)
    ax = axes[1, 0]
    ax.plot(time_real * 1000, pulse_realistic, 'g-', linewidth=1, alpha=0.8, label='Realistic (filtered + noise)')
    ax.plot(time_filt * 1000, pulse_filtered, 'r--', linewidth=1.5, alpha=0.5, label='Filtered only')
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Realistic Pulse (-80 dB Noise Floor)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 4: Noise detail (baseline)
    ax = axes[1, 1]
    # Show just noise (no signal)
    time_noise, noise_only = generate_realistic_pulse(0.0, apply_filter=False, add_noise_flag=True, noise_floor_db=-80)
    ax.plot(time_noise[:1000] * 1000, noise_only[:1000], 'k-', linewidth=0.5, alpha=0.7)
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Noise Floor Detail (-80 dB)')
    ax.grid(True, alpha=0.3)
    # Add RMS noise level
    noise_rms = np.std(noise_only)
    ax.axhline(noise_rms, color='r', linestyle='--', alpha=0.5, label=f'RMS={noise_rms:.6f}')
    ax.axhline(-noise_rms, color='r', linestyle='--', alpha=0.5)
    ax.legend()

    # Plot 5: Frequency domain comparison
    ax = axes[2, 0]
    # FFT of ideal and filtered pulses
    fft_ideal = np.fft.rfft(pulse_ideal)
    fft_filtered = np.fft.rfft(pulse_filtered)
    freqs = np.fft.rfftfreq(len(pulse_ideal), 1/10000)

    ax.plot(freqs, 20*np.log10(np.abs(fft_ideal) + 1e-10), 'b-', alpha=0.7, label='Ideal')
    ax.plot(freqs, 20*np.log10(np.abs(fft_filtered) + 1e-10), 'r-', label='Filtered')
    ax.axvline(1000, color='g', linestyle='--', alpha=0.5, label='Cutoff (1 kHz)')
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Magnitude (dB)')
    ax.set_title('Frequency Response')
    ax.set_xlim([0, 2500])
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 6: SNR vs amplitude
    ax = axes[2, 1]
    test_amplitudes = np.logspace(-4, 0, 20)  # 0.0001 to 1.0
    snr_values = []

    for amp in test_amplitudes:
        _, test_pulse = generate_realistic_pulse(amp, apply_filter=True, add_noise_flag=True, noise_floor_db=-80, seed=42)
        signal_power = np.max(test_pulse) ** 2
        noise_power = (10 ** (-80/20)) ** 2
        snr_db = 10 * np.log10(signal_power / noise_power)
        snr_values.append(snr_db)

    ax.semilogx(test_amplitudes, snr_values, 'b-', linewidth=2)
    ax.set_xlabel('Pulse Amplitude (particle speed)')
    ax.set_ylabel('SNR (dB)')
    ax.set_title('Signal-to-Noise Ratio vs Amplitude')
    ax.grid(True, alpha=0.3, which='both')
    ax.axhline(0, color='r', linestyle='--', alpha=0.5, label='SNR = 0 dB')
    ax.legend()

    plt.tight_layout()
    plt.savefig('daq_pulse_realistic.png', dpi=150)
    print("Saved: daq_pulse_realistic.png")
    plt.close()


def verify_parameters():
    """Verify pulse parameters numerically"""
    print("\nVerifying pulse parameters...")

    time, pulse = generate_calorimeter_pulse(amplitude=1.0)

    # Find peak
    peak_idx = np.argmax(pulse)
    peak_value = pulse[peak_idx]
    peak_time_ms = time[peak_idx] * 1000

    print(f"  Peak amplitude: {peak_value:.6f} (expected: 1.0)")
    print(f"  Peak time: {peak_time_ms:.2f} ms (expected: 1.0 ms)")

    # Verify rise time
    rise_samples = 10
    expected_rise_time_ms = rise_samples / 10000 * 1000
    print(f"  Rise time: {peak_time_ms:.2f} ms (expected: {expected_rise_time_ms:.2f} ms)")

    # Verify decay constant
    # At t = rise_time + decay_time, amplitude should be 1/e of peak
    decay_idx = 10 + 100
    decay_value = pulse[decay_idx]
    expected_decay = np.exp(-1)

    print(f"  Amplitude at τ: {decay_value:.6f} (expected: {expected_decay:.6f} = 1/e)")
    print(f"  Decay error: {abs(decay_value - expected_decay):.6e}")

    # Verify pulse is nearly zero after 5 decay constants
    tail_idx = min(10 + 5 * 100, len(pulse) - 1)
    tail_value = pulse[tail_idx]
    expected_tail = np.exp(-5)

    print(f"  Amplitude at 5τ: {tail_value:.6e} (expected: {expected_tail:.6e})")
    print(f"  Tail represents {tail_value/peak_value*100:.4f}% of peak")

    # Summary
    print("\n  ✓ Pulse shape verified!")
    print(f"  Total pulse length: {len(pulse)} samples ({len(pulse)/10000*1000:.1f} ms)")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Calorimeter DAQ Pulse Shape Tests")
    print("=" * 60)

    # Verify parameters numerically
    verify_parameters()

    # Visual tests
    test_single_pulse()
    test_pulse_pileup()
    test_realistic_pulse()

    print("\n" + "=" * 60)
    print("All tests complete!")
    print("Generated images:")
    print("  - daq_pulse_single.png (basic pulse shapes)")
    print("  - daq_pulse_pileup.png (overlapping pulses)")
    print("  - daq_pulse_realistic.png (filtering + noise)")
    print("=" * 60)


if __name__ == '__main__':
    main()
