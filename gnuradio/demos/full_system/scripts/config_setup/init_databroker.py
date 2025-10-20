#!/usr/bin/env python3
"""
Initialize persistent DataBroker catalog.

This script sets up a persistent DataBroker catalog using the modern
databroker v2 API with suitcase serialization.
"""

import sys
from pathlib import Path
import config


def init_persistent_catalog(verbose=True):
    """
    Initialize a persistent DataBroker catalog.

    This uses suitcase-msgpack to serialize documents to disk.
    Data persists between sessions.

    Returns
    -------
    catalog : Catalog
        DataBroker v2 catalog
    """
    if verbose:
        print("\n" + "="*70)
        print("INITIALIZING PERSISTENT DATABROKER CATALOG")
        print("="*70 + "\n")

    # Ensure catalog directory exists
    config.CATALOG_DIR.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Catalog directory: {config.CATALOG_DIR}")
        print(f"Catalog name: {config.CATALOG_NAME}")

    # Try to use databroker v2
    try:
        from databroker import catalog
        from suitcase.msgpack import Serializer

        # Check if catalog exists
        if config.CATALOG_NAME in catalog:
            if verbose:
                print(f"\n✅ Found existing catalog '{config.CATALOG_NAME}'")

            cat = catalog[config.CATALOG_NAME]

            # Show existing runs
            try:
                runs = list(cat)
                if verbose:
                    print(f"   Contains {len(runs)} runs")
                    if runs:
                        latest = runs[-1]
                        start = latest.metadata['start']
                        print(f"   Latest run: {start['scan_id']} - "
                              f"{start.get('plan_name', 'unknown')} - "
                              f"UID: {start['uid'][:8]}")
            except Exception as e:
                if verbose:
                    print(f"   (Could not count runs: {e})")

        else:
            if verbose:
                print(f"\n⚠️  Catalog '{config.CATALOG_NAME}' not found")
                print("   This is normal for first-time setup")
                print("   Documents will be saved via DocumentLogger callback")
                print(f"   Location: {config.DOCUMENT_DIR}")

            # Create a simple in-memory broker for now
            # Documents will be saved by DocumentLogger callback
            from databroker import Broker
            cat = Broker.named('temp')

            if verbose:
                print("\n   Using temporary catalog for now")
                print("   (Documents still saved to disk via callback)")

    except ImportError as e:
        if verbose:
            print(f"\n⚠️  Modern databroker v2 not available: {e}")
            print("   Falling back to databroker v1 with temp catalog")

        from databroker import Broker
        cat = Broker.named('temp')

        if verbose:
            print("   Documents will be saved via DocumentLogger callback")

    if verbose:
        print("\n" + "="*70)
        print("DATABROKER READY")
        print("="*70 + "\n")

    return cat


def setup_serializer(catalog_dir=None):
    """
    Setup suitcase serializer for persistent storage.

    Parameters
    ----------
    catalog_dir : Path, optional
        Directory to save serialized documents

    Returns
    -------
    Serializer
        Suitcase serializer instance
    """
    if catalog_dir is None:
        catalog_dir = config.CATALOG_DIR

    try:
        from suitcase.msgpack import Serializer

        # Create serializer
        serializer = Serializer(catalog_dir)

        print(f"✅ Suitcase serializer ready")
        print(f"   Saving documents to: {catalog_dir}")

        return serializer

    except ImportError:
        print("⚠️  suitcase-msgpack not available")
        print("   Install with: pip install suitcase-msgpack")
        return None


def create_catalog_callback(catalog_dir=None):
    """
    Create a callback that saves documents to disk using suitcase.

    This provides persistent storage without requiring databroker v2.

    Parameters
    ----------
    catalog_dir : Path, optional
        Directory to save documents

    Returns
    -------
    Serializer or DocumentLogger
        Callback that saves documents
    """
    if catalog_dir is None:
        catalog_dir = config.CATALOG_DIR

    # Try suitcase first
    try:
        from suitcase.msgpack import Serializer
        return Serializer(catalog_dir)
    except ImportError:
        pass

    # Fallback to DocumentLogger
    from bluesky_config.callbacks import DocumentLogger
    return DocumentLogger(catalog_dir)


def show_catalog_stats(catalog, max_runs=10):
    """
    Show statistics about catalog contents.

    Parameters
    ----------
    catalog : Catalog or Broker
        DataBroker catalog
    max_runs : int
        Maximum number of recent runs to display
    """
    print("\n" + "="*70)
    print("CATALOG STATISTICS")
    print("="*70 + "\n")

    try:
        # Try to get all runs
        runs = list(catalog)

        if not runs:
            print("No runs in catalog")
            return

        print(f"Total runs: {len(runs)}\n")

        # Show recent runs
        recent = runs[-max_runs:]
        print(f"Most recent {len(recent)} runs:")
        print("-" * 70)

        for run in recent:
            start = run.metadata['start']
            print(f"Scan {start['scan_id']:3d} | "
                  f"{start['uid'][:8]} | "
                  f"{start.get('plan_name', 'unknown'):20s} | "
                  f"{start.get('operator', 'N/A'):10s}")

        print("-" * 70)

    except Exception as e:
        print(f"Could not retrieve catalog stats: {e}")

    print()


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Initialize persistent DataBroker catalog'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show catalog statistics'
    )
    parser.add_argument(
        '--setup-serializer',
        action='store_true',
        help='Setup suitcase serializer'
    )

    args = parser.parse_args()

    # Initialize catalog
    catalog = init_persistent_catalog(verbose=True)

    # Show stats if requested
    if args.stats:
        show_catalog_stats(catalog)

    # Setup serializer if requested
    if args.setup_serializer:
        print()
        setup_serializer()

    print("✅ Initialization complete\n")
    print("To use this catalog in your experiments:")
    print("  from databroker import Broker")
    print("  db = Broker.named('temp')  # Or use catalog from init_databroker")
    print("\nDocuments are automatically saved to:")
    print(f"  {config.DOCUMENT_DIR}")
    print(f"  {config.CATALOG_DIR}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
