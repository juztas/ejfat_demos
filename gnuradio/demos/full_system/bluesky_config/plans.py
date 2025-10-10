"""
Custom Bluesky scan plans for EJFAT GNU Radio experiments.

This module provides reusable scan plans that can be used across
different experiments.
"""

from bluesky import plans as bp
from bluesky import plan_stubs as bps
from bluesky.preprocessors import run_decorator
import numpy as np


def frequency_sweep(signal_gen, start, stop, num_points, dwell_time=1.0):
    """
    Sweep through a range of frequencies without triggering detectors.

    Useful for visual observation of GNU Radio GUI changes.

    Parameters
    ----------
    signal_gen : Device
        Signal generator device with frequency attribute
    start : float
        Starting frequency in Hz
    stop : float
        Ending frequency in Hz
    num_points : int
        Number of frequency points
    dwell_time : float, optional
        Time to dwell at each frequency in seconds (default: 1.0, minimum: 1.0)
        WARNING: GNU Radio can segfault if frequency is changed faster than 1s

    Yields
    ------
    Msg
        Bluesky messages
    """
    # Enforce minimum dwell time to prevent GNU Radio segfaults
    if dwell_time < 1.0:
        print(f"WARNING: dwell_time {dwell_time}s is too short. Using 1.0s minimum.")
        dwell_time = 1.0

    @run_decorator(md={
        'plan_name': 'frequency_sweep',
        'start_freq': start,
        'stop_freq': stop,
        'num_points': num_points,
        'dwell_time': dwell_time,
    })
    def inner():
        frequencies = np.linspace(start, stop, num_points)

        for i, freq in enumerate(frequencies, 1):
            yield from bps.abs_set(signal_gen.frequency, freq, wait=True)
            print(f"[{i:3d}/{num_points}] Frequency: {freq/1e6:.2f} MHz")
            yield from bps.sleep(dwell_time)

    yield from inner()


def frequency_scan(detectors, signal_gen, start, stop, num_points):
    """
    Scan frequency while collecting data from detectors.

    This implements a frequency scan with proper 1s settling time between
    frequency changes to prevent GNU Radio segfaults.

    Parameters
    ----------
    detectors : list
        List of detector objects to read at each point
    signal_gen : Device
        Signal generator device
    start : float
        Starting frequency in Hz
    stop : float
        Ending frequency in Hz
    num_points : int
        Number of frequency points

    Yields
    ------
    Msg
        Bluesky messages
    """
    @run_decorator(md={
        'plan_name': 'frequency_scan',
        'start_freq': start,
        'stop_freq': stop,
        'num_points': num_points,
    })
    def inner():
        frequencies = np.linspace(start, stop, num_points)

        for i, freq in enumerate(frequencies, 1):
            # Set frequency
            yield from bps.abs_set(signal_gen.frequency, freq, wait=True)
            # Wait 1s after frequency change to prevent segfault
            yield from bps.sleep(1.0)

            # Read detectors
            yield from bps.trigger_and_read(detectors)

            print(f"[{i:3d}/{num_points}] Frequency: {freq/1e6:.2f} MHz")

    yield from inner()


def frequency_characterization(detectors, signal_gen, frequencies, num_samples=5):
    """
    Characterize signal response at specific frequencies.

    Takes multiple samples at each frequency for statistical analysis.

    Parameters
    ----------
    detectors : list
        List of detector objects to read
    signal_gen : Device
        Signal generator device
    frequencies : list of float
        List of frequencies to characterize in Hz
    num_samples : int, optional
        Number of samples to take at each frequency (default: 5)

    Yields
    ------
    Msg
        Bluesky messages
    """
    @run_decorator(md={
        'plan_name': 'frequency_characterization',
        'frequencies': frequencies,
        'num_samples': num_samples,
    })
    def inner():
        for freq in frequencies:
            yield from bps.abs_set(signal_gen.frequency, freq, wait=True)
            print(f"\nCharacterizing frequency: {freq/1e6:.2f} MHz")

            # Allow settling time (minimum 1s to prevent GNU Radio segfaults)
            yield from bps.sleep(1.0)

            # Take multiple samples
            for sample_num in range(num_samples):
                yield from bps.trigger_and_read(detectors)
                print(f"  Sample {sample_num + 1}/{num_samples}")
                yield from bps.sleep(0.1)

    yield from inner()


