"""
Metadata collection and organization utilities.

This module provides functions to generate standard metadata for experiments.
"""

import datetime
import socket
import getpass
from pathlib import Path


# Facility-level metadata (constant for this beamline)
FACILITY_MD = {
    'facility': 'EJFAT',
    'beamline': 'gnuradio_testbed',
    'location': 'Ottawa',
}


def get_session_metadata(experiment_id, purpose, project='EJFAT-DEMO'):
    """
    Generate standard session metadata.

    Parameters
    ----------
    experiment_id : str
        Unique experiment identifier (e.g., 'EXP-2025-001')
    purpose : str
        Brief description of experiment purpose
    project : str, optional
        Project name (default: 'EJFAT-DEMO')

    Returns
    -------
    dict
        Session metadata dictionary
    """
    return {
        'experiment_id': experiment_id,
        'purpose': purpose,
        'project': project,
        'operator': getpass.getuser(),
        'hostname': socket.gethostname(),
        'session_start': datetime.datetime.now().isoformat(),
    }


def get_plan_metadata(plan_type, **kwargs):
    """
    Generate plan-specific metadata.

    Parameters
    ----------
    plan_type : str
        Type of plan being run
    **kwargs
        Plan-specific parameters

    Returns
    -------
    dict
        Plan metadata dictionary
    """
    return {
        'plan_type': plan_type,
        'plan_args': kwargs,
        'timestamp': datetime.datetime.now().isoformat(),
    }


def add_environmental_metadata(temperature=None, humidity=None,
                                 weather='unknown', notes=''):
    """
    Add environmental conditions metadata.

    Parameters
    ----------
    temperature : float, optional
        Temperature in Celsius
    humidity : float, optional
        Relative humidity in percent
    weather : str, optional
        Weather conditions (default: 'unknown')
    notes : str, optional
        Additional notes

    Returns
    -------
    dict
        Environmental metadata dictionary
    """
    md = {
        'weather': weather,
        'notes': notes,
    }
    if temperature is not None:
        md['temperature'] = temperature
    if humidity is not None:
        md['humidity'] = humidity

    return md


def add_hardware_metadata(sdr_type=None, antenna=None, cable_length=None, **kwargs):
    """
    Add hardware configuration metadata.

    Parameters
    ----------
    sdr_type : str, optional
        Type of SDR (e.g., 'USRP B210', 'RTL-SDR')
    antenna : str, optional
        Antenna description
    cable_length : float, optional
        Cable length in meters
    **kwargs
        Additional hardware parameters

    Returns
    -------
    dict
        Hardware metadata dictionary
    """
    md = {}
    if sdr_type is not None:
        md['sdr_type'] = sdr_type
    if antenna is not None:
        md['antenna'] = antenna
    if cable_length is not None:
        md['cable_length_m'] = cable_length

    md.update(kwargs)
    return md


def add_signal_metadata(frequency_range=None, sample_rate=None,
                        bandwidth=None, **kwargs):
    """
    Add signal processing metadata.

    Parameters
    ----------
    frequency_range : tuple, optional
        (min, max) frequency range in Hz
    sample_rate : float, optional
        Sample rate in Hz
    bandwidth : float, optional
        Signal bandwidth in Hz
    **kwargs
        Additional signal parameters

    Returns
    -------
    dict
        Signal metadata dictionary
    """
    md = {}
    if frequency_range is not None:
        md['frequency_range_hz'] = frequency_range
    if sample_rate is not None:
        md['sample_rate_hz'] = sample_rate
    if bandwidth is not None:
        md['bandwidth_hz'] = bandwidth

    md.update(kwargs)
    return md


def combine_metadata(*metadata_dicts, **extra):
    """
    Combine multiple metadata dictionaries.

    Parameters
    ----------
    *metadata_dicts
        Variable number of metadata dictionaries
    **extra
        Additional key-value pairs to add

    Returns
    -------
    dict
        Combined metadata dictionary
    """
    combined = {}
    for md in metadata_dicts:
        combined.update(md)
    combined.update(extra)
    return combined


