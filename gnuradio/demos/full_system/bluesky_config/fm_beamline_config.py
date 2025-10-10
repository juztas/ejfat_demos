"""
FM SHM Beamline Configuration

Configuration specific to the FM shared memory transmit/receive beamline.
This includes FM band parameters, Ottawa station frequencies, shared memory
settings, and signal processing parameters.
"""

from pathlib import Path

# Paths to flowgraph scripts
FM_DIR = Path(__file__).parent.parent.parent / "fm"
FM_TX_FLOWGRAPH = FM_DIR / "fm_transmitter_shm.py"
FM_RX_FLOWGRAPH = FM_DIR / "fm_receiver_shm.py"

# Verify flowgraph files exist
if not FM_TX_FLOWGRAPH.exists():
    print(f"Warning: FM TX flowgraph not found at {FM_TX_FLOWGRAPH}")
if not FM_RX_FLOWGRAPH.exists():
    print(f"Warning: FM RX flowgraph not found at {FM_RX_FLOWGRAPH}")

# FM Band Configuration
FM_BAND = {
    'min_freq': 88.0e6,      # 88 MHz
    'max_freq': 108.0e6,     # 108 MHz
    'step_freq': 100e3,      # 100 kHz steps
    'channel_spacing': 200e3, # 200 kHz (North America standard)
}

# Ottawa FM Stations (for testing and characterization)
# Frequencies verified as of October 2024
OTTAWA_FM_STATIONS = {
    'CBC Radio One': {
        'frequency': 91.5e6,
        'format': 'Public Radio/News',
        'callsign': 'CBOF-FM',
    },
    'CHEZ 106': {
        'frequency': 106.1e6,
        'format': 'Classic Rock',
        'callsign': 'CHEZ-FM',
    },
    'Hot 89.9': {
        'frequency': 89.9e6,
        'format': 'Top 40/CHR',
        'callsign': 'CKKL-FM',
    },
    'The Bear 106.9': {
        'frequency': 106.9e6,
        'format': 'Rock',
        'callsign': 'CKQB-FM',
    },
    'BOB FM 93.9': {
        'frequency': 93.9e6,
        'format': 'Adult Hits',
        'callsign': 'CJOT-FM',
    },
    'DAWG FM 101.9': {
        'frequency': 101.9e6,
        'format': 'Classic Hits',
        'callsign': 'CKBY-FM',
    },
    'TSN 1200': {
        'frequency': 94.5e6,
        'format': 'Sports',
        'callsign': 'CFGO-FM',
    },
    'Majic 100': {
        'frequency': 100.3e6,
        'format': 'Adult Contemporary',
        'callsign': 'CJMJ-FM',
    },
    'Live 88.5': {
        'frequency': 88.5e6,
        'format': 'Alternative Rock',
        'callsign': 'CIMF-FM',
    },
    'Boom 99.7': {
        'frequency': 99.7e6,
        'format': 'Classic Hits',
        'callsign': 'CKBA-FM',
    },
}

# Get just frequencies for quick access
OTTAWA_FM_FREQUENCIES = {
    name: info['frequency']
    for name, info in OTTAWA_FM_STATIONS.items()
}

# Shared Memory Configuration
# These must match the settings in fm_transmitter_shm.grc and fm_receiver_shm.grc
SHM_CONFIG = {
    'name': 'fm_stream',           # Shared memory segment name
    'capacity': 1024,              # Number of entries in ring buffer
    'entry_size': 65552,           # Size of each entry in bytes
    'vlen': 8192,                  # Vector length (samples per entry)
    'data_type': 'complex64',      # Data type (complex float32)
}

# Signal Processing Configuration
SIGNAL_CONFIG = {
    'sample_rate': 2.4e6,          # 2.4 MHz sample rate
    'audio_rate': 48000,           # 48 kHz audio output
    'filter_cutoff': 75e3,         # 75 kHz low-pass filter
    'filter_transition': 25e3,     # 25 kHz transition bandwidth
    'decimation': 5,               # Decimation factor (2.4 MHz → 480 kHz)
}

# XML-RPC Configuration
XMLRPC_CONFIG = {
    'tx_host': 'localhost',
    'tx_port': 8080,
    'rx_host': 'localhost',
    'rx_port': 8081,  # Different port for RX if both run simultaneously
    'timeout': 5.0,   # Connection timeout in seconds
}

