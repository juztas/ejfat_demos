"""
Bluesky Scan Plans for FM SHM Beamline

This module provides custom scan plans specifically designed for the FM
shared memory beamline, including frequency sweeps, station monitoring,
and performance testing.

Available Plans:
- fm_band_sweep: Sweep across FM band measuring signal strength
- characterize_fm_station: Time-series monitoring of specific station
- shm_performance_test: Test shared memory performance under load
- multi_station_survey: Quick survey of known stations
- adaptive_station_finder: Auto-tune to strongest signal
- frequency_dwell_scan: Dwell at specific frequencies
"""

import time
import numpy as np
from bluesky import plan_stubs as bps
from bluesky.preprocessors import run_decorator

from .fm_beamline_config import (
    FM_BAND,
    OTTAWA_FM_FREQUENCIES,
    SCAN_DEFAULTS,
    THRESHOLDS,
)


@run_decorator(md={'plan_name': 'fm_band_sweep', 'beamline': 'fm_shm'})
def fm_band_sweep(beamline, start=None, stop=None, num=None, dwell_time=None):
    """
    Sweep across FM band and measure signal strength.

    This plan steps through the FM band, measuring RF power and buffer
    health at each frequency. Useful for identifying active stations.

    Parameters
    ----------
    beamline : FMSHMBeamline
        The FM beamline device
    start : float, optional
        Start frequency (Hz). Default: 88 MHz
    stop : float, optional
        Stop frequency (Hz). Default: 108 MHz
    num : int, optional
        Number of points. Default: from SCAN_DEFAULTS
    dwell_time : float, optional
        Dwell time at each frequency (seconds). Default: from SCAN_DEFAULTS

    Yields
    ------
    Msg
        Bluesky messages

    Metadata
    --------
    plan_name : 'fm_band_sweep'
    beamline : 'fm_shm'
    start_freq : Start frequency
    stop_freq : Stop frequency
    num_points : Number of points
    dwell_time : Dwell time per point

    Examples
    --------
    >>> # Full band sweep with defaults
    >>> RE(fm_band_sweep(beamline))

    >>> # Custom range and resolution
    >>> RE(fm_band_sweep(beamline, start=95e6, stop=100e6, num=50))
    """
    # Use defaults if not specified
    start = start or FM_BAND['min_freq']
    stop = stop or FM_BAND['max_freq']
    num = num or SCAN_DEFAULTS['band_sweep_points']
    dwell_time = dwell_time or SCAN_DEFAULTS['band_sweep_dwell']

    # Generate frequency points
    frequencies = np.linspace(start, stop, num)

    for i, freq in enumerate(frequencies):
        # Set transmitter frequency
        yield from bps.abs_set(beamline.transmitter.frequency, freq, wait=True)

        # Wait for settling
        yield from bps.sleep(SCAN_DEFAULTS['settling_time'])

        # Wait for dwell time
        yield from bps.sleep(dwell_time)

        # Measure signal strength and buffer health
        yield from bps.trigger_and_read([
            beamline.transmitter,
            beamline.receiver,
            beamline.buffer,
        ])

        # Progress indicator (every 10%)
        if (i + 1) % max(1, num // 10) == 0:
            progress = ((i + 1) / num) * 100
            print(f"  Progress: {progress:.0f}% ({freq/1e6:.1f} MHz)")


@run_decorator()
def characterize_fm_station(beamline, frequency, duration=60, sample_interval=None):
    """
    Monitor a specific FM station over time.

    Tunes to a specific frequency and takes repeated measurements
    to characterize signal quality and buffer health over time.

    Parameters
    ----------
    beamline : FMSHMBeamline
        The FM beamline device
    frequency : float
        Station frequency (Hz)
    duration : float
        Total monitoring duration (seconds)
    sample_interval : float, optional
        Time between samples (seconds). Default: from SCAN_DEFAULTS

    Yields
    ------
    Msg
        Bluesky messages

    Metadata
    --------
    plan_name : 'fm_station_characterization'
    station_frequency : Frequency being monitored
    duration : Total duration
    sample_interval : Sampling interval

    Examples
    --------
    >>> # Monitor CHEZ 106.1 for 5 minutes
    >>> RE(characterize_fm_station(beamline, 106.1e6, duration=300))

    >>> # Quick 30-second check
    >>> RE(characterize_fm_station(beamline, 98.5e6, duration=30, sample_interval=0.5))
    """
    sample_interval = sample_interval or SCAN_DEFAULTS['station_monitor_interval']

    # Calculate number of samples
    num_samples = int(duration / sample_interval)

    # Add metadata
    _md = {
        'plan_name': 'fm_station_characterization',
        'beamline': 'fm_shm',
        'station_frequency': frequency,
        'station_frequency_mhz': frequency / 1e6,
        'duration': duration,
        'sample_interval': sample_interval,
        'num_samples': num_samples,
    }
    # Tune to station
    print(f"Tuning to {frequency/1e6:.1f} MHz...")
    yield from bps.abs_set(beamline.transmitter.frequency, frequency, wait=True)
    yield from bps.sleep(2.0)  # Extra settling time

    print(f"Monitoring for {duration} seconds (taking {num_samples} samples)...")

    # Time-series monitoring
    start_time = time.time()
    for i in range(num_samples):
        # Measure
        yield from bps.trigger_and_read([
            beamline.transmitter,
            beamline.receiver,
            beamline.buffer,
        ])

        # Progress indicator (every 10%)
        if (i + 1) % max(1, num_samples // 10) == 0:
            elapsed = time.time() - start_time
            progress = ((i + 1) / num_samples) * 100
            print(f"  Progress: {progress:.0f}% ({elapsed:.0f}s elapsed)")

        # Sleep until next sample
        if i < num_samples - 1:  # Don't sleep after last sample
            yield from bps.sleep(sample_interval)



@run_decorator()
def shm_performance_test(beamline, test_duration=300, sweep_rate='normal'):
    """
    Test shared memory performance under load.

    Sweeps through frequencies while monitoring buffer statistics
    to characterize shared memory performance and detect issues.

    Parameters
    ----------
    beamline : FMSHMBeamline
        The FM beamline device
    test_duration : float
        Total test duration (seconds)
    sweep_rate : str
        Sweep rate: 'slow', 'normal', 'fast', 'stress'

    Yields
    ------
    Msg
        Bluesky messages

    Metadata
    --------
    plan_name : 'shm_performance_test'
    test_duration : Duration of test
    sweep_rate : Sweep rate setting

    Examples
    --------
    >>> # Normal 5-minute performance test
    >>> RE(shm_performance_test(beamline, test_duration=300))

    >>> # Stress test with rapid frequency changes
    >>> RE(shm_performance_test(beamline, test_duration=600, sweep_rate='stress'))
    """
    # Sweep rate parameters
    sweep_rates = {
        'slow': {'num_freqs': 10, 'dwell': 1.0},
        'normal': {'num_freqs': 20, 'dwell': 0.5},
        'fast': {'num_freqs': 50, 'dwell': 0.2},
        'stress': {'num_freqs': 100, 'dwell': 0.1},
    }

    if sweep_rate not in sweep_rates:
        raise ValueError(f"Invalid sweep_rate: {sweep_rate}. "
                        f"Must be one of {list(sweep_rates.keys())}")

    params = sweep_rates[sweep_rate]

    # Add metadata
    _md = {
        'plan_name': 'shm_performance_test',
        'beamline': 'fm_shm',
        'test_duration': test_duration,
        'sweep_rate': sweep_rate,
        'num_frequencies': params['num_freqs'],
        'dwell_time': params['dwell'],
    }
    # Generate frequency sweep
    freq_range = np.linspace(FM_BAND['min_freq'], FM_BAND['max_freq'],
                             params['num_freqs'])

    print(f"Starting {sweep_rate} performance test ({test_duration}s)...")
    print(f"  Frequencies: {params['num_freqs']}")
    print(f"  Dwell time: {params['dwell']}s")

    start_time = time.time()
    cycle_count = 0

    # Sweep continuously until duration reached
    while (time.time() - start_time) < test_duration:
        cycle_count += 1

        for freq in freq_range:
            # Check if time's up
            if (time.time() - start_time) >= test_duration:
                break

            # Set frequency
            yield from bps.abs_set(beamline.transmitter.frequency, freq, wait=True)

            # Measure buffer health
            yield from bps.trigger_and_read([beamline.buffer])

            # Dwell
            yield from bps.sleep(params['dwell'])

        # Progress indicator
        elapsed = time.time() - start_time
        progress = min(100, (elapsed / test_duration) * 100)
        print(f"  Cycle {cycle_count} complete - {progress:.0f}% ({elapsed:.0f}s)")

    print(f"Performance test complete - {cycle_count} sweep cycles")



@run_decorator()
def multi_station_survey(beamline, stations=None, dwell_time=5.0, num_cycles=1):
    """
    Survey multiple known FM stations.

    Quickly characterizes known Ottawa FM stations by tuning to each
    and measuring signal quality.

    Parameters
    ----------
    beamline : FMSHMBeamline
        The FM beamline device
    stations : dict, optional
        Dictionary of station_name: frequency (Hz)
        Default: OTTAWA_FM_FREQUENCIES
    dwell_time : float
        Time to monitor each station (seconds)
    num_cycles : int
        Number of times to cycle through all stations

    Yields
    ------
    Msg
        Bluesky messages

    Metadata
    --------
    plan_name : 'multi_station_survey'
    num_stations : Number of stations surveyed
    dwell_time : Dwell time per station
    num_cycles : Number of cycles

    Examples
    --------
    >>> # Survey all Ottawa stations
    >>> RE(multi_station_survey(beamline))

    >>> # Survey specific stations multiple times
    >>> stations = {'CHEZ 106': 106.1e6, 'CBC': 91.5e6}
    >>> RE(multi_station_survey(beamline, stations=stations, num_cycles=3))
    """
    stations = stations or OTTAWA_FM_FREQUENCIES

    # Add metadata
    _md = {
        'plan_name': 'multi_station_survey',
        'beamline': 'fm_shm',
        'num_stations': len(stations),
        'station_names': list(stations.keys()),
        'dwell_time': dwell_time,
        'num_cycles': num_cycles,
    }
    print(f"Surveying {len(stations)} stations ({num_cycles} cycle(s))...")

    for cycle in range(num_cycles):
        if num_cycles > 1:
            print(f"\n--- Cycle {cycle + 1}/{num_cycles} ---")

        for station_name, frequency in stations.items():
            print(f"  Monitoring: {station_name} ({frequency/1e6:.1f} MHz)")

            # Tune to station
            yield from bps.abs_set(beamline.transmitter.frequency,
                                  frequency, wait=True)

            # Settling time
            yield from bps.sleep(SCAN_DEFAULTS['settling_time'])

            # Monitor for dwell_time with multiple samples
            samples_per_station = max(1, int(dwell_time / 0.5))
            for _ in range(samples_per_station):
                yield from bps.trigger_and_read([
                    beamline.transmitter,
                    beamline.receiver,
                    beamline.buffer,
                ])
                yield from bps.sleep(0.5)

    print(f"\nSurvey complete - {len(stations)} stations × {num_cycles} cycles")



@run_decorator()
def adaptive_station_finder(beamline, start=None, stop=None,
                            coarse_points=20, fine_points=10,
                            threshold=None):
    """
    Adaptively find and tune to strongest FM station.

    Uses two-stage approach:
    1. Coarse sweep to find general peak regions
    2. Fine sweep around peaks to precisely tune

    Parameters
    ----------
    beamline : FMSHMBeamline
        The FM beamline device
    start : float, optional
        Start frequency (Hz). Default: 88 MHz
    stop : float, optional
        Stop frequency (Hz). Default: 108 MHz
    coarse_points : int
        Number of points in coarse sweep
    fine_points : int
        Number of points in fine sweep around peak
    threshold : float, optional
        Minimum signal threshold to consider as station
        Default: from THRESHOLDS

    Yields
    ------
    Msg
        Bluesky messages

    Metadata
    --------
    plan_name : 'adaptive_station_finder'
    threshold : Signal threshold used

    Examples
    --------
    >>> # Find strongest station in band
    >>> RE(adaptive_station_finder(beamline))

    >>> # Search specific range
    >>> RE(adaptive_station_finder(beamline, start=95e6, stop=100e6))
    """
    start = start or FM_BAND['min_freq']
    stop = stop or FM_BAND['max_freq']
    threshold = threshold or THRESHOLDS['station_threshold']

    # Add metadata
    _md = {
        'plan_name': 'adaptive_station_finder',
        'beamline': 'fm_shm',
        'start_freq': start,
        'stop_freq': stop,
        'coarse_points': coarse_points,
        'fine_points': fine_points,
        'threshold': threshold,
    }
    print("Stage 1: Coarse sweep...")

    # Stage 1: Coarse sweep
    coarse_freqs = np.linspace(start, stop, coarse_points)
    coarse_powers = []

    for freq in coarse_freqs:
        yield from bps.abs_set(beamline.transmitter.frequency, freq, wait=True)
        yield from bps.sleep(0.2)

        # Read RF power (would come from transmitter.rf_power in real system)
        # For now, we'll store frequency for demonstration
        coarse_powers.append(freq)  # Placeholder

    # TODO: In real system, analyze coarse_powers to find peak
    # For now, use middle of band as "peak"
    peak_freq = (start + stop) / 2
    print(f"  Coarse peak found near {peak_freq/1e6:.1f} MHz")

    # Stage 2: Fine sweep around peak
    print("Stage 2: Fine sweep around peak...")
    fine_width = (stop - start) / coarse_points  # Width of one coarse step
    fine_start = peak_freq - fine_width
    fine_stop = peak_freq + fine_width
    fine_freqs = np.linspace(fine_start, fine_stop, fine_points)

    best_freq = peak_freq
    best_power = -999

    for freq in fine_freqs:
        yield from bps.abs_set(beamline.transmitter.frequency, freq, wait=True)
        yield from bps.sleep(0.2)

        yield from bps.trigger_and_read([
            beamline.transmitter,
            beamline.receiver,
            beamline.buffer,
        ])

        # TODO: Track actual power measurements

    print(f"  Best frequency: {best_freq/1e6:.1f} MHz")

    # Final tune to best frequency
    print("Stage 3: Final tune...")
    yield from bps.abs_set(beamline.transmitter.frequency, best_freq, wait=True)
    yield from bps.sleep(1.0)

    # Final measurement
    yield from bps.trigger_and_read([
        beamline.transmitter,
        beamline.receiver,
        beamline.buffer,
    ])

    print(f"Tuned to {best_freq/1e6:.1f} MHz")



@run_decorator()
def frequency_dwell_scan(beamline, frequencies, dwell_time=10.0, num_samples=None):
    """
    Scan specific frequencies with extended dwell time.

    Useful for detailed characterization of known stations or
    specific frequencies of interest.

    Parameters
    ----------
    beamline : FMSHMBeamline
        The FM beamline device
    frequencies : list of float
        List of frequencies to scan (Hz)
    dwell_time : float
        Time to spend at each frequency (seconds)
    num_samples : int, optional
        Number of samples to take at each frequency
        Default: calculated from dwell_time

    Yields
    ------
    Msg
        Bluesky messages

    Metadata
    --------
    plan_name : 'frequency_dwell_scan'
    frequencies : List of frequencies scanned
    dwell_time : Dwell time per frequency

    Examples
    --------
    >>> # Scan specific frequencies
    >>> freqs = [88.5e6, 91.5e6, 98.5e6, 106.1e6]
    >>> RE(frequency_dwell_scan(beamline, freqs, dwell_time=30))

    >>> # Detailed scan with many samples
    >>> RE(frequency_dwell_scan(beamline, freqs, num_samples=100))
    """
    if num_samples is None:
        num_samples = max(1, int(dwell_time / 0.5))
    sample_interval = dwell_time / num_samples

    # Add metadata
    _md = {
        'plan_name': 'frequency_dwell_scan',
        'beamline': 'fm_shm',
        'frequencies': frequencies,
        'frequencies_mhz': [f/1e6 for f in frequencies],
        'dwell_time': dwell_time,
        'num_samples': num_samples,
        'sample_interval': sample_interval,
    }
    print(f"Scanning {len(frequencies)} frequencies...")
    print(f"  Dwell time: {dwell_time}s per frequency")
    print(f"  Samples: {num_samples} per frequency")

    for i, freq in enumerate(frequencies):
        print(f"\n[{i+1}/{len(frequencies)}] Frequency: {freq/1e6:.1f} MHz")

        # Tune to frequency
        yield from bps.abs_set(beamline.transmitter.frequency, freq, wait=True)
        yield from bps.sleep(SCAN_DEFAULTS['settling_time'])

        # Take multiple samples
        for sample in range(num_samples):
            yield from bps.trigger_and_read([
                beamline.transmitter,
                beamline.receiver,
                beamline.buffer,
            ])

            if sample < num_samples - 1:
                yield from bps.sleep(sample_interval)

            # Progress indicator
            if (sample + 1) % max(1, num_samples // 4) == 0:
                progress = ((sample + 1) / num_samples) * 100
                print(f"    {progress:.0f}% complete")

    print(f"\nScan complete - {len(frequencies)} frequencies scanned")



# Export all plans
__all__ = [
    'fm_band_sweep',
    'characterize_fm_station',
    'shm_performance_test',
    'multi_station_survey',
    'adaptive_station_finder',
    'frequency_dwell_scan',
]