def create_experiment_metadata(experiment_id, purpose,
                                 plan_type='custom',
                                 temperature=None, humidity=None,
                                 sdr_type=None,
                                 **kwargs):
    """
    Create comprehensive experiment metadata.

    Convenience function that combines all metadata types.

    Parameters
    ----------
    experiment_id : str
        Unique experiment identifier
    purpose : str
        Experiment purpose description
    plan_type : str, optional
        Type of plan (default: 'custom')
    temperature : float, optional
        Temperature in Celsius
    humidity : float, optional
        Humidity in percent
    sdr_type : str, optional
        SDR type
    **kwargs
        Additional metadata fields

    Returns
    -------
    dict
        Complete metadata dictionary

    Examples
    --------
    >>> md = create_experiment_metadata(
    ...     experiment_id='EXP-2025-001',
    ...     purpose='FM frequency characterization',
    ...     plan_type='frequency_sweep',
    ...     temperature=22.5,
    ...     sdr_type='USRP B210',
    ...     start_freq=88e6,
    ...     stop_freq=108e6,
    ... )
    """
    session_md = get_session_metadata(experiment_id, purpose)
    plan_md = get_plan_metadata(plan_type)
    env_md = add_environmental_metadata(temperature, humidity)
    hw_md = add_hardware_metadata(sdr_type)

    return combine_metadata(
        FACILITY_MD,
        session_md,
        plan_md,
        env_md,
        hw_md,
        **kwargs
    )


def get_standard_fm_metadata(station_name='Ottawa FM', **kwargs):
    """
    Get standard metadata for FM radio experiments.

    Parameters
    ----------
    station_name : str, optional
        Name of the FM station or area (default: 'Ottawa FM')
    **kwargs
        Additional metadata fields

    Returns
    -------
    dict
        FM-specific metadata

    Examples
    --------
    >>> md = get_standard_fm_metadata(
    ...     station_name='CHEZ 106.1 FM',
    ...     carrier_freq=106.1e6,
    ... )
    """
    md = {
        'sample': station_name,
        'signal_type': 'FM broadcast',
        'modulation': 'wideband FM',
        'fm_bandwidth': 200e3,  # Standard FM bandwidth
    }
    md.update(kwargs)
    return md


def get_standard_ejfat_metadata(data_rate=None, num_nodes=None, **kwargs):
    """
    Get standard metadata for EJFAT experiments.

    Parameters
    ----------
    data_rate : float, optional
        Data rate in bytes/second
    num_nodes : int, optional
        Number of EJFAT nodes
    **kwargs
        Additional metadata fields

    Returns
    -------
    dict
        EJFAT-specific metadata
    """
    md = {
        'system': 'EJFAT',
        'protocol': 'E2SAR',
    }
    if data_rate is not None:
        md['data_rate_bps'] = data_rate
    if num_nodes is not None:
        md['num_nodes'] = num_nodes

    md.update(kwargs)
    return md


def save_metadata_to_file(metadata, filename='metadata.json'):
    """
    Save metadata dictionary to JSON file.

    Parameters
    ----------
    metadata : dict
        Metadata dictionary
    filename : str or Path
        Output filename

    Examples
    --------
    >>> md = create_experiment_metadata('EXP-001', 'Test')
    >>> save_metadata_to_file(md, 'data/exp001_metadata.json')
    """
    import json

    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)

    print(f"Metadata saved to: {filepath}")


def load_metadata_from_file(filename):
    """
    Load metadata from JSON file.

    Parameters
    ----------
    filename : str or Path
        Input filename

    Returns
    -------
    dict
        Metadata dictionary
    """
    import json

    with open(filename, 'r') as f:
        metadata = json.load(f)

    return metadata