# Measurement Thresholds
THRESHOLDS = {
    'rf_power_min': -100,          # Minimum expected RF power (dBm)
    'rf_power_max': 0,             # Maximum expected RF power (dBm)
    'station_threshold': -60,      # Power level to consider as station (dBm)
    'buffer_high_watermark': 90,   # Buffer fill % - warning threshold
    'buffer_low_watermark': 10,    # Buffer fill % - warning threshold
    'overrun_threshold': 10,       # Number of overruns before alert
    'underrun_threshold': 10,      # Number of underruns before alert
}

# Scan Parameters
SCAN_DEFAULTS = {
    'band_sweep_points': 200,      # Number of points in full band sweep
    'band_sweep_dwell': 0.5,       # Dwell time per point (seconds)
    'station_monitor_interval': 1.0, # Sampling interval for station monitoring
    'settling_time': 0.2,          # Time to wait after frequency change
}

# Device Default Settings
DEVICE_DEFAULTS = {
    'tx_frequency': 98.5e6,        # Default frequency (MHz)
    'rx_volume': 1.0,              # Default volume (0-10 scale)
    'tx_rf_gain': 40,              # TX RF gain (dB)
    'tx_if_gain': 20,              # TX IF gain (dB)
    'tx_bb_gain': 20,              # TX baseband gain (dB)
}

# Metadata Templates
METADATA_TEMPLATES = {
    'fm_band_sweep': {
        'beamline': 'fm_shm',
        'experiment_type': 'frequency_sweep',
        'measurement_type': 'rf_power',
    },
    'station_monitor': {
        'beamline': 'fm_shm',
        'experiment_type': 'time_series',
        'measurement_type': 'signal_quality',
    },
    'buffer_test': {
        'beamline': 'fm_shm',
        'experiment_type': 'performance_test',
        'measurement_type': 'buffer_health',
    },
}


def get_station_frequency(station_name):
    """
    Get frequency for a known Ottawa FM station.

    Parameters
    ----------
    station_name : str
        Name of the station (e.g., 'CHEZ 106', 'CBC Radio One')

    Returns
    -------
    float
        Frequency in Hz

    Raises
    ------
    KeyError
        If station name is not found
    """
    if station_name not in OTTAWA_FM_STATIONS:
        available = ', '.join(OTTAWA_FM_STATIONS.keys())
        raise KeyError(
            f"Station '{station_name}' not found. "
            f"Available stations: {available}"
        )

    return OTTAWA_FM_STATIONS[station_name]['frequency']


def get_station_info(frequency, tolerance=100e3):
    """
    Find station information for a given frequency.

    Parameters
    ----------
    frequency : float
        Frequency in Hz
    tolerance : float
        Frequency tolerance for matching (Hz), default 100 kHz

    Returns
    -------
    dict or None
        Station information if found, None otherwise
    """
    for name, info in OTTAWA_FM_STATIONS.items():
        if abs(info['frequency'] - frequency) < tolerance:
            return {
                'name': name,
                **info
            }

    return None


def validate_frequency(frequency):
    """
    Validate that frequency is within FM band.

    Parameters
    ----------
    frequency : float
        Frequency in Hz

    Returns
    -------
    bool
        True if valid, False otherwise
    """
    return FM_BAND['min_freq'] <= frequency <= FM_BAND['max_freq']


def nearest_channel(frequency):
    """
    Round frequency to nearest FM channel.

    Parameters
    ----------
    frequency : float
        Frequency in Hz

    Returns
    -------
    float
        Nearest channel frequency in Hz
    """
    spacing = FM_BAND['channel_spacing']
    min_freq = FM_BAND['min_freq']

    # Round to nearest channel
    channel_num = round((frequency - min_freq) / spacing)
    return min_freq + (channel_num * spacing)


# Export key configuration items
__all__ = [
    'FM_DIR',
    'FM_TX_FLOWGRAPH',
    'FM_RX_FLOWGRAPH',
    'FM_BAND',
    'OTTAWA_FM_STATIONS',
    'OTTAWA_FM_FREQUENCIES',
    'SHM_CONFIG',
    'SIGNAL_CONFIG',
    'XMLRPC_CONFIG',
    'THRESHOLDS',
    'SCAN_DEFAULTS',
    'DEVICE_DEFAULTS',
    'METADATA_TEMPLATES',
    'get_station_frequency',
    'get_station_info',
    'validate_frequency',
    'nearest_channel',
]
