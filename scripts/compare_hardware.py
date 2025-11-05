#!/usr/bin/env python3
"""
Compare hardware configurations across DTN nodes.

This script parses hardware survey files and creates pandas DataFrames
showing CPU, memory, and socket buffer configurations for each node side-by-side.

Parsed files:
- lscpu_*.txt: CPU specifications
- meminfo_*.txt: Memory configuration
- sysctl_*.txt: Socket buffer settings
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def parse_lscpu_file(lscpu_path: Path) -> Dict[str, str]:
    """Parse an lscpu output file and return a dictionary of CPU specs."""
    try:
        with open(lscpu_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return {}

    specs = {}

    # Parse each line in the format "Key:    Value"
    for line in content.strip().split('\n'):
        if ':' not in line:
            continue

        # Split on first colon
        parts = line.split(':', 1)
        if len(parts) != 2:
            continue

        key = parts[0].strip()
        value = parts[1].strip()

        specs[key] = value

    return specs


def parse_meminfo_file(meminfo_path: Path) -> Dict[str, str]:
    """Parse a meminfo output file and return key memory specs."""
    try:
        with open(meminfo_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return {}

    specs = {}

    # Parse free -h output (first few lines)
    lines = content.strip().split('\n')
    for i, line in enumerate(lines):
        if line.startswith('Mem:'):
            parts = line.split()
            if len(parts) >= 2:
                specs['Total Memory'] = parts[1]
            break

    # Parse /proc/meminfo for detailed info
    for line in lines:
        if ':' not in line:
            continue

        # Look for specific memory parameters
        if line.startswith('MemTotal:'):
            parts = line.split(':')
            if len(parts) == 2:
                specs['MemTotal'] = parts[1].strip()
        elif line.startswith('MemAvailable:'):
            parts = line.split(':')
            if len(parts) == 2:
                specs['MemAvailable'] = parts[1].strip()
        elif line.startswith('HugePages_Total:'):
            parts = line.split(':')
            if len(parts) == 2:
                specs['HugePages_Total'] = parts[1].strip()
        elif line.startswith('Hugepagesize:'):
            parts = line.split(':')
            if len(parts) == 2:
                specs['Hugepagesize'] = parts[1].strip()

    return specs


def parse_sysctl_file(sysctl_path: Path) -> Dict[str, str]:
    """Parse a sysctl output file and return socket buffer settings."""
    try:
        with open(sysctl_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return {}

    specs = {}

    # Parse sysctl output
    for line in content.strip().split('\n'):
        if '=' not in line:
            continue

        # Split on equals sign
        parts = line.split('=', 1)
        if len(parts) != 2:
            continue

        key = parts[0].strip()
        value = parts[1].strip()

        # Clean up the key (remove 'net.core.' and 'net.ipv4.' prefixes for display)
        display_key = key.replace('net.core.', '').replace('net.ipv4.', '')
        specs[display_key] = value

    return specs


def create_comparison_dataframe(log_dir: Path) -> Optional[pd.DataFrame]:
    """Create a DataFrame comparing lscpu output across all nodes."""
    if not PANDAS_AVAILABLE:
        return None

    # Find all lscpu files
    lscpu_files = sorted(log_dir.glob('lscpu_*.txt'))
    if not lscpu_files:
        return None

    # Parse all lscpu files
    all_specs = {}
    for lscpu_file in lscpu_files:
        # Extract hostname from filename (e.g., "wash" from "lscpu_wash.txt")
        hostname = lscpu_file.stem.replace('lscpu_', '')
        all_specs[hostname] = parse_lscpu_file(lscpu_file)

    if not all_specs:
        return None

    # Get all unique keys across all nodes
    all_keys = set()
    for specs in all_specs.values():
        all_keys.update(specs.keys())

    all_keys = sorted(all_keys)

    # Build DataFrame with nodes as columns
    data_dict = {}
    for hostname, specs in all_specs.items():
        column_data = {}
        for key in all_keys:
            column_data[key] = specs.get(key, 'N/A')
        data_dict[hostname] = column_data

    df = pd.DataFrame(data_dict)

    # Add DIFFERS column to mark rows where values differ
    df['DIFFERS'] = df.apply(lambda row: '***' if len(set(row.dropna())) > 1 else '', axis=1)

    return df


def create_memory_comparison_dataframe(log_dir: Path) -> Optional[pd.DataFrame]:
    """Create a DataFrame comparing memory configuration across all nodes."""
    if not PANDAS_AVAILABLE:
        return None

    # Find all meminfo files
    meminfo_files = sorted(log_dir.glob('meminfo_*.txt'))
    if not meminfo_files:
        return None

    # Parse all meminfo files
    all_specs = {}
    for meminfo_file in meminfo_files:
        hostname = meminfo_file.stem.replace('meminfo_', '')
        all_specs[hostname] = parse_meminfo_file(meminfo_file)

    if not all_specs:
        return None

    # Get all unique keys
    all_keys = set()
    for specs in all_specs.values():
        all_keys.update(specs.keys())

    all_keys = sorted(all_keys)

    # Build DataFrame
    data_dict = {}
    for hostname, specs in all_specs.items():
        column_data = {}
        for key in all_keys:
            column_data[key] = specs.get(key, 'N/A')
        data_dict[hostname] = column_data

    df = pd.DataFrame(data_dict)

    # Add DIFFERS column
    df['DIFFERS'] = df.apply(lambda row: '***' if len(set(row.dropna())) > 1 else '', axis=1)

    return df


def create_sysctl_comparison_dataframe(log_dir: Path) -> Optional[pd.DataFrame]:
    """Create a DataFrame comparing socket buffer settings across all nodes."""
    if not PANDAS_AVAILABLE:
        return None

    # Find all sysctl files
    sysctl_files = sorted(log_dir.glob('sysctl_*.txt'))
    if not sysctl_files:
        return None

    # Parse all sysctl files
    all_specs = {}
    for sysctl_file in sysctl_files:
        hostname = sysctl_file.stem.replace('sysctl_', '')
        all_specs[hostname] = parse_sysctl_file(sysctl_file)

    if not all_specs:
        return None

    # Get all unique keys
    all_keys = set()
    for specs in all_specs.values():
        all_keys.update(specs.keys())

    all_keys = sorted(all_keys)

    # Build DataFrame
    data_dict = {}
    for hostname, specs in all_specs.items():
        column_data = {}
        for key in all_keys:
            column_data[key] = specs.get(key, 'N/A')
        data_dict[hostname] = column_data

    df = pd.DataFrame(data_dict)

    # Add DIFFERS column
    df['DIFFERS'] = df.apply(lambda row: '***' if len(set(row.dropna())) > 1 else '', axis=1)

    return df


def print_separator(char='=', width=160):
    """Print a separator line."""
    print(char * width)


def print_dataframe_pages(df: pd.DataFrame, max_width: int = 160):
    """Print DataFrame in multiple pages with fixed-width columns."""
    # Calculate available width for data columns
    # Reserve space for index column (field names) - use 35 chars
    index_width = 35
    differs_width = 8  # Width for DIFFERS column

    # Available width for host columns
    available_width = max_width - index_width - differs_width - 3  # 3 for spacing

    # Get all columns except DIFFERS
    host_columns = [col for col in df.columns if col != 'DIFFERS']

    # Calculate column width (equal width for all hosts)
    # Add 2 for spacing between columns
    num_hosts = len(host_columns)
    col_width = min(25, (available_width - (num_hosts - 1) * 2) // num_hosts)

    # Determine how many hosts can fit per page
    hosts_per_page = max(1, (available_width + 2) // (col_width + 2))

    # Split hosts into pages
    pages = []
    for i in range(0, len(host_columns), hosts_per_page):
        page_hosts = host_columns[i:i + hosts_per_page]
        pages.append(page_hosts)

    # Print each page
    for page_num, page_hosts in enumerate(pages, 1):
        if page_num > 1:
            print()

        print_separator('=', max_width)
        page_title = f"HARDWARE COMPARISON - Page {page_num}/{len(pages)}"
        print(f"{page_title:^{max_width}}")
        print_separator('=', max_width)

        # Create page DataFrame with only these hosts plus DIFFERS
        page_df = df[page_hosts + ['DIFFERS']].copy()

        # Configure pandas for fixed-width output
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', max_width)
        pd.set_option('display.max_colwidth', col_width)
        pd.set_option('display.colheader_justify', 'left')

        # Truncate long values to fit column width
        for col in page_hosts:
            page_df[col] = page_df[col].apply(
                lambda x: (x[:col_width-3] + '...') if isinstance(x, str) and len(x) > col_width else x
            )

        print(page_df.to_string(max_colwidth=col_width))
        print()
        print_separator('=', max_width)


def print_differences_pages(df: pd.DataFrame, max_width: int = 160):
    """Print only rows with differences in multiple pages."""
    diff_rows = df[df['DIFFERS'] == '***']

    if diff_rows.empty:
        print()
        print("All nodes have identical CPU configurations!")
        print()
        print_separator('=', max_width)
        return

    # Calculate available width for data columns
    index_width = 35
    differs_width = 8
    available_width = max_width - index_width - differs_width - 3

    # Get all columns except DIFFERS
    host_columns = [col for col in diff_rows.columns if col != 'DIFFERS']

    # Calculate column width
    num_hosts = len(host_columns)
    col_width = min(25, (available_width - (num_hosts - 1) * 2) // num_hosts)

    # Determine hosts per page
    hosts_per_page = max(1, (available_width + 2) // (col_width + 2))

    # Split hosts into pages
    pages = []
    for i in range(0, len(host_columns), hosts_per_page):
        page_hosts = host_columns[i:i + hosts_per_page]
        pages.append(page_hosts)

    # Print each page
    for page_num, page_hosts in enumerate(pages, 1):
        print()
        print_separator('=', max_width)
        page_title = f"DIFFERENCES FOUND (*** marked) - Page {page_num}/{len(pages)}"
        print(f"{page_title:^{max_width}}")
        print_separator('=', max_width)

        # Create page DataFrame
        page_df = diff_rows[page_hosts + ['DIFFERS']].copy()

        # Configure pandas
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', max_width)
        pd.set_option('display.max_colwidth', col_width)
        pd.set_option('display.colheader_justify', 'left')

        # Truncate long values
        for col in page_hosts:
            page_df[col] = page_df[col].apply(
                lambda x: (x[:col_width-3] + '...') if isinstance(x, str) and len(x) > col_width else x
            )

        print(page_df.to_string(max_colwidth=col_width))
        print()
        print_separator('=', max_width)


def save_dataframe_to_csv(df: pd.DataFrame, output_path: Path, name: str):
    """Save a DataFrame to CSV file."""
    try:
        df.to_csv(output_path)
        print(f"Saved {name} to: {output_path}")
    except Exception as e:
        print(f"Error saving {name} to CSV: {e}")


def main():
    """Main function to compare hardware across all nodes."""
    # Determine the log directory
    if len(sys.argv) > 1:
        log_dir = Path(sys.argv[1])
    else:
        log_dir = Path('run_output')

    if not log_dir.exists():
        print(f"Error: Directory '{log_dir}' does not exist")
        sys.exit(1)

    # Find all hardware survey files
    lscpu_files = sorted(log_dir.glob('lscpu_*.txt'))
    meminfo_files = sorted(log_dir.glob('meminfo_*.txt'))
    sysctl_files = sorted(log_dir.glob('sysctl_*.txt'))

    if not lscpu_files and not meminfo_files and not sysctl_files:
        print(f"No hardware survey files found in {log_dir}")
        sys.exit(1)

    max_width = 160

    print()
    print_separator('=', max_width)
    print(f"{'DTN HARDWARE COMPARISON':^{max_width}}")
    print_separator('=', max_width)
    print(f"Log Directory: {log_dir.resolve()}")
    print(f"CPU Files Found: {len(lscpu_files)}")
    print(f"Memory Files Found: {len(meminfo_files)}")
    print(f"Sysctl Files Found: {len(sysctl_files)}")
    print()
    print_separator('=', max_width)

    if not PANDAS_AVAILABLE:
        print("Error: pandas is required for hardware comparison")
        print("      pip install pandas")
        print()
        print_separator('=', max_width)
        sys.exit(1)

    # Track CSV files that were created
    csv_files = []

    # CPU Comparison
    if lscpu_files:
        df = create_comparison_dataframe(log_dir)
        if df is not None:
            print()
            print_separator('=', max_width)
            print(f"{'CPU CONFIGURATION':^{max_width}}")
            print_separator('=', max_width)
            print()
            print_dataframe_pages(df, max_width)
            print_differences_pages(df, max_width)

            # Save to CSV
            csv_path = log_dir / 'hardware_comparison_cpu.csv'
            save_dataframe_to_csv(df, csv_path, 'CPU comparison')
            csv_files.append(csv_path)

    # Memory Comparison
    if meminfo_files:
        mem_df = create_memory_comparison_dataframe(log_dir)
        if mem_df is not None:
            print()
            print_separator('=', max_width)
            print(f"{'MEMORY CONFIGURATION':^{max_width}}")
            print_separator('=', max_width)
            print()
            print_dataframe_pages(mem_df, max_width)
            print_differences_pages(mem_df, max_width)

            # Save to CSV
            csv_path = log_dir / 'hardware_comparison_memory.csv'
            save_dataframe_to_csv(mem_df, csv_path, 'Memory comparison')
            csv_files.append(csv_path)

    # Socket Buffer Comparison
    if sysctl_files:
        sysctl_df = create_sysctl_comparison_dataframe(log_dir)
        if sysctl_df is not None:
            print()
            print_separator('=', max_width)
            print(f"{'SOCKET BUFFER CONFIGURATION':^{max_width}}")
            print_separator('=', max_width)
            print()
            print_dataframe_pages(sysctl_df, max_width)
            print_differences_pages(sysctl_df, max_width)

            # Save to CSV
            csv_path = log_dir / 'hardware_comparison_sysctl.csv'
            save_dataframe_to_csv(sysctl_df, csv_path, 'Sysctl comparison')
            csv_files.append(csv_path)

    # Print summary of CSV files created
    if csv_files:
        print()
        print_separator('=', max_width)
        print(f"{'CSV FILES CREATED':^{max_width}}")
        print_separator('=', max_width)
        for csv_file in csv_files:
            print(f"  {csv_file}")
        print()
        print_separator('=', max_width)

    print()


if __name__ == '__main__':
    main()
