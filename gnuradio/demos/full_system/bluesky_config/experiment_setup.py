"""
Standardized experiment setup with persistent DataBroker.

This module provides a unified way to set up experiments with:
- RunEngine configuration
- DataBroker with persistent storage
- Standard callbacks
- Proper subscriptions

All experiments should use create_experiment_environment() for consistent setup.
"""

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from databroker import Broker
import config
import matplotlib
# Set non-interactive backend for headless operation
matplotlib.use('Agg')


def create_experiment_environment(
    headless=True,
    enable_serializer=True,
    enable_document_logger=True,
    enable_bec=True,
    verbose=True
):
    """
    Create a complete experiment environment with RunEngine and DataBroker.

    This is the recommended way to set up experiments. It provides:
    - RunEngine with proper configuration
    - DataBroker with persistent storage (via suitcase-msgpack)
    - BestEffortCallback for live feedback
    - DocumentLogger for JSON backup
    - All properly subscribed

    Parameters
    ----------
    headless : bool, optional
        If True, disable interactive plotting (default: True)
    enable_serializer : bool, optional
        If True, enable persistent catalog via suitcase-msgpack (default: True)
    enable_document_logger : bool, optional
        If True, save JSON documents to data/documents/ (default: True)
    enable_bec : bool, optional
        If True, enable BestEffortCallback for live tables/plots (default: True)
    verbose : bool, optional
        If True, print setup information (default: True)

    Returns
    -------
    dict
        Dictionary with keys:
        - 'RE': RunEngine instance
        - 'db': DataBroker instance
        - 'bec': BestEffortCallback (or None)
        - 'serializer': Suitcase serializer (or None)
        - 'doc_logger': DocumentLogger (or None)

    Examples
    --------
    >>> from bluesky_config.experiment_setup import create_experiment_environment
    >>> from bluesky_config.devices import MockDetector
    >>> from bluesky.plans import count
    >>>
    >>> # Set up experiment
    >>> env = create_experiment_environment()
    >>> RE = env['RE']
    >>> db = env['db']
    >>>
    >>> # Create devices
    >>> det = MockDetector(name='det')
    >>>
    >>> # Run experiment
    >>> RE(count([det], num=10))
    >>>
    >>> # Retrieve data immediately
    >>> run = db[-1]
    >>> table = run.table()
    """
    if verbose:
        print("\n" + "="*70)
        print("CREATING EXPERIMENT ENVIRONMENT")
        print("="*70)

    # Create RunEngine
    RE = RunEngine(config.RUNENGINE_MD)

    if verbose:
        print("\n✅ RunEngine created")
        print(f"   Metadata: {config.FACILITY_MD}")

    # Create BestEffortCallback
    bec = None
    if enable_bec:
        bec = BestEffortCallback()
        if headless:
            bec.disable_plots()
        RE.subscribe(bec)

        if verbose:
            mode = "headless" if headless else "interactive"
            print(f"✅ BestEffortCallback subscribed ({mode})")

    # Set up DataBroker with persistent storage
    db = Broker.named('temp')  # In-memory for same-session retrieval

    if verbose:
        print("✅ DataBroker created (temp catalog for in-session retrieval)")

    # Subscribe DataBroker to RunEngine
    RE.subscribe(db.v1.insert)

    if verbose:
        print("   ✅ Subscribed to RunEngine (use db[-1] for immediate retrieval)")

    # Set up persistent storage with suitcase-msgpack
    serializer = None
    if enable_serializer:
        try:
            from suitcase.msgpack import Serializer

            # Ensure catalog directory exists
            config.CATALOG_DIR.mkdir(parents=True, exist_ok=True)

            # Create serializer
            serializer = Serializer(config.CATALOG_DIR)
            RE.subscribe(serializer)

            if verbose:
                print(f"✅ Suitcase serializer subscribed")
                print(f"   Persistent storage: {config.CATALOG_DIR}")

        except ImportError:
            if verbose:
                print("⚠️  suitcase-msgpack not available")
                print("   Install with: pip install suitcase-msgpack")
                print("   Experiments will still save to documents/")

    # Set up DocumentLogger for JSON backup
    doc_logger = None
    if enable_document_logger:
        from bluesky_config.callbacks import DocumentLogger

        doc_logger = DocumentLogger(config.DOCUMENT_DIR)
        RE.subscribe(doc_logger)

        if verbose:
            print(f"✅ DocumentLogger subscribed")
            print(f"   JSON documents: {config.DOCUMENT_DIR}")

    if verbose:
        print("\n" + "="*70)
        print("ENVIRONMENT READY")
        print("="*70)
        print("\nData will be saved to:")
        if serializer:
            print(f"  ✅ Catalog (msgpack): {config.CATALOG_DIR}")
        print(f"  ✅ Documents (JSON):  {config.DOCUMENT_DIR}")
        print("\nRetrieve data with:")
        print("  run = db[-1]  # Latest run")
        print("  table = run.table()")
        print("="*70 + "\n")

    return {
        'RE': RE,
        'db': db,
        'bec': bec,
        'serializer': serializer,
        'doc_logger': doc_logger,
    }


def create_headless_environment(verbose=True):
    """
    Convenience function for headless (non-interactive) experiments.

    This is a shortcut for:
        create_experiment_environment(headless=True)

    Returns
    -------
    dict
        Environment dictionary (see create_experiment_environment)
    """
    return create_experiment_environment(
        headless=True,
        enable_serializer=True,
        enable_document_logger=True,
        enable_bec=True,
        verbose=verbose
    )


def create_interactive_environment(verbose=True):
    """
    Convenience function for interactive experiments with live plots.

    This is a shortcut for:
        create_experiment_environment(headless=False)

    Returns
    -------
    dict
        Environment dictionary (see create_experiment_environment)
    """
    return create_experiment_environment(
        headless=False,
        enable_serializer=True,
        enable_document_logger=True,
        enable_bec=True,
        verbose=verbose
    )


# Legacy compatibility - keep old function names
def get_standard_re_db(verbose=True):
    """
    Legacy function for backwards compatibility.

    Use create_experiment_environment() instead.
    """
    env = create_experiment_environment(verbose=verbose)
    return env['RE'], env['db']
