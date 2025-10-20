#!/usr/bin/env python3
"""
DataBroker helper with persistent storage via suitcase.

This module provides a simple way to set up DataBroker with persistent
storage that works across sessions.
"""

from databroker import Broker
import config


def get_databroker_with_persistence(verbose=True):
    """
    Get DataBroker configured with persistent storage.

    This uses suitcase-msgpack to save all data to disk automatically.
    Data can be retrieved across sessions.

    Parameters
    ----------
    verbose : bool
        Print status messages

    Returns
    -------
    db : Broker
        DataBroker instance (in-memory for retrieval during session)
    serializer : Serializer or None
        Suitcase serializer for persistent storage (or None if not available)

    Examples
    --------
    >>> from bluesky import RunEngine
    >>> from setup_databroker_helper import get_databroker_with_persistence
    >>>
    >>> # Set up
    >>> RE = RunEngine({})
    >>> db, serializer = get_databroker_with_persistence()
    >>>
    >>> # Subscribe BOTH
    >>> RE.subscribe(db.v1.insert)  # For in-session retrieval
    >>> if serializer:
    ...     RE.subscribe(serializer)  # For persistent storage
    >>>
    >>> # Run experiments
    >>> # ... your scans ...
    >>>
    >>> # Retrieve immediately (same session)
    >>> run = db[-1]
    >>> table = run.table()
    """
    # Use temp broker for in-memory retrieval
    db = Broker.named('temp')

    # Try to set up persistent storage with suitcase
    serializer = None
    try:
        from suitcase.msgpack import Serializer

        # Ensure catalog directory exists
        config.CATALOG_DIR.mkdir(parents=True, exist_ok=True)

        # Create serializer
        serializer = Serializer(config.CATALOG_DIR)

        if verbose:
            print(f"✅ DataBroker ready with persistent storage")
            print(f"   In-session retrieval: Broker.named('temp')")
            print(f"   Persistent storage: {config.CATALOG_DIR}")
            print(f"   Documents also saved to: {config.DOCUMENT_DIR}")

    except ImportError:
        if verbose:
            print(f"⚠️  suitcase-msgpack not available")
            print(f"   Install with: pip install suitcase-msgpack")
            print(f"   Using in-memory catalog only")
            print(f"   Documents will still be saved to: {config.DOCUMENT_DIR}")

    return db, serializer


def load_data_from_catalog(verbose=True):
    """
    Load data from persistent catalog.

    This loads previously saved runs from the msgpack catalog.

    Returns
    -------
    catalog : Catalog or None
        DataBroker v2 catalog with saved runs, or None if not available

    Examples
    --------
    >>> from setup_databroker_helper import load_data_from_catalog
    >>>
    >>> # Load saved data
    >>> cat = load_data_from_catalog()
    >>>
    >>> if cat:
    ...     # Access runs
    ...     runs = list(cat)
    ...     latest = runs[-1]
    ...     table = latest.table()
    """
    try:
        from databroker import catalog as catalog_module
        from intake.catalog import Catalog

        # Check if catalog exists
        catalog_files = list(config.CATALOG_DIR.glob('*.msgpack'))

        if not catalog_files:
            if verbose:
                print(f"⚠️  No catalog files found in {config.CATALOG_DIR}")
                print(f"   Run some experiments first!")
            return None

        if verbose:
            print(f"✅ Found {len(catalog_files)} catalog files")

        # Try to create catalog
        from databroker._drivers.msgpack import BlueskyMsgpackCatalog

        cat = BlueskyMsgpackCatalog(str(config.CATALOG_DIR / '*.msgpack'))

        runs = list(cat)
        if verbose:
            print(f"📊 Total runs: {len(runs)}")

        return cat

    except ImportError as e:
        if verbose:
            print(f"⚠️  Could not load catalog: {e}")
            print(f"   You can still access data from {config.DOCUMENT_DIR}")
        return None


def load_from_documents(uid_prefix=None, verbose=True):
    """
    Load run data from JSON documents.

    This is a fallback method that works even without DataBroker catalog.

    Parameters
    ----------
    uid_prefix : str, optional
        UID prefix to match (e.g., '1aef708b')
        If None, loads the latest run
    verbose : bool
        Print status messages

    Returns
    -------
    dict
        Dictionary with 'start', 'descriptors', 'events', 'stop' documents

    Examples
    --------
    >>> from setup_databroker_helper import load_from_documents
    >>>
    >>> # Load latest run
    >>> run_data = load_from_documents()
    >>>
    >>> # Access documents
    >>> print(run_data['start']['plan_name'])
    >>> print(run_data['start']['scan_id'])
    >>>
    >>> # Extract data
    >>> for event in run_data['events']:
    ...     print(event['data'])
    """
    import json
    from pathlib import Path

    doc_dir = Path(config.DOCUMENT_DIR)

    if uid_prefix:
        # Find specific UID
        pattern = f"{uid_prefix}*_documents.jsonl"
        matches = list(doc_dir.glob(pattern))

        if not matches:
            if verbose:
                print(f"❌ No documents found matching: {pattern}")
            return None

        doc_file = matches[0]
    else:
        # Get latest
        doc_files = sorted(doc_dir.glob('*_documents.jsonl'))

        if not doc_files:
            if verbose:
                print(f"❌ No document files found in {doc_dir}")
            return None

        doc_file = doc_files[-1]

    if verbose:
        print(f"📂 Loading: {doc_file.name}")

    # Parse documents
    run_data = {
        'start': None,
        'descriptors': [],
        'events': [],
        'stop': None
    }

    with open(doc_file, 'r') as f:
        for line in f:
            doc = json.loads(line)

            if 'start' in doc:
                run_data['start'] = doc['start']
            elif 'descriptor' in doc:
                run_data['descriptors'].append(doc['descriptor'])
            elif 'event' in doc:
                run_data['events'].append(doc['event'])
            elif 'stop' in doc:
                run_data['stop'] = doc['stop']

    if verbose:
        print(f"✅ Loaded run: {run_data['start']['uid'][:8]}")
        print(f"   Plan: {run_data['start'].get('plan_name', 'unknown')}")
        print(f"   Events: {len(run_data['events'])}")

    return run_data


if __name__ == "__main__":
    import sys

    print("\n" + "="*70)
    print("DATABROKER HELPER - STATUS CHECK")
    print("="*70 + "\n")

    # Test setup
    print("1. Testing DataBroker setup...")
    db, serializer = get_databroker_with_persistence(verbose=True)

    print("\n2. Checking for existing catalog...")
    cat = load_data_from_catalog(verbose=True)

    print("\n3. Checking document files...")
    run_data = load_from_documents(verbose=True)

    print("\n" + "="*70)
    print("STATUS CHECK COMPLETE")
    print("="*70)

    if run_data:
        print("\n✅ You have existing data!")
        print(f"   Latest run: {run_data['start']['uid'][:8]}")
        print(f"   Plan: {run_data['start'].get('plan_name')}")
        print(f"   Data points: {len(run_data['events'])}")

    print()