def adaptive_frequency_scan(detectors, signal_gen, start, stop,
                             target_delta=0.05, min_step=1e3, max_step=1e6):
    """
    Adaptive frequency scan with variable step size.

    Step size is adjusted based on the derivative of the signal.
    Takes smaller steps where signal is changing rapidly.

    Parameters
    ----------
    detectors : list
        List of detector objects (should have one primary detector)
    signal_gen : Device
        Signal generator device
    start : float
        Starting frequency in Hz
    stop : float
        Ending frequency in Hz
    target_delta : float, optional
        Target change in detector reading between steps (default: 0.05)
    min_step : float, optional
        Minimum frequency step in Hz (default: 1 kHz)
    max_step : float, optional
        Maximum frequency step in Hz (default: 1 MHz)

    Yields
    ------
    Msg
        Bluesky messages
    """
    @run_decorator(md={
        'plan_name': 'adaptive_frequency_scan',
        'start_freq': start,
        'stop_freq': stop,
        'target_delta': target_delta,
        'min_step': min_step,
        'max_step': max_step,
    })
    def inner():
        # Assume first detector is primary
        detector = detectors[0]
        detector_key = f'{detector.name}_value'

        current_freq = start
        prev_value = None
        step = max_step

        while current_freq <= stop:
            # Set frequency
            yield from bps.abs_set(signal_gen.frequency, current_freq, wait=True)

            # Wait for settling (minimum 1s to prevent GNU Radio segfaults)
            yield from bps.sleep(1.0)

            # Read detectors
            reading = yield from bps.trigger_and_read(detectors)
            current_value = reading[detector_key]['value']

            print(f"Freq: {current_freq/1e6:.3f} MHz, "
                  f"Value: {current_value:.4f}, Step: {step/1e3:.1f} kHz")

            # Adjust step size based on derivative
            if prev_value is not None:
                delta = abs(current_value - prev_value)
                if delta > target_delta * 1.5:
                    step = max(min_step, step * 0.5)  # Smaller steps
                elif delta < target_delta * 0.5:
                    step = min(max_step, step * 1.5)  # Larger steps

            prev_value = current_value
            current_freq += step

    yield from inner()


def grid_scan_2d(detectors, motor1, start1, stop1, num1,
                 motor2, start2, stop2, num2):
    """
    2D grid scan over two motors/parameters.

    Useful for mapping response over two dimensions (e.g., TX freq vs RX freq).

    Parameters
    ----------
    detectors : list
        List of detector objects
    motor1 : Device
        First motor/parameter to scan
    start1, stop1 : float
        Range for first motor
    num1 : int
        Number of points for first motor
    motor2 : Device
        Second motor/parameter to scan
    start2, stop2 : float
        Range for second motor
    num2 : int
        Number of points for second motor

    Yields
    ------
    Msg
        Bluesky messages
    """
    yield from bp.grid_scan(detectors,
                             motor1, start1, stop1, num1,
                             motor2, start2, stop2, num2,
                             snake_axes=True)


def time_series_acquisition(detectors, num_points, delay=1.0):
    """
    Time series data acquisition at a fixed configuration.

    Parameters
    ----------
    detectors : list
        List of detector objects
    num_points : int
        Number of data points to acquire
    delay : float, optional
        Delay between measurements in seconds (default: 1.0)

    Yields
    ------
    Msg
        Bluesky messages
    """
    @run_decorator(md={
        'plan_name': 'time_series_acquisition',
        'num_points': num_points,
        'delay': delay,
    })
    def inner():
        for i in range(num_points):
            yield from bps.trigger_and_read(detectors)
            print(f"Point {i+1}/{num_points}")
            if i < num_points - 1:  # Don't sleep after last point
                yield from bps.sleep(delay)

    yield from inner()


