#!/usr/bin/env python3
"""
Test script to verify DataBroker catalog connection.

This helps diagnose catalog connection issues.
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts" / "config_setup"))

from databroker import Broker


def test_catalog_connection():
    """Test connection to DataBroker catalogs."""
    print("\n" + "="*70)
    print("DATABROKER CATALOG CONNECTION TEST")
    print("="*70 + "\n")

    # Test 1: Try persistent catalog
    print("Test 1: Attempting to connect to 'ejfat_gnuradio' catalog...")
    try:
        db = Broker.named('ejfat_gnuradio')
        print("✅ Connected to persistent catalog: ejfat_gnuradio")
        catalog_type = "persistent"
    except Exception as e:
        print(f"⚠️  Could not connect to 'ejfat_gnuradio': {e}")
        print("   Falling back to temporary catalog...")
        db = Broker.named('temp')
        print("✅ Connected to temporary catalog (temp)")
        catalog_type = "temporary"

    print()

    # Test 2: Count runs - try multiple methods
    print("Test 2: Counting runs in catalog...")

    # Method 1: Direct iteration (DataBroker v1)
    try:
        # For DataBroker v1.x
        all_runs = list(db)
        print(f"✅ Method 1 (db iteration): {len(all_runs)} runs found")

        if all_runs:
            latest = all_runs[-1]
            print(f"\n   Latest run:")
            print(f"     UID: {latest.start['uid'][:8]}")
            print(f"     Plan: {latest.start.get('plan_name', 'unknown')}")
            print(f"     Time: {latest.start.get('time', 'N/A')}")
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")

    print()

    # Method 2: Using v1 attribute (if available)
    try:
        all_runs = list(db.v1)
        print(f"✅ Method 2 (db.v1): {len(all_runs)} runs found")
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")

    print()

    # Method 3: Using v2 attribute (if available)
    try:
        all_runs = list(db.v2)
        print(f"✅ Method 3 (db.v2): {len(all_runs)} runs found")
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")

    print()

    # Test 3: Check if we can retrieve latest run
    print("Test 3: Attempting to retrieve latest run...")
    try:
        latest = db[-1]
        print("✅ Successfully retrieved latest run")
        print(f"   UID: {latest.start['uid'][:8]}")
        print(f"   Plan: {latest.start.get('plan_name', 'unknown')}")
    except IndexError:
        print("⚠️  No runs in catalog (this is normal if no experiments have been run)")
    except Exception as e:
        print(f"❌ Error retrieving run: {e}")

    print()

    # Test 4: Check catalog registration
    print("Test 4: Checking catalog registration...")
    try:
        from databroker import catalog

        if 'ejfat_gnuradio' in catalog:
            print("✅ 'ejfat_gnuradio' is registered in intake catalog")
            cat = catalog['ejfat_gnuradio']
            print(f"   Type: {type(cat)}")
        else:
            print("⚠️  'ejfat_gnuradio' is NOT registered in intake catalog")
            print("\n   To register it, run:")
            print("   python scripts/config_setup/register_catalog.py")
    except ImportError:
        print("⚠️  intake-bluesky not available")
        print("   Install with: pip install intake-bluesky")

    print()

    # Test 5: Check for document files
    print("Test 5: Checking for saved document files...")
    try:
        import config
        doc_files = list(config.DOCUMENT_DIR.glob('*_documents.jsonl'))

        if doc_files:
            print(f"✅ Found {len(doc_files)} document files in {config.DOCUMENT_DIR}")
            print(f"\n   You can access this data with:")
            print(f"   python scripts/data_access/retrieve_data.py --list")
        else:
            print(f"⚠️  No document files found in {config.DOCUMENT_DIR}")
            print(f"   Run an experiment first:")
            print(f"   python scripts/cli/run_experiment.py mock_experiment")
    except Exception as e:
        print(f"❌ Error checking documents: {e}")

    # Summary
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\nCatalog type: {catalog_type}")

    if catalog_type == "temporary":
        print("\n⚠️  IMPORTANT: Using temporary catalog")
        print("   Data will be lost when Python exits")
        print("\nTo enable persistent storage:")
        print("   1. Run: python scripts/config_setup/register_catalog.py")
        print("   2. Restart Python and try again")
    else:
        print("\n✅ Using persistent catalog - data will be saved")

    print()
    print("To run an experiment:")
    print("   python scripts/cli/run_experiment.py mock_experiment")
    print()
    print("To view saved data:")
    print("   python scripts/data_access/retrieve_data.py --list")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(test_catalog_connection())
