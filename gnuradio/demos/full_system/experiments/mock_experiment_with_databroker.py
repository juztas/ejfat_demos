#!/usr/bin/env python3
"""
Mock Experiment with DataBroker (FIXED VERSION)

This is a corrected version that properly integrates with DataBroker
for persistent data storage and retrieval.

Improvements over original:
- Subscribes RunEngine to DataBroker
- Saves data to persistent catalog (data/catalog/*.msgpack)
- Allows immediate data retrieval: db[-1]
- Still saves JSON documents as backup
- Data accessible across sessions
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky_config.run_engine_setup import create_headless_run_engine
from setup_databroker_helper import get_databroker_with_persistence
from ophyd import Signal
from bluesky.plans import scan
from bluesky_config.devices import MockDetector
from bluesky_config.callbacks import (PeakDetectorCallback, StatisticsCallback,
                                      ProgressCallback, DocumentLogger)
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run mock experiment with DataBroker integration."""

    # Create headless RunEngine (no GUI/plotting)
    RE, bec = create_headless_run_engine()
    RE.subscribe(bec)

    # Set up DataBroker with persistent storage
    print("\n🔧 Setting up DataBroker...")
    db, serializer = get_databroker_with_persistence(verbose=True)

    # Subscribe RunEngine to DataBroker
    print("\n📡 Subscribing RunEngine to DataBroker...")
    RE.subscribe(db.v1.insert)  # For in-session retrieval via db[-1]

    if serializer:
        RE.subscribe(serializer)  # For persistent catalog storage
        print("   ✅ Subscribed to serializer (persistent storage)")
    else:
        print("   ⚠️  Serializer not available (install suitcase-msgpack)")

    # Set up callbacks
    peak_detector = PeakDetectorCallback('det_value', threshold=1.2)
    RE.subscribe(peak_detector)

    stats = StatisticsCallback(['det_value'])
    RE.subscribe(stats)

    progress = ProgressCallback()
    RE.subscribe(progress)

    # Also save documents as JSON backup
    doc_logger = DocumentLogger('data/documents')
    RE.subscribe(doc_logger)
    print("   ✅ Subscribed to DocumentLogger (JSON backup)")

    # Create mock devices (no hardware required)
    motor = Signal(name='motor', value=0)
    detector = MockDetector(name='det', noise_level=0.15)

    # Scan parameters
    start = 0
    stop = 10
    num_points = 20

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='MOCK-DB-001',
        purpose='Test DataBroker integration with mock devices',
        plan_type='scan',
        start=start,
        stop=stop,
        num_points=num_points,
    )

    print("\n" + "="*70)
    print("MOCK EXPERIMENT WITH DATABROKER")
    print("="*70)
    print(f"Experiment ID: {md['experiment_id']}")
    print(f"Operator: {md['operator']}")
    print(f"Purpose: {md['purpose']}")
    print(f"\nMotor range: {start} - {stop}")
    print(f"Number of points: {num_points}")
    print("="*70 + "\n")

    # Run the scan
    print("🚀 Running scan...\n")
    uid = RE(scan([detector], motor, start, stop, num_points), **md)

    print("\n" + "="*70)
    print("EXPERIMENT COMPLETE")
    print("="*70)
    print(f"Run UID: {uid[0]}")
    print(f"Short UID: {uid[0][:8]}")

    # Retrieve data immediately from DataBroker
    print("\n📊 Retrieving data from DataBroker...")
    try:
        run = db[-1]
        table = run.table()

        print("\n" + "-"*70)
        print("DATA TABLE (first 5 rows)")
        print("-"*70)
        print(table.head())

        print("\n" + "-"*70)
        print("STATISTICS")
        print("-"*70)
        print(table['det_value'].describe())

        print("\n✅ Data successfully retrieved from DataBroker!")

    except Exception as e:
        print(f"\n⚠️  Could not retrieve from DataBroker: {e}")
        print("   Data is still saved to documents/")

    # Show where data was saved
    print("\n" + "="*70)
    print("DATA SAVED TO:")
    print("="*70)

    if serializer:
        print(f"✅ Persistent catalog: data/catalog/{uid[0][:8]}*.msgpack")
    else:
        print("⚠️  No catalog (install suitcase-msgpack)")

    print(f"✅ JSON documents: data/documents/{uid[0][:8]}_documents.jsonl")

    print("\n" + "="*70)
    print("HOW TO ACCESS THIS DATA LATER:")
    print("="*70)

    print("\nMethod 1: Quick access script")
    print("  python access_my_data.py")

    print("\nMethod 2: Load from catalog (if suitcase-msgpack installed)")
    print("  from setup_databroker_helper import load_data_from_catalog")
    print("  cat = load_data_from_catalog()")
    print("  runs = list(cat)")
    print("  table = runs[-1].table()")

    print("\nMethod 3: Load from documents")
    print("  from setup_databroker_helper import load_from_documents")
    print(f"  run_data = load_from_documents(uid_prefix='{uid[0][:8]}')")
    print("  events = run_data['events']")

    print("\n" + "="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
