"""
Configuration settings for the Bluesky experiment framework.

This module contains configuration parameters for the experiment setup,
including DataBroker settings, device connections, and metadata defaults.
"""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DOCUMENT_DIR = DATA_DIR / "documents"
EXPORT_DIR = DATA_DIR / "exports"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
DOCUMENT_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

# Facility-level metadata (constant for this beamline)
FACILITY_MD = {
    'facility': 'EJFAT',
    'beamline': 'gnuradio_testbed',
    'location': 'Ottawa',
}

# Default GNU Radio connection settings
GNURADIO_DEFAULT_HOST = 'localhost'
GNURADIO_DEFAULT_PORT = 8080

# DataBroker configuration options

# Option 1: Temporary in-memory catalog (for testing)
DATABROKER_TEMP_CONFIG = {
    'description': 'Temporary in-memory catalog',
    'driver': 'temp',
}

# Option 2: SQLite catalog (persistent, single-user)
# Modern databroker v2 uses msgpack files
DATABROKER_SQLITE_CONFIG = {
    'description': 'EJFAT GNU Radio Experiments',
    'driver': 'bluesky-msgpack-catalog',
    'args': {
        'paths': [str(DATA_DIR / 'catalog' / '*.msgpack')],
    },
    'metadata': {
        'timezone': 'US/Eastern',
    }
}

# Catalog name for persistent storage
CATALOG_NAME = 'ejfat_gnuradio'

# Catalog directory
CATALOG_DIR = DATA_DIR / 'catalog'
CATALOG_DIR.mkdir(exist_ok=True)

# Option 3: MongoDB catalog (production, multi-user)
# Requires MongoDB server running
DATABROKER_MONGODB_CONFIG = {
    'description': 'EJFAT Production Catalog',
    'driver': 'mongodb',
    'config': {
        'host': 'localhost',
        'port': 27017,
        'database': 'bluesky_metadata',
        'timezone': 'US/Eastern',
    }
}

# Default catalog to use
# Options: 'temp', 'sqlite', 'mongodb'
DEFAULT_CATALOG = 'sqlite'  # Changed to persistent storage


def get_databroker_config(catalog_type=None):
    """
    Get DataBroker configuration.

    Parameters
    ----------
    catalog_type : str, optional
        Type of catalog: 'temp', 'sqlite', or 'mongodb'
        If None, uses DEFAULT_CATALOG

    Returns
    -------
    dict
        DataBroker configuration dictionary
    """
    if catalog_type is None:
        catalog_type = DEFAULT_CATALOG

    configs = {
        'temp': DATABROKER_TEMP_CONFIG,
        'sqlite': DATABROKER_SQLITE_CONFIG,
        'mongodb': DATABROKER_MONGODB_CONFIG,
    }

    if catalog_type not in configs:
        raise ValueError(f"Unknown catalog type: {catalog_type}. "
                        f"Must be one of: {list(configs.keys())}")

    return configs[catalog_type]


# RunEngine configuration
RUNENGINE_MD = {
    **FACILITY_MD,
    'software_version': '0.1.0',
}

# Logging configuration
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "bluesky.log"

# Device registry (optional - for future use)
DEVICE_REGISTRY = {
    'sig_gen': {
        'class': 'GNURadioSignalGenerator',
        'host': GNURADIO_DEFAULT_HOST,
        'port': GNURADIO_DEFAULT_PORT,
    },
    'fm_tx': {
        'class': 'FMTransmitter',
        'host': GNURADIO_DEFAULT_HOST,
        'port': 8080,
    },
}

# Callback configuration
ENABLE_BEST_EFFORT_CALLBACK = True
ENABLE_DOCUMENT_LOGGER = True
ENABLE_LIVE_TABLE = False  # Can be verbose

# Plot configuration
PLOT_STYLE = 'seaborn-v0_8-darkgrid'  # Matplotlib style
PLOT_DPI = 150
PLOT_FIGSIZE = (10, 6)

# Export defaults
DEFAULT_EXPORT_FORMATS = ['csv', 'hdf5']
DEFAULT_EXPORT_DIR = EXPORT_DIR
