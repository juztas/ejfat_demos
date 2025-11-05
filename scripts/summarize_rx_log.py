#!/usr/bin/env python3
"""
Summarize a single EJFAT receiver log file.

This script parses an rx_*.log file and outputs a structured summary
that can be used for individual analysis or merged with other summaries
for multi-column comparison.

Usage:
    summarize_rx_log.py <rx_log_file> [--format json|text|csv]

Examples:
    summarize_rx_log.py rx_0.log
    summarize_rx_log.py rx_0.log --format json
    summarize_rx_log.py rx_0.log --format csv
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Optional


def parse_rx_log(log_path: Path) -> Optional[Dict]:
    """Parse a receiver log file and extract key information."""
    try:
        with open(log_path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {log_path}: {e}", file=sys.stderr)
        return None

    data = {
        'file': log_path.name,
        'type': 'receiver',
        'run_id': None,
        'config_file': None,
        'receiver_ip': None,
        'ip_version': None,
        'interface': None,
        'data_port': None,
        'monitor_ports': None,
        'rx_duration': None,
        'rx_buffer_size': None,
        'rx_timeout': None,
        'rx_cores': None,
        'rx_dequeue': None,
        'monitor_interval': None,
        'use_control_plane': None,
        'rx_index': None,
        'hostname': None,
        'events_received': None,
        'events_mangled': None,
        'events_lost_reassembly': None,
        'events_lost_enqueue': None,
        'data_errors': None,
        'grpc_errors': None,
        'port_stats': None,
        'total_packets': None,
    }

    # Extract configuration section
    run_id_match = re.search(r'Run ID:\s*(.+)', content)
    if run_id_match:
        data['run_id'] = run_id_match.group(1).strip()

    config_match = re.search(r'Config file:\s*(.+)', content)
    if config_match:
        data['config_file'] = config_match.group(1).strip()

    receiver_ip_match = re.search(r'Receiver IP:\s*(.+)', content)
    if receiver_ip_match:
        data['receiver_ip'] = receiver_ip_match.group(1).strip()

    ip_version_match = re.search(r'IP Version:\s*(.+)', content)
    if ip_version_match:
        data['ip_version'] = ip_version_match.group(1).strip()

    interface_match = re.search(r'Interface:\s*(.+)', content)
    if interface_match:
        data['interface'] = interface_match.group(1).strip()

    data_port_match = re.search(r'Data Port:\s*(\d+)', content)
    if data_port_match:
        data['data_port'] = int(data_port_match.group(1))

    monitor_ports_match = re.search(r'Monitor Ports:\s*(.+)', content)
    if monitor_ports_match:
        data['monitor_ports'] = monitor_ports_match.group(1).strip()

    rx_duration_match = re.search(r'RX Duration:\s*(.+)', content)
    if rx_duration_match:
        data['rx_duration'] = rx_duration_match.group(1).strip()

    rx_buffer_match = re.search(r'RX Buffer Size:\s*(.+)', content)
    if rx_buffer_match:
        data['rx_buffer_size'] = rx_buffer_match.group(1).strip()

    rx_timeout_match = re.search(r'RX Timeout:\s*(.+)', content)
    if rx_timeout_match:
        data['rx_timeout'] = rx_timeout_match.group(1).strip()

    rx_cores_match = re.search(r'RX Cores:\s*(\d+)', content)
    if rx_cores_match:
        data['rx_cores'] = int(rx_cores_match.group(1))

    rx_dequeue_match = re.search(r'RX Dequeue:\s*(\d+)', content)
    if rx_dequeue_match:
        data['rx_dequeue'] = int(rx_dequeue_match.group(1))

    monitor_interval_match = re.search(r'Monitor Interval:\s*(.+)', content)
    if monitor_interval_match:
        data['monitor_interval'] = monitor_interval_match.group(1).strip()

    cp_match = re.search(r'Use Control Plane:\s*(.+)', content)
    if cp_match:
        data['use_control_plane'] = cp_match.group(1).strip()

    rx_index_match = re.search(r'RX Index:\s*(\d+)', content)
    if rx_index_match:
        data['rx_index'] = int(rx_index_match.group(1))

    # Extract hostname from "Registering the worker" line
    hostname_match = re.search(r'Registering the worker\s+([^\s]+)\s+\.\.\.', content)
    if hostname_match:
        data['hostname'] = hostname_match.group(1).strip()

    # Extract final statistics (look for the last occurrence before "Stopping threads")
    # Stats are on separate lines, so we need to find the last Stats: block
    stopping_pos = content.find('Stopping threads')
    if stopping_pos != -1:
        # Get content before "Stopping threads"
        content_before_stop = content[:stopping_pos]
    else:
        content_before_stop = content

    # Find all "Stats:" markers
    stats_positions = [m.start() for m in re.finditer(r'^Stats:', content_before_stop, re.MULTILINE)]

    if stats_positions:
        # Get the last Stats block
        last_stats_pos = stats_positions[-1]
        # Extract a chunk after the last Stats: (next 500 chars should be enough)
        stats_chunk = content_before_stop[last_stats_pos:last_stats_pos+500]

        # Parse individual fields from the stats block
        events_received_match = re.search(r'Events Received:\s*([\d,]+)', stats_chunk)
        if events_received_match:
            data['events_received'] = int(events_received_match.group(1).replace(',', ''))

        events_mangled_match = re.search(r'Events Mangled:\s*([\d,]+)', stats_chunk)
        if events_mangled_match:
            data['events_mangled'] = int(events_mangled_match.group(1).replace(',', ''))

        events_lost_reassembly_match = re.search(r'Events Lost in reassembly:\s*([\d,]+)', stats_chunk)
        if events_lost_reassembly_match:
            data['events_lost_reassembly'] = int(events_lost_reassembly_match.group(1).replace(',', ''))

        events_lost_enqueue_match = re.search(r'Events Lost in enqueue:\s*([\d,]+)', stats_chunk)
        if events_lost_enqueue_match:
            data['events_lost_enqueue'] = int(events_lost_enqueue_match.group(1).replace(',', ''))

        data_errors_match = re.search(r'Data Errors:\s*([\d,]+)', stats_chunk)
        if data_errors_match:
            data['data_errors'] = int(data_errors_match.group(1).replace(',', ''))

        grpc_errors_match = re.search(r'gRPC Errors:\s*([\d,]+)', stats_chunk)
        if grpc_errors_match:
            data['grpc_errors'] = int(grpc_errors_match.group(1).replace(',', ''))

    # Extract port statistics
    port_stats_match = re.search(r'Port Stats:.*?Port:\s*([\d,]+)\s+Received:\s*([\d,]+)', content, re.DOTALL)
    if port_stats_match:
        data['port_stats'] = {
            'port': int(port_stats_match.group(1).replace(',', '')),
            'received': int(port_stats_match.group(2).replace(',', ''))
        }

    total_match = re.search(r'Total:\s*([\d,]+)', content)
    if total_match:
        data['total_packets'] = int(total_match.group(1).replace(',', ''))

    return data


def format_text(data: Dict) -> str:
    """Format receiver data as human-readable text."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"{'RECEIVER LOG SUMMARY':^80}")
    lines.append("=" * 80)
    lines.append(f"Log File:            {data['file']}")

    if data['run_id']:
        lines.append(f"Run ID:              {data['run_id']}")

    if data['config_file']:
        lines.append(f"Config File:         {data['config_file']}")

    if data['hostname']:
        lines.append(f"Hostname:            {data['hostname']}")

    lines.append("")
    lines.append("Configuration:")
    lines.append("-" * 80)

    if data['receiver_ip']:
        lines.append(f"  Receiver IP:       {data['receiver_ip']}")
    if data['ip_version']:
        lines.append(f"  IP Version:        {data['ip_version']}")
    if data['interface']:
        lines.append(f"  Interface:         {data['interface']}")
    if data['data_port'] is not None:
        lines.append(f"  Data Port:         {data['data_port']}")
    if data['monitor_ports']:
        lines.append(f"  Monitor Ports:     {data['monitor_ports']}")
    if data['rx_duration']:
        lines.append(f"  RX Duration:       {data['rx_duration']}")
    if data['rx_buffer_size']:
        lines.append(f"  RX Buffer Size:    {data['rx_buffer_size']}")
    if data['rx_timeout']:
        lines.append(f"  RX Timeout:        {data['rx_timeout']}")
    if data['rx_cores'] is not None:
        lines.append(f"  RX Cores:          {data['rx_cores']}")
    if data['rx_dequeue'] is not None:
        lines.append(f"  RX Dequeue:        {data['rx_dequeue']}")
    if data['monitor_interval']:
        lines.append(f"  Monitor Interval:  {data['monitor_interval']}")
    if data['use_control_plane']:
        lines.append(f"  Control Plane:     {data['use_control_plane']}")
    if data['rx_index'] is not None:
        lines.append(f"  RX Index:          {data['rx_index']}")

    lines.append("")
    lines.append("Statistics:")
    lines.append("-" * 80)

    if data['events_received'] is not None:
        lines.append(f"  Events Received:   {data['events_received']:,}")
    if data['events_mangled'] is not None:
        lines.append(f"  Events Mangled:    {data['events_mangled']:,}")
    if data['events_lost_reassembly'] is not None:
        lines.append(f"  Events Lost (Reassembly): {data['events_lost_reassembly']:,}")
    if data['events_lost_enqueue'] is not None:
        lines.append(f"  Events Lost (Enqueue):    {data['events_lost_enqueue']:,}")
    if data['data_errors'] is not None:
        lines.append(f"  Data Errors:       {data['data_errors']:,}")
    if data['grpc_errors'] is not None:
        lines.append(f"  gRPC Errors:       {data['grpc_errors']:,}")

    if data['port_stats']:
        lines.append(f"\n  Port Statistics:")
        lines.append(f"    Port {data['port_stats']['port']}: {data['port_stats']['received']:,} packets")

    if data['total_packets'] is not None:
        lines.append(f"  Total Packets:     {data['total_packets']:,}")

    # Calculate derived metrics
    if data['events_received'] is not None and data['events_received'] > 0:
        lines.append("")
        lines.append("Derived Metrics:")
        lines.append("-" * 80)

        if data['events_lost_reassembly'] is not None:
            loss_rate = (data['events_lost_reassembly'] / data['events_received']) * 100
            lines.append(f"  Loss Rate:         {loss_rate:.4f}%")

        if data['events_mangled'] is not None:
            mangle_rate = (data['events_mangled'] / data['events_received']) * 100
            lines.append(f"  Mangle Rate:       {mangle_rate:.4f}%")

        if data['data_errors'] is not None:
            error_rate = (data['data_errors'] / data['events_received']) * 100
            lines.append(f"  Error Rate:        {error_rate:.4f}%")

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)


