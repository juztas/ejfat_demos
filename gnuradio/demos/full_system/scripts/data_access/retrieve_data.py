#!/usr/bin/env python3
"""
Retrieve and display data from saved Bluesky documents.

This script demonstrates how to load experiment data from the persistent
document storage and analyze it.
"""

import json
from pathlib import Path
import sys
from collections import defaultdict
import argparse


def load_documents_from_file(filepath):
    """
    Load Bluesky documents from a JSONL file.

    Parameters
    ----------
    filepath : Path
        Path to the JSONL document file

    Returns
    -------
    dict
        Dictionary of document_name: [documents] lists
    """
    documents = defaultdict(list)

    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                doc_dict = json.loads(line)
                # Each line is {document_name: document}
                for name, doc in doc_dict.items():
                    documents[name].append(doc)

    return documents


def display_run_summary(documents):
    """
    Display summary of a run from its documents.

    Parameters
    ----------
    documents : dict
        Dictionary of documents
    """
    # Get start document
    if 'start' not in documents or not documents['start']:
        print("No start document found")
        return

    start = documents['start'][0]

    print("\n" + "="*70)
    print("RUN SUMMARY")
    print("="*70)
    print(f"\nUID: {start['uid']}")
    print(f"Scan ID: {start['scan_id']}")
    print(f"Plan: {start['plan_name']}")
    print(f"Operator: {start.get('operator', 'N/A')}")
    print(f"Purpose: {start.get('purpose', 'N/A')}")
    print(f"Time: {start['time']}")

    # Plan details
    if 'plan_args' in start:
        print(f"\nPlan Arguments:")
        for key, value in start['plan_args'].items():
            print(f"  {key}: {value}")

    # Custom metadata
    print(f"\nMetadata:")
    for key in ['experiment_id', 'facility', 'beamline', 'temperature', 'humidity']:
        if key in start:
            print(f"  {key}: {start[key]}")

    # Event count
    event_count = len(documents.get('event', []))
    print(f"\nEvents collected: {event_count}")

    # Stop document
    if 'stop' in documents and documents['stop']:
        stop = documents['stop'][0]
        print(f"Exit status: {stop.get('exit_status', 'unknown')}")

    print("="*70)


def display_data_table(documents, max_rows=20):
    """
    Display data in table format.

    Parameters
    ----------
    documents : dict
        Dictionary of documents
    max_rows : int
        Maximum number of rows to display
    """
    events = documents.get('event', [])

    if not events:
        print("\nNo event data found")
        return

    # Get column names from first event
    first_event = events[0]
    columns = ['seq_num', 'time'] + list(first_event.get('data', {}).keys())

    print("\n" + "="*70)
    print("DATA TABLE")
    print("="*70)

    # Print header
    header = " | ".join([f"{col:15s}" for col in columns])
    print(header)
    print("-" * len(header))

    # Print data rows
    for i, event in enumerate(events[:max_rows]):
        row = [
            f"{event.get('seq_num', i):15d}",
            f"{event.get('time', 0):15.6f}",
        ]
        for key in columns[2:]:  # Skip seq_num and time
            value = event.get('data', {}).get(key, '')
            if isinstance(value, float):
                row.append(f"{value:15.6f}")
            else:
                row.append(f"{str(value):15s}")

        print(" | ".join(row))

    if len(events) > max_rows:
        print(f"... ({len(events) - max_rows} more rows)")

    print("="*70)


