"""
Data export utilities for Bluesky experiments.

This module provides functions to export experiment data to various formats.
"""

import json
from pathlib import Path
import pandas as pd


def export_to_csv(run, filename, include_metadata=True):
    """
    Export run data to CSV file.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    filename : str or Path
        Output CSV filename
    include_metadata : bool, optional
        Include metadata as comments in header (default: True)

    Examples
    --------
    >>> from databroker import Broker
    >>> db = Broker.named('temp')
    >>> run = db[-1]
    >>> export_to_csv(run, 'data/my_scan.csv')
    """
    table = run.table()
    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if include_metadata:
        # Write metadata as header comments
        with open(filepath, 'w') as f:
            start = run.metadata['start']
            f.write(f"# Plan: {start['plan_name']}\n")
            f.write(f"# Operator: {start.get('operator', 'unknown')}\n")
            f.write(f"# Time: {start['time']}\n")
            f.write(f"# UID: {start['uid']}\n")
            f.write(f"# Purpose: {start.get('purpose', 'N/A')}\n")

            if 'plan_args' in start:
                f.write(f"# Plan args: {start['plan_args']}\n")

            f.write("#\n")

        # Append data
        table.to_csv(filepath, mode='a', index=False)
    else:
        table.to_csv(filepath, index=False)

    print(f"✅ Exported to CSV: {filepath}")
    return filepath


def export_to_hdf5(run, filename, compression=True):
    """
    Export run data to HDF5 file.

    HDF5 is efficient for large datasets and preserves data types.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    filename : str or Path
        Output HDF5 filename
    compression : bool, optional
        Use compression (default: True)

    Examples
    --------
    >>> export_to_hdf5(run, 'data/my_scan.h5')
    """
    table = run.table()
    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Save data table
    if compression:
        table.to_hdf(filepath, 'data', mode='w', complevel=9, complib='blosc')
    else:
        table.to_hdf(filepath, 'data', mode='w')

    # Save metadata separately
    import h5py
    with h5py.File(filepath, 'a') as f:
        metadata_group = f.create_group('metadata') if 'metadata' not in f else f['metadata']
        start = run.metadata['start']

        for key, value in start.items():
            # Convert to string to avoid type issues
            metadata_group.attrs[key] = str(value)

    print(f"✅ Exported to HDF5: {filepath}")
    return filepath


def export_metadata(run, filename):
    """
    Export metadata to JSON file.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    filename : str or Path
        Output JSON filename

    Examples
    --------
    >>> export_metadata(run, 'data/my_scan_metadata.json')
    """
    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w') as f:
        json.dump(run.metadata['start'], f, indent=2, default=str)

    print(f"✅ Exported metadata to: {filepath}")
    return filepath


def export_all_documents(run, output_dir='data/documents'):
    """
    Export all documents (start, descriptor, event, stop) to JSON files.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    output_dir : str or Path
        Output directory

    Returns
    -------
    Path
        Path to output directory

    Examples
    --------
    >>> export_all_documents(run, 'data/run_12345')
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    uid = run.metadata['start']['uid'][:8]

    # Export each document type
    for name, doc in run.documents():
        filename = output_path / f"{uid}_{name}.json"

        with open(filename, 'w') as f:
            json.dump({name: doc}, f, indent=2, default=str)

        print(f"   Saved {name} document: {filename.name}")

    print(f"✅ Exported all documents to: {output_path}")
    return output_path


def export_to_excel(run, filename):
    """
    Export run data to Excel file with multiple sheets.

    Creates sheets for data, metadata, and summary statistics.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    filename : str or Path
        Output Excel filename

    Examples
    --------
    >>> export_to_excel(run, 'data/my_scan.xlsx')
    """
    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    table = run.table()
    start = run.metadata['start']

    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # Data sheet
        table.to_excel(writer, sheet_name='Data', index=False)

        # Metadata sheet
        metadata_df = pd.DataFrame([start]).T
        metadata_df.columns = ['Value']
        metadata_df.to_excel(writer, sheet_name='Metadata')

        # Summary statistics sheet
        if table.select_dtypes(include=['number']).shape[1] > 0:
            stats = table.describe()
            stats.to_excel(writer, sheet_name='Statistics')

    print(f"✅ Exported to Excel: {filepath}")
    return filepath


def export_for_analysis(run, output_dir='data/analysis', formats=['csv', 'hdf5']):
    """
    Export run data in multiple formats for analysis.

    Convenience function that exports to multiple formats at once.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    output_dir : str or Path
        Output directory
    formats : list of str
        Formats to export ('csv', 'hdf5', 'excel', 'json')

    Returns
    -------
    dict
        Dictionary of format: filepath pairs

    Examples
    --------
    >>> export_for_analysis(run, 'data/exp_001',
    ...                     formats=['csv', 'hdf5', 'excel'])
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    uid = run.metadata['start']['uid'][:8]
    scan_id = run.metadata['start']['scan_id']
    base_name = f"run_{scan_id}_{uid}"

    exported = {}

    if 'csv' in formats:
        csv_file = output_path / f"{base_name}.csv"
        export_to_csv(run, csv_file)
        exported['csv'] = csv_file

    if 'hdf5' in formats:
        h5_file = output_path / f"{base_name}.h5"
        export_to_hdf5(run, h5_file)
        exported['hdf5'] = h5_file

    if 'excel' in formats:
        excel_file = output_path / f"{base_name}.xlsx"
        export_to_excel(run, excel_file)
        exported['excel'] = excel_file

    if 'json' in formats:
        json_file = output_path / f"{base_name}_metadata.json"
        export_metadata(run, json_file)
        exported['json'] = json_file

    print(f"\n✅ Exported run {scan_id} ({uid}) to: {output_path}")
    return exported


def batch_export(runs, output_dir='data/batch_export', formats=['csv']):
    """
    Export multiple runs at once.

    Parameters
    ----------
    runs : list of BlueskyRun
        List of run objects from databroker
    output_dir : str or Path
        Output directory
    formats : list of str
        Formats to export

    Examples
    --------
    >>> from databroker import Broker
    >>> db = Broker.named('temp')
    >>> recent_runs = list(db.search(since='2025-01-08'))
    >>> batch_export(recent_runs, 'data/batch', formats=['csv', 'hdf5'])
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Batch exporting {len(runs)} runs...")

    for i, run in enumerate(runs, 1):
        scan_id = run.metadata['start']['scan_id']
        uid = run.metadata['start']['uid'][:8]

        print(f"\n[{i}/{len(runs)}] Run {scan_id} ({uid}):")

        run_dir = output_path / f"run_{scan_id}_{uid}"
        export_for_analysis(run, run_dir, formats=formats)

    print(f"\n✅ Batch export complete: {output_path}")
    return output_path
