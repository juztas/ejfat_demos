"""
Bluesky plans for controlling GNU Radio signal generators.

This module provides example Bluesky plans that demonstrate how to
control a GNU Radio signal generator from Bluesky experiments.
"""

from bluesky import plans as bp
from bluesky import plan_stubs as bps
from bluesky.preprocessors import run_decorator
import time


def set_sine_frequency(signal_gen, frequency):
    """
    Simple plan to set the sine wave frequency.

    Parameters
    ----------
    signal_gen : GNURadioSignalGenerator
        The signal generator device
    frequency : float
        Target frequency in Hz

    Yields
    ------
    Msg
        Bluesky messages

    Examples
    --------
    >>> from bluesky import RunEngine
    >>> from bluesky.gnuradio_device import GNURadioSignalGenerator
    >>>
    >>> RE = RunEngine({})
    >>> sig_gen = GNURadioSignalGenerator('', name='sig_gen')
    >>>
    >>> # Set frequency to 2.5 kHz
    >>> RE(set_sine_frequency(sig_gen, 2500))
    """
    yield from bps.abs_set(signal_gen.frequency, frequency, wait=True)
    print(f"Set frequency to {frequency} Hz")


def frequency_sweep(signal_gen, start, stop, num_points, dwell_time=0.5):
    """
    Sweep through a range of frequencies.

    This plan steps through frequencies from start to stop, dwelling at
    each frequency for the specified time. No detectors are triggered,
    making this useful for visual observation of the GNU Radio GUI.

    Parameters
    ----------
    signal_gen : GNURadioSignalGenerator
        The signal generator device
    start : float
        Starting frequency in Hz
    stop : float
        Ending frequency in Hz
    num_points : int
        Number of frequency points
    dwell_time : float, optional
        Time to dwell at each frequency in seconds (default: 0.5)

    Yields
    ------
    Msg
        Bluesky messages

    Examples
    --------
    >>> # Sweep from 100 Hz to 5 kHz in 50 steps
    >>> RE(frequency_sweep(sig_gen, 100, 5000, 50, dwell_time=0.5))
    """
    frequencies = list(range(int(start), int(stop) + 1,
                             int((stop - start) / (num_points - 1))))

    @run_decorator(md={'plan_name': 'frequency_sweep',
                       'start': start,
                       'stop': stop,
                       'num_points': num_points,
                       'dwell_time': dwell_time})
    def inner_plan():
        for freq in frequencies:
            yield from bps.abs_set(signal_gen.frequency, freq, wait=True)
            print(f"Frequency: {freq} Hz")
            yield from bps.sleep(dwell_time)

    yield from inner_plan()


def frequency_scan(detectors, signal_gen, start, stop, num_points):
    """
    Scan frequency while collecting data from detectors.

    This is a wrapper around Bluesky's standard scan plan that makes
    it easy to scan frequency while acquiring data.

    Parameters
    ----------
    detectors : list
        List of detector objects to read at each point
    signal_gen : GNURadioSignalGenerator
        The signal generator device
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

    Examples
    --------
    >>> from ophyd import Signal
    >>> detector = Signal(name='det', value=0)
    >>>
    >>> # Scan frequency and collect detector readings
    >>> RE(frequency_scan([detector], sig_gen, 100, 5000, 50))
    """
    yield from bp.scan(detectors, signal_gen.frequency, start, stop, num_points)


def frequency_list_scan(detectors, signal_gen, frequencies):
    """
    Scan through an arbitrary list of frequencies.

    Parameters
    ----------
    detectors : list
        List of detector objects to read at each point
    signal_gen : GNURadioSignalGenerator
        The signal generator device
    frequencies : list of float
        List of frequencies to visit in Hz

    Yields
    ------
    Msg
        Bluesky messages

    Examples
    --------
    >>> # Visit specific frequencies
    >>> freqs = [100, 250, 500, 1000, 2500, 5000]
    >>> RE(frequency_list_scan([detector], sig_gen, freqs))
    """
    yield from bp.list_scan(detectors, signal_gen.frequency, frequencies)


def frequency_steps(signal_gen, frequencies, dwell_time=1.0):
    """
    Step through discrete frequencies with dwell time at each.

    Unlike frequency_sweep, this plan takes an explicit list of
    frequencies rather than generating them from start/stop/num.

    Parameters
    ----------
    signal_gen : GNURadioSignalGenerator
        The signal generator device
    frequencies : list of float
        List of frequencies to visit in Hz
    dwell_time : float, optional
        Time to dwell at each frequency in seconds (default: 1.0)

    Yields
    ------
    Msg
        Bluesky messages

    Examples
    --------
    >>> # Step through musical notes (A4=440 Hz and harmonics)
    >>> notes = [440, 880, 1320, 1760, 2200]
    >>> RE(frequency_steps(sig_gen, notes, dwell_time=2.0))
    """
    @run_decorator(md={'plan_name': 'frequency_steps',
                       'frequencies': frequencies,
                       'dwell_time': dwell_time})
    def inner_plan():
        for freq in frequencies:
            yield from bps.abs_set(signal_gen.frequency, freq, wait=True)
            print(f"Frequency: {freq} Hz")
            yield from bps.sleep(dwell_time)

    yield from inner_plan()


