#!/usr/bin/env python3
"""
Quick script to access your existing experiment data.

This loads data from the saved JSON documents and provides
easy access even without a DataBroker catalog.
"""

import sys
from pathlib import Path

# Add project root and scripts/config_setup to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts" / "config_setup"))

from setup_databroker_helper import load_from_documents
import pandas as pd


def main():
    """Load and display latest experiment data."""

    print("\n" + "="*70)
    print("ACCESSING YOUR EXPERIMENT DATA")
    print("="*70 + "\n")

    # Load latest run
    run_data = load_from_documents(verbose=True)

    if not run_data:
        print("\n❌ No data found!")
        print("   Run an experiment first: python run_experiment.py mock_experiment")
        return 1

    # Extract metadata
    start = run_data['start']
    print("\n📋 METADATA:")
    print(f"   UID: {start['uid']}")
    print(f"   Plan: {start.get('plan_name', 'unknown')}")
    print(f"   Scan ID: {start.get('scan_id', 'N/A')}")
    print(f"   Experiment ID: {start.get('experiment_id', 'N/A')}")
    print(f"   Purpose: {start.get('purpose', 'N/A')}")
    print(f"   Operator: {start.get('operator', 'N/A')}")
    print(f"   Time: {start.get('time', 'N/A')}")

    # Extract data into DataFrame
    events = run_data['events']

    if not events:
        print("\n⚠️  No data events found")
        return 0

    print(f"\n📊 DATA: {len(events)} data points")

    # Build DataFrame from events
    data_rows = []
    for event in events:
        row = {'seq_num': event['seq_num'], 'time': event['time']}
        row.update(event['data'])
        data_rows.append(row)

    df = pd.DataFrame(data_rows)

    # Display data
    print("\n" + "="*70)
    print("DATA TABLE")
    print("="*70)
    print(df.to_string())

    # Statistics
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    numeric_cols = df.select_dtypes(include='number').columns
    print(df[numeric_cols].describe())

    # Save to CSV
    output_file = f"data/exports/{start['uid'][:8]}_data.csv"
    df.to_csv(output_file, index=False)
    print(f"\n💾 Saved to: {output_file}")

    print("\n" + "="*70)
    print("✅ DATA ACCESS COMPLETE")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