def compute_statistics(documents):
    """
    Compute statistics from event data.

    Parameters
    ----------
    documents : dict
        Dictionary of documents
    """
    events = documents.get('event', [])

    if not events:
        print("\nNo data to analyze")
        return

    # Collect numeric data
    data_keys = list(events[0].get('data', {}).keys())
    data_arrays = {key: [] for key in data_keys}

    for event in events:
        for key in data_keys:
            value = event.get('data', {}).get(key)
            if isinstance(value, (int, float)):
                data_arrays[key].append(value)

    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)

    import numpy as np

    for key, values in data_arrays.items():
        if values:
            arr = np.array(values)
            print(f"\n{key}:")
            print(f"  Count:  {len(arr)}")
            print(f"  Mean:   {np.mean(arr):.6f}")
            print(f"  Std:    {np.std(arr):.6f}")
            print(f"  Min:    {np.min(arr):.6f}")
            print(f"  Max:    {np.max(arr):.6f}")
            print(f"  Median: {np.median(arr):.6f}")

    print("="*70)


def list_saved_runs(doc_dir='data/documents'):
    """
    List all saved runs.

    Parameters
    ----------
    doc_dir : str or Path
        Directory containing saved documents
    """
    doc_path = Path(doc_dir)

    if not doc_path.exists():
        print(f"No documents directory found: {doc_path}")
        return []

    doc_files = list(doc_path.glob('*.jsonl'))

    if not doc_files:
        print(f"No saved runs found in: {doc_path}")
        return []

    print("\n" + "="*70)
    print("SAVED RUNS")
    print("="*70)

    runs = []

    for doc_file in sorted(doc_files):
        try:
            documents = load_documents_from_file(doc_file)
            if 'start' in documents and documents['start']:
                start = documents['start'][0]
                uid = start['uid'][:8]
                scan_id = start.get('scan_id', '?')
                plan = start.get('plan_name', 'unknown')
                purpose = start.get('purpose', 'N/A')
                operator = start.get('operator', 'N/A')

                print(f"[{scan_id:3}] {uid} | {plan:20s} | {operator:10s} | {doc_file.name}")

                runs.append({
                    'file': doc_file,
                    'uid': start['uid'],
                    'scan_id': scan_id,
                    'start': start
                })
        except Exception as e:
            print(f"Error loading {doc_file.name}: {e}")

    print("="*70)
    print(f"\nTotal runs: {len(runs)}")

    return runs


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Retrieve and display saved Bluesky experiment data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                      # List all saved runs
  %(prog)s --uid 85067302              # Show run by UID prefix
  %(prog)s --latest                    # Show latest run
  %(prog)s --latest --table            # Show data table
  %(prog)s --latest --stats            # Show statistics
  %(prog)s --latest --all              # Show everything
        """
    )

    parser.add_argument('--list', action='store_true',
                       help='List all saved runs')
    parser.add_argument('--uid', type=str,
                       help='UID or UID prefix of run to display')
    parser.add_argument('--latest', action='store_true',
                       help='Display latest run')
    parser.add_argument('--table', action='store_true',
                       help='Show data table')
    parser.add_argument('--stats', action='store_true',
                       help='Show statistics')
    parser.add_argument('--all', action='store_true',
                       help='Show everything (summary + table + stats)')
    parser.add_argument('--max-rows', type=int, default=20,
                       help='Maximum rows to display in table')

    args = parser.parse_args()

    # List runs
    if args.list or (not args.uid and not args.latest):
        list_saved_runs()
        return 0

    # Find run to display
    doc_path = Path('data/documents')
    doc_file = None

    if args.uid:
        # Find by UID prefix
        matching = list(doc_path.glob(f'{args.uid}*_documents.jsonl'))
        if not matching:
            print(f"No run found with UID prefix: {args.uid}")
            return 1
        doc_file = matching[0]

    elif args.latest:
        # Get latest file
        doc_files = sorted(doc_path.glob('*.jsonl'))
        if not doc_files:
            print("No saved runs found")
            return 1
        doc_file = doc_files[-1]

    # Load and display
    print(f"\nLoading: {doc_file.name}")
    documents = load_documents_from_file(doc_file)

    # Always show summary
    display_run_summary(documents)

    # Show table if requested
    if args.table or args.all:
        display_data_table(documents, max_rows=args.max_rows)

    # Show stats if requested
    if args.stats or args.all:
        compute_statistics(documents)

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