def frequency_ramp(signal_gen, start, stop, duration, step_size=100):
    """
    Ramp frequency continuously from start to stop over a duration.

    This creates a smooth frequency ramp by taking small steps at
    regular intervals.

    Parameters
    ----------
    signal_gen : GNURadioSignalGenerator
        The signal generator device
    start : float
        Starting frequency in Hz
    stop : float
        Ending frequency in Hz
    duration : float
        Total ramp duration in seconds
    step_size : float, optional
        Frequency step size in Hz (default: 100)

    Yields
    ------
    Msg
        Bluesky messages

    Examples
    --------
    >>> # Ramp from 100 Hz to 5 kHz over 10 seconds
    >>> RE(frequency_ramp(sig_gen, 100, 5000, duration=10, step_size=50))
    """
    num_steps = int(abs(stop - start) / step_size)
    sleep_time = duration / num_steps

    @run_decorator(md={'plan_name': 'frequency_ramp',
                       'start': start,
                       'stop': stop,
                       'duration': duration,
                       'step_size': step_size})
    def inner_plan():
        frequencies = [start + i * step_size * (1 if stop > start else -1)
                       for i in range(num_steps + 1)]

        for freq in frequencies:
            if (stop > start and freq > stop) or (stop < start and freq < stop):
                freq = stop  # Clamp to final value

            yield from bps.abs_set(signal_gen.frequency, freq, wait=True)
            yield from bps.sleep(sleep_time)

        # Ensure we end exactly at stop
        yield from bps.abs_set(signal_gen.frequency, stop, wait=True)

    yield from inner_plan()


def characterize_sine_wave(detectors, signal_gen, frequencies, num_samples=5):
    """
    Characterize the sine wave at multiple frequencies by taking
    repeated measurements.

    This plan is useful for collecting statistics at each frequency point.

    Parameters
    ----------
    detectors : list
        List of detector objects to read
    signal_gen : GNURadioSignalGenerator
        The signal generator device
    frequencies : list of float
        List of frequencies to characterize in Hz
    num_samples : int, optional
        Number of samples to take at each frequency (default: 5)

    Yields
    ------
    Msg
        Bluesky messages

    Examples
    --------
    >>> # Characterize at three frequencies with 10 samples each
    >>> freqs = [1000, 2000, 3000]
    >>> RE(characterize_sine_wave([detector], sig_gen, freqs, num_samples=10))
    """
    @run_decorator(md={'plan_name': 'characterize_sine_wave',
                       'frequencies': frequencies,
                       'num_samples': num_samples})
    def inner_plan():
        for freq in frequencies:
            yield from bps.abs_set(signal_gen.frequency, freq, wait=True)
            print(f"\nCharacterizing frequency: {freq} Hz")

            # Take multiple samples at this frequency
            for sample_num in range(num_samples):
                yield from bps.trigger_and_read(detectors)
                print(f"  Sample {sample_num + 1}/{num_samples}")

    yield from inner_plan()


# Example of a more complex plan combining multiple operations
def frequency_sweep_and_return(signal_gen, start, stop, num_points,
                                dwell_time=0.5, return_to_start=True):
    """
    Sweep frequency and optionally return to starting frequency.

    Parameters
    ----------
    signal_gen : GNURadioSignalGenerator
        The signal generator device
    start : float
        Starting frequency in Hz
    stop : float
        Ending frequency in Hz
    num_points : int
        Number of frequency points
    dwell_time : float, optional
        Time to dwell at each frequency in seconds (default: 0.5)
    return_to_start : bool, optional
        Whether to return to starting frequency after sweep (default: True)

    Yields
    ------
    Msg
        Bluesky messages

    Examples
    --------
    >>> # Sweep and return to starting frequency
    >>> RE(frequency_sweep_and_return(sig_gen, 100, 5000, 50))
    """
    @run_decorator(md={'plan_name': 'frequency_sweep_and_return',
                       'start': start,
                       'stop': stop,
                       'num_points': num_points,
                       'return_to_start': return_to_start})
    def inner_plan():
        # Record initial frequency
        initial_freq = yield from bps.rd(signal_gen.frequency)

        # Perform the sweep
        yield from frequency_sweep(signal_gen, start, stop, num_points, dwell_time)

        # Return to start if requested
        if return_to_start:
            print(f"\nReturning to initial frequency: {initial_freq} Hz")
            yield from bps.abs_set(signal_gen.frequency, initial_freq, wait=True)

    yield from inner_plan()