def synchronized_tx_rx_scan(tx_gen, rx_gen, detectors, start, stop, num_points):
    """
    Synchronized TX and RX frequency scan.

    Both transmitter and receiver are set to the same frequency at each step.

    Parameters
    ----------
    tx_gen : Device
        Transmitter signal generator
    rx_gen : Device
        Receiver signal generator
    detectors : list
        List of detector objects
    start : float
        Starting frequency in Hz
    stop : float
        Ending frequency in Hz
    num_points : int
        Number of frequency points

    Yields
    ------
    Msg
        Bluesky messages
    """
    @run_decorator(md={
        'plan_name': 'synchronized_tx_rx_scan',
        'start_freq': start,
        'stop_freq': stop,
        'num_points': num_points,
    })
    def inner():
        frequencies = np.linspace(start, stop, num_points)

        for i, freq in enumerate(frequencies, 1):
            # Set both TX and RX
            yield from bps.abs_set(tx_gen.frequency, freq, wait=True)
            # Wait 1s after first frequency change to prevent segfault
            yield from bps.sleep(1.0)

            yield from bps.abs_set(rx_gen.frequency, freq, wait=True)
            # Wait 1s after second frequency change to prevent segfault
            yield from bps.sleep(1.0)

            # Measure
            yield from bps.trigger_and_read(detectors)

            print(f"[{i:3d}/{num_points}] TX/RX Freq: {freq/1e6:.2f} MHz")

    yield from inner()


def peak_finding_scan(detectors, signal_gen, start, stop, num_initial_points=20):
    """
    Two-stage scan: coarse scan to find peaks, then fine scan around peaks.

    Parameters
    ----------
    detectors : list
        List of detector objects
    signal_gen : Device
        Signal generator device
    start : float
        Starting frequency in Hz
    stop : float
        Ending frequency in Hz
    num_initial_points : int, optional
        Number of points for initial coarse scan (default: 20)

    Yields
    ------
    Msg
        Bluesky messages
    """
    @run_decorator(md={
        'plan_name': 'peak_finding_scan',
        'start_freq': start,
        'stop_freq': stop,
        'num_initial_points': num_initial_points,
    })
    def inner():
        from scipy.signal import find_peaks

        # Stage 1: Coarse scan
        print("Stage 1: Coarse scan to locate peaks...")
        coarse_freqs = np.linspace(start, stop, num_initial_points)
        coarse_values = []

        for freq in coarse_freqs:
            yield from bps.abs_set(signal_gen.frequency, freq, wait=True)
            # Wait 1s after frequency change to prevent segfault
            yield from bps.sleep(1.0)

            reading = yield from bps.trigger_and_read(detectors)

            detector = detectors[0]
            detector_key = f'{detector.name}_value'
            value = reading[detector_key]['value']
            coarse_values.append(value)

        # Find peaks
        coarse_values = np.array(coarse_values)
        peaks, _ = find_peaks(coarse_values, prominence=0.1)

        print(f"Found {len(peaks)} peaks in coarse scan")

        # Stage 2: Fine scan around each peak
        for peak_idx in peaks:
            peak_freq = coarse_freqs[peak_idx]
            freq_range = (stop - start) / num_initial_points

            fine_start = max(start, peak_freq - freq_range)
            fine_stop = min(stop, peak_freq + freq_range)

            print(f"\nStage 2: Fine scan around {peak_freq/1e6:.2f} MHz...")
            # Use frequency_scan which has proper delays
            yield from frequency_scan(detectors, signal_gen,
                                     fine_start, fine_stop, 20)

    yield from inner()