def format_csv_header() -> str:
    """Return CSV header row."""
    fields = [
        'file', 'run_id', 'hostname', 'rx_index',
        'receiver_ip', 'ip_version', 'interface', 'data_port',
        'rx_duration', 'rx_cores', 'rx_dequeue',
        'events_received', 'events_mangled',
        'events_lost_reassembly', 'events_lost_enqueue',
        'data_errors', 'grpc_errors', 'total_packets',
        'loss_rate_pct', 'mangle_rate_pct', 'error_rate_pct'
    ]
    return ','.join(fields)


def format_csv(data: Dict) -> str:
    """Format receiver data as CSV row."""
    # Calculate derived metrics
    loss_rate = None
    mangle_rate = None
    error_rate = None

    if data['events_received'] is not None and data['events_received'] > 0:
        if data['events_lost_reassembly'] is not None:
            loss_rate = (data['events_lost_reassembly'] / data['events_received']) * 100
        if data['events_mangled'] is not None:
            mangle_rate = (data['events_mangled'] / data['events_received']) * 100
        if data['data_errors'] is not None:
            error_rate = (data['data_errors'] / data['events_received']) * 100

    values = [
        data.get('file', ''),
        data.get('run_id', ''),
        data.get('hostname', ''),
        str(data.get('rx_index', '')) if data.get('rx_index') is not None else '',
        data.get('receiver_ip', ''),
        data.get('ip_version', ''),
        data.get('interface', ''),
        str(data.get('data_port', '')) if data.get('data_port') is not None else '',
        data.get('rx_duration', ''),
        str(data.get('rx_cores', '')) if data.get('rx_cores') is not None else '',
        str(data.get('rx_dequeue', '')) if data.get('rx_dequeue') is not None else '',
        str(data.get('events_received', '')) if data.get('events_received') is not None else '',
        str(data.get('events_mangled', '')) if data.get('events_mangled') is not None else '',
        str(data.get('events_lost_reassembly', '')) if data.get('events_lost_reassembly') is not None else '',
        str(data.get('events_lost_enqueue', '')) if data.get('events_lost_enqueue') is not None else '',
        str(data.get('data_errors', '')) if data.get('data_errors') is not None else '',
        str(data.get('grpc_errors', '')) if data.get('grpc_errors') is not None else '',
        str(data.get('total_packets', '')) if data.get('total_packets') is not None else '',
        f"{loss_rate:.4f}" if loss_rate is not None else '',
        f"{mangle_rate:.4f}" if mangle_rate is not None else '',
        f"{error_rate:.4f}" if error_rate is not None else '',
    ]

    # Quote values that might contain commas
    quoted_values = [f'"{v}"' if ',' in v else v for v in values]
    return ','.join(quoted_values)


def main():
    """Main function to parse arguments and output summary."""
    parser = argparse.ArgumentParser(
        description='Summarize a single EJFAT receiver log file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  summarize_rx_log.py rx_0.log
  summarize_rx_log.py rx_0.log --format json
  summarize_rx_log.py rx_0.log --format csv
  summarize_rx_log.py rx_0.log --format csv --header
        """
    )

    parser.add_argument('log_file', type=str, help='Path to rx_*.log file')
    parser.add_argument('--format', '-f', choices=['text', 'json', 'csv'],
                       default='text', help='Output format (default: text)')
    parser.add_argument('--header', action='store_true',
                       help='Include CSV header (only for CSV format)')

    args = parser.parse_args()

    # Check if file exists
    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"Error: File not found: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    # Parse the log file
    data = parse_rx_log(log_path)

    if data is None:
        print(f"Error: Failed to parse log file: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    # Output in requested format
    if args.format == 'json':
        print(json.dumps(data, indent=2))
    elif args.format == 'csv':
        if args.header:
            print(format_csv_header())
        print(format_csv(data))
    else:  # text
        print(format_text(data))


if __name__ == '__main__':
    main()
