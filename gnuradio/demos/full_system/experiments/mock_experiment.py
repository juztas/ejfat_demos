#!/usr/bin/env python3
"""
Mock Experiment (No Hardware Required)

This is a simple experiment using mock devices for testing the Bluesky
framework without requiring GNU Radio or other hardware.

✨ UPDATED: Now uses persistent DataBroker catalog ✨

This experiment demonstrates the RECOMMENDED setup pattern:
- Uses create_experiment_environment() for standardized setup
- Automatically gets persistent DataBroker catalog (data/catalog/*.msgpack)
- Saves to both msgpack catalog AND JSON documents (data/documents/*.jsonl)
- Includes standard callbacks for monitoring
- Data accessible via db[-1] immediately AND across sessions
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky_config.experiment_setup import create_experiment_environment
from ophyd import Signal
from bluesky.plans import scan
from bluesky_config.devices import MockDetector
from bluesky_config.callbacks import (PeakDetectorCallback, StatisticsCallback,
                                      ProgressCallback)
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run mock experiment with persistent DataBroker."""

    # ==================== EXPERIMENT SETUP ====================
    # This is the RECOMMENDED approach for all experiments:
    # create_experiment_environment() provides:
    #   - RunEngine with proper configuration
    #   - DataBroker with persistent catalog (msgpack files)
    #   - Document logger for JSON backup
    #   - All callbacks properly subscribed
    # ==========================================================

    env = create_experiment_environment(headless=True, verbose=False)

    RE = env['RE']        # RunEngine
    db = env['db']        # DataBroker (can use db[-1] for retrieval)
    # env also contains: bec, serializer, doc_logger

    print("\n" + "="*70)
    print("🔧 ENVIRONMENT SETUP COMPLETE")
    print("="*70)
    print("✅ RunEngine configured")
    print("✅ DataBroker ready (persistent catalog)")
    print("✅ Serializer enabled (saves to data/catalog/*.msgpack)")
    print("✅ DocumentLogger enabled (saves to data/documents/*.jsonl)")
    print("="*70)

    # Add custom callbacks for this experiment
    peak_detector = PeakDetectorCallback('det_value', threshold=1.2)
    RE.subscribe(peak_detector)

    stats = StatisticsCallback(['det_value'])
    RE.subscribe(stats)

    progress = ProgressCallback()
    RE.subscribe(progress)

    # Create mock devices (no hardware required)
    motor = Signal(name='motor', value=0)
    detector = MockDetector(name='det', noise_level=0.15)

    # Scan parameters
    start = 0
    stop = 10
    num_points = 20

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='MOCK-001',
        purpose='Test Bluesky framework with mock devices and persistent DataBroker',
        plan_type='scan',
        start=start,
        stop=stop,
        num_points=num_points,
    )

    print("\n" + "="*70)
    print("MOCK EXPERIMENT (No Hardware Required)")
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
    print("✅ EXPERIMENT COMPLETE")
    print("="*70)
    print(f"Run UID: {uid[0]}")
    print(f"Short UID: {uid[0][:8]}")

    # ==================== DATA RETRIEVAL ====================
    # Demonstrate immediate data access via DataBroker
    # ==========================================================

    print("\n📊 Retrieving data from DataBroker...")

    try:
        # Get latest run from DataBroker
        run = db[-1]
        table = run.table()

        print(f"✅ Data retrieved successfully!")
        print(f"\nData shape: {table.shape}")
        print(f"Columns: {list(table.columns)}")

        print("\n" + "-"*70)
        print("DATA PREVIEW (first 5 rows):")
        print("-"*70)
        print(table.head())

        print("\n" + "-"*70)
        print("STATISTICS:")
        print("-"*70)
        print(table['det_value'].describe())

    except Exception as e:
        print(f"⚠️  Could not retrieve from DataBroker: {e}")
        print("   Data is still saved to documents/")

    # Show where data was saved
    print("\n" + "="*70)
    print("💾 DATA SAVED TO:")
    print("="*70)
    print(f"✅ Persistent catalog: data/catalog/{uid[0][:8]}*.msgpack")
    print(f"✅ JSON documents:     data/documents/{uid[0][:8]}_documents.jsonl")

    print("\n" + "="*70)
    print("🔍 HOW TO ACCESS THIS DATA:")
    print("="*70)

    print("\n1️⃣  Quick access script:")
    print("    python access_my_data.py")

    print("\n2️⃣  In Python (same session):")
    print("    from databroker import Broker")
    print("    db = Broker.named('temp')")
    print("    run = db[-1]")
    print("    table = run.table()")

    print("\n3️⃣  From saved catalog (across sessions):")
    print("    from setup_databroker_helper import load_data_from_catalog")
    print("    cat = load_data_from_catalog()")
    print("    runs = list(cat.items())")
    print("    run = cat[runs[-1][0]]")

    print("\n4️⃣  From JSON documents:")
    print("    from setup_databroker_helper import load_from_documents")
    print(f"    run_data = load_from_documents(uid_prefix='{uid[0][:8]}')")

    print("\n" + "="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
