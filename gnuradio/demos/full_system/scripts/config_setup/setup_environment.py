"""
Setup Bluesky environment with RunEngine and DataBroker.

This module initializes the core Bluesky components and is imported
by experiment scripts to get a configured RunEngine and DataBroker.
"""

from bluesky_config.run_engine_setup import create_headless_run_engine
from databroker import Broker
import config


def setup_databroker(catalog_type=None, verbose=True):
    """
    Setup and return DataBroker catalog.

    Parameters
    ----------
    catalog_type : str, optional
        Type of catalog: 'temp', 'sqlite', or 'mongodb'
        If None, uses default from config
    verbose : bool, optional
        Print setup information (default: True)

    Returns
    -------
    Broker
        Configured DataBroker instance
    """
    if catalog_type is None:
        catalog_type = config.DEFAULT_CATALOG

    if verbose:
        print(f"Setting up DataBroker ({catalog_type} catalog)...")

    # Create catalog based on type
    if catalog_type == 'temp':
        db = Broker.named('temp')
        if verbose:
            print("  ⚠️  Using temporary in-memory catalog (data will be lost on exit)")
            print("  ℹ️  Documents will be saved to disk via DocumentLogger")

    elif catalog_type == 'sqlite':
        # For persistent storage, use temp catalog but save documents to disk
        # Documents will be saved by DocumentLogger callback
        db = Broker.named('temp')
        if verbose:
            print(f"  ℹ️  Using persistent storage via DocumentLogger")
            print(f"  📁 Documents saved to: {config.DOCUMENT_DIR}")
            print(f"  📁 Catalog directory: {config.CATALOG_DIR}")

            # Check for existing documents
            import glob
            doc_files = glob.glob(str(config.DOCUMENT_DIR / '*.jsonl'))
            if doc_files:
                print(f"  ℹ️  Found {len(doc_files)} existing document files")

    elif catalog_type == 'mongodb':
        try:
            db_config = config.get_databroker_config(catalog_type)
            db = Broker.from_config(config.DATABROKER_MONGODB_CONFIG)
            if verbose:
                print(f"  ✅ Connected to MongoDB at "
                      f"{db_config['config']['host']}:{db_config['config']['port']}")
        except Exception as e:
            if verbose:
                print(f"  ⚠️  MongoDB connection failed: {e}")
                print("  ℹ️  Falling back to temporary catalog with file persistence")
            db = Broker.named('temp')

    else:
        raise ValueError(f"Unknown catalog type: {catalog_type}")

    if verbose:
        print(f"  ✅ DataBroker ready\n")

    return db


def setup_runengine(db=None, verbose=True, headless=True):
    """
    Setup and return configured RunEngine.

    Parameters
    ----------
    db : Broker, optional
        DataBroker instance to subscribe to RunEngine
        If None, no data will be saved
    verbose : bool, optional
        Print setup information (default: True)
    headless : bool, optional
        Use headless (no GUI) RunEngine setup (default: True)

    Returns
    -------
    RunEngine
        Configured RunEngine instance
    """
    if verbose:
        print("Setting up RunEngine...")

    # Create RunEngine with metadata
    if headless:
        RE, bec = create_headless_run_engine()
        # Update metadata
        RE.md.update(config.RUNENGINE_MD)
        if verbose:
            print("  ✅ Headless RunEngine created (no GUI/plots)")
    else:
        from bluesky import RunEngine
        RE = RunEngine(config.RUNENGINE_MD)
        bec = None

    # Subscribe DataBroker if provided
    if db is not None:
        RE.subscribe(db.insert)
        if verbose:
            print("  ✅ DataBroker subscribed to RunEngine")

    # Setup default callbacks
    if config.ENABLE_BEST_EFFORT_CALLBACK:
        if bec is None:
            from bluesky.callbacks.best_effort import BestEffortCallback
            bec = BestEffortCallback()
        RE.subscribe(bec)
        if verbose:
            mode = "headless" if headless else "live table & plots"
            print(f"  ✅ BestEffortCallback enabled ({mode})")

    if config.ENABLE_DOCUMENT_LOGGER:
        from bluesky_config.callbacks import DocumentLogger
        doc_logger = DocumentLogger(config.DOCUMENT_DIR)
        RE.subscribe(doc_logger)
        if verbose:
            print(f"  ✅ DocumentLogger enabled (saving to {config.DOCUMENT_DIR})")

    if verbose:
        print(f"  ✅ RunEngine ready\n")

    return RE


def setup_environment(catalog_type=None, verbose=True, headless=True):
    """
    Setup complete Bluesky environment.

    Convenience function that creates both DataBroker and RunEngine.

    Parameters
    ----------
    catalog_type : str, optional
        Type of catalog: 'temp', 'sqlite', or 'mongodb'
    verbose : bool, optional
        Print setup information (default: True)
    headless : bool, optional
        Use headless (no GUI) RunEngine setup (default: True)

    Returns
    -------
    RE, db
        Tuple of (RunEngine, DataBroker)

    Examples
    --------
    >>> from setup_environment import setup_environment
    >>> RE, db = setup_environment()
    >>> # Now ready to run experiments
    """
    if verbose:
        print("\n" + "="*70)
        print("BLUESKY ENVIRONMENT SETUP")
        print("="*70 + "\n")

    db = setup_databroker(catalog_type, verbose)
    RE = setup_runengine(db, verbose, headless=headless)

    if verbose:
        print("="*70)
        print("SETUP COMPLETE - Ready for experiments!")
        print("="*70 + "\n")

    return RE, db


def create_standard_devices(verbose=True):
    """
    Create standard device instances.

    Returns
    -------
    dict
        Dictionary of device_name: device_instance
    """
    from bluesky_config.devices import (GNURadioSignalGenerator, FMTransmitter,
                                         MockDetector, PowerMeter)

    devices = {}

    if verbose:
        print("Creating standard devices...\n")

    # Try to create GNU Radio signal generator
    try:
        sig_gen = GNURadioSignalGenerator(
            '',
            name='sig_gen',
            host=config.GNURADIO_DEFAULT_HOST,
            port=config.GNURADIO_DEFAULT_PORT
        )
        devices['sig_gen'] = sig_gen
        if verbose:
            print("  ✅ Created GNURadioSignalGenerator (sig_gen)")
    except ConnectionError as e:
        if verbose:
            print(f"  ⚠️  Could not connect to GNU Radio: {e}")
            print("     (This is normal if GNU Radio is not running)")

    # Create mock devices (always available)
    devices['mock_det'] = MockDetector(name='mock_det', noise_level=0.15)
    devices['power_meter'] = PowerMeter(name='power_meter')

    if verbose:
        print("  ✅ Created MockDetector (mock_det)")
        print("  ✅ Created PowerMeter (power_meter)")
        print()

    return devices


# Example usage when run as script
if __name__ == "__main__":
    # Setup environment
    RE, db = setup_environment(catalog_type='temp', verbose=True)

    # Create devices
    devices = create_standard_devices(verbose=True)

    # Show what's available
    print("Available devices:")
    for name, device in devices.items():
        print(f"  - {name}: {type(device).__name__}")

    print("\nYou can now run experiments!")
    print("\nExample:")
    print("  from bluesky.plans import count")
    print("  RE(count([devices['mock_det']], num=10))")
