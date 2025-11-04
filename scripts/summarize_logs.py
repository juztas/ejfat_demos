#!/usr/bin/env python3
"""
Summarize EJFAT sender and receiver logs from run_output directory.

This script parses tx_* and rx_* log files to extract:
- Transmit and receive parameters
- Nodes that runs were conducted on
- Transmit statistics
- Receive statistics
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


def parse_tx_log(log_path: Path) -> Optional[Dict]:
    """Parse a transmitter log file and extract key information."""
    try:
        with open(log_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return None

    data = {
        'file': log_path.name,
        'type': 'transmitter',
        'run_id': None,
        'config_file': None,
        'hostname': None,
        'sender_ip': None,
        'ip_version': None,
        'tx_rate': None,
        'tx_length': None,
        'frames': None,
        'send_sockets': None,
        'data_id': None,
        'use_control_plane': None,
        'mtu': None,
        'frames_sent': None,
        'errors': None,
        'elapsed_usecs': None,
        'throughput_gbps': None,
        'goodput_gbps': None,
    }

    # Extract configuration section
    run_id_match = re.search(r'Run ID:\s*(.+)', content)
    if run_id_match:
        data['run_id'] = run_id_match.group(1).strip()

    config_match = re.search(r'Config file:\s*(.+)', content)
    if config_match:
        data['config_file'] = config_match.group(1).strip()

    hostname_match = re.search(r'Hostname:\s*(.+)', content)
    if hostname_match:
        data['hostname'] = hostname_match.group(1).strip()

    sender_ip_match = re.search(r'Sender IP:\s*(.+)', content)
    if sender_ip_match:
        data['sender_ip'] = sender_ip_match.group(1).strip()

    ip_version_match = re.search(r'IP Version:\s*(.+)', content)
    if ip_version_match:
        data['ip_version'] = ip_version_match.group(1).strip()

    tx_rate_match = re.search(r'TX Rate:\s*(.+)', content)
    if tx_rate_match:
        data['tx_rate'] = tx_rate_match.group(1).strip()

    tx_length_match = re.search(r'TX Length:\s*(.+)', content)
    if tx_length_match:
        data['tx_length'] = tx_length_match.group(1).strip()

    frames_match = re.search(r'Frames:\s*(\d+)', content)
    if frames_match:
        data['frames'] = int(frames_match.group(1))

    sockets_match = re.search(r'Send Sockets:\s*(\d+)', content)
    if sockets_match:
        data['send_sockets'] = int(sockets_match.group(1))

    data_id_match = re.search(r'Data ID:\s*(\d+)', content)
    if data_id_match:
        data['data_id'] = int(data_id_match.group(1))

    cp_match = re.search(r'Use Control Plane:\s*(.+)', content)
    if cp_match:
        data['use_control_plane'] = cp_match.group(1).strip()

    mtu_match = re.search(r'MTU:\s*(\d+)', content)
    if mtu_match:
        data['mtu'] = int(mtu_match.group(1))

    # Extract statistics
    frames_sent_match = re.search(r'Completed,\s*([\d,]+)\s*frames sent,\s*(\d+)\s*errors', content)
    if frames_sent_match:
        data['frames_sent'] = int(frames_sent_match.group(1).replace(',', ''))
        data['errors'] = int(frames_sent_match.group(2))

    elapsed_match = re.search(r'Elapsed usecs:\s*([\d,]+)\s*microseconds', content)
    if elapsed_match:
        data['elapsed_usecs'] = int(elapsed_match.group(1).replace(',', ''))

    throughput_match = re.search(r'Estimated effective throughput \(Gbps\):\s*([\d.]+)', content)
    if throughput_match:
        data['throughput_gbps'] = float(throughput_match.group(1))

    goodput_match = re.search(r'Estimated goodput \(Gbps\):\s*([\d.]+)', content)
    if goodput_match:
        data['goodput_gbps'] = float(goodput_match.group(1))

    return data


def parse_rx_log(log_path: Path) -> Optional[Dict]:
    """Parse a receiver log file and extract key information."""
    try:
        with open(log_path, 'r') as f:
            content = f.read()
    except Exception as e:
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


def print_separator(char='=', width=80):
    """Print a separator line."""
    print(char * width)


def print_tx_summary(tx_data: Dict):
    """Print transmitter summary."""
    print(f"\n{'TRANSMITTER':^80}")
    print_separator()
    print(f"Log File:            {tx_data['file']}")

    if tx_data['run_id']:
        print(f"Run ID:              {tx_data['run_id']}")

    if tx_data['config_file']:
        print(f"Config File:         {tx_data['config_file']}")

    if tx_data['hostname']:
        print(f"Hostname:            {tx_data['hostname']}")

    print()
    print("Configuration:")
    print_separator('-')
    if tx_data['sender_ip']:
        print(f"  Sender IP:         {tx_data['sender_ip']}")
    if tx_data['ip_version']:
        print(f"  IP Version:        {tx_data['ip_version']}")
    if tx_data['tx_rate']:
        print(f"  TX Rate:           {tx_data['tx_rate']}")
    if tx_data['tx_length']:
        print(f"  TX Length:         {tx_data['tx_length']}")
    if tx_data['frames'] is not None:
        print(f"  Frames:            {tx_data['frames']:,}")
    if tx_data['send_sockets'] is not None:
        print(f"  Send Sockets:      {tx_data['send_sockets']}")
    if tx_data['data_id'] is not None:
        print(f"  Data ID:           {tx_data['data_id']}")
    if tx_data['use_control_plane']:
        print(f"  Control Plane:     {tx_data['use_control_plane']}")
    if tx_data['mtu'] is not None:
        print(f"  MTU:               {tx_data['mtu']}")

    print()
    print("Statistics:")
    print_separator('-')
    if tx_data['frames_sent'] is not None:
        print(f"  Frames Sent:       {tx_data['frames_sent']:,}")
    if tx_data['errors'] is not None:
        print(f"  Errors:            {tx_data['errors']}")
    if tx_data['elapsed_usecs'] is not None:
        elapsed_sec = tx_data['elapsed_usecs'] / 1_000_000
        print(f"  Elapsed Time:      {elapsed_sec:.3f} sec ({tx_data['elapsed_usecs']:,} μs)")
    if tx_data['throughput_gbps'] is not None:
        print(f"  Throughput:        {tx_data['throughput_gbps']:.4f} Gbps")
    if tx_data['goodput_gbps'] is not None:
        print(f"  Goodput:           {tx_data['goodput_gbps']:.4f} Gbps")


def print_rx_summary(rx_data: Dict):
    """Print receiver summary."""
    print(f"\n{'RECEIVER':^80}")
    print_separator()
    print(f"Log File:            {rx_data['file']}")

    if rx_data['run_id']:
        print(f"Run ID:              {rx_data['run_id']}")

    if rx_data['config_file']:
        print(f"Config File:         {rx_data['config_file']}")

    if rx_data['hostname']:
        print(f"Hostname:            {rx_data['hostname']}")

    print()
    print("Configuration:")
    print_separator('-')
    if rx_data['receiver_ip']:
        print(f"  Receiver IP:       {rx_data['receiver_ip']}")
    if rx_data['ip_version']:
        print(f"  IP Version:        {rx_data['ip_version']}")
    if rx_data['interface']:
        print(f"  Interface:         {rx_data['interface']}")
    if rx_data['data_port'] is not None:
        print(f"  Data Port:         {rx_data['data_port']}")
    if rx_data['monitor_ports']:
        print(f"  Monitor Ports:     {rx_data['monitor_ports']}")
    if rx_data['rx_duration']:
        print(f"  RX Duration:       {rx_data['rx_duration']}")
    if rx_data['rx_buffer_size']:
        print(f"  RX Buffer Size:    {rx_data['rx_buffer_size']}")
    if rx_data['rx_timeout']:
        print(f"  RX Timeout:        {rx_data['rx_timeout']}")
    if rx_data['rx_cores'] is not None:
        print(f"  RX Cores:          {rx_data['rx_cores']}")
    if rx_data['rx_dequeue'] is not None:
        print(f"  RX Dequeue:        {rx_data['rx_dequeue']}")
    if rx_data['monitor_interval']:
        print(f"  Monitor Interval:  {rx_data['monitor_interval']}")
    if rx_data['use_control_plane']:
        print(f"  Control Plane:     {rx_data['use_control_plane']}")
    if rx_data['rx_index'] is not None:
        print(f"  RX Index:          {rx_data['rx_index']}")

    print()
    print("Statistics:")
    print_separator('-')
    if rx_data['events_received'] is not None:
        print(f"  Events Received:   {rx_data['events_received']:,}")
    if rx_data['events_mangled'] is not None:
        print(f"  Events Mangled:    {rx_data['events_mangled']:,}")
    if rx_data['events_lost_reassembly'] is not None:
        print(f"  Events Lost (Reassembly): {rx_data['events_lost_reassembly']:,}")
    if rx_data['events_lost_enqueue'] is not None:
        print(f"  Events Lost (Enqueue):    {rx_data['events_lost_enqueue']:,}")
    if rx_data['data_errors'] is not None:
        print(f"  Data Errors:       {rx_data['data_errors']:,}")
    if rx_data['grpc_errors'] is not None:
        print(f"  gRPC Errors:       {rx_data['grpc_errors']:,}")

    if rx_data['port_stats']:
        print(f"\n  Port Statistics:")
        print(f"    Port {rx_data['port_stats']['port']}: {rx_data['port_stats']['received']:,} packets")

    if rx_data['total_packets'] is not None:
        print(f"  Total Packets:     {rx_data['total_packets']:,}")


def create_tx_dataframe(tx_files: List[Path]) -> Optional[pd.DataFrame]:
    """Create a DataFrame from transmitter log data."""
    if not PANDAS_AVAILABLE or not tx_files:
        return None

    data_dict = {}

    for tx_file in tx_files:
        tx_data = parse_tx_log(tx_file)
        if not tx_data:
            continue

        col_name = tx_data['file']

        # Build column data
        column_data = {
            'Run ID': tx_data.get('run_id', 'N/A'),
            'Hostname': tx_data.get('hostname', 'N/A'),
            'Sender IP': tx_data.get('sender_ip', 'N/A'),
            'IP Version': tx_data.get('ip_version', 'N/A'),
            'TX Rate': tx_data.get('tx_rate', 'N/A'),
            'TX Length': tx_data.get('tx_length', 'N/A'),
            'Frames (target)': f"{tx_data['frames']:,}" if tx_data.get('frames') is not None else 'N/A',
            'Send Sockets': tx_data.get('send_sockets', 'N/A'),
            'Data ID': tx_data.get('data_id', 'N/A'),
            'Control Plane': tx_data.get('use_control_plane', 'N/A'),
            'MTU': tx_data.get('mtu', 'N/A'),
            'Frames Sent': f"{tx_data['frames_sent']:,}" if tx_data.get('frames_sent') is not None else 'N/A',
            'Errors': tx_data.get('errors', 'N/A'),
            'Elapsed Time (sec)': f"{tx_data['elapsed_usecs']/1_000_000:.3f}" if tx_data.get('elapsed_usecs') is not None else 'N/A',
            'Throughput (Gbps)': f"{tx_data['throughput_gbps']:.4f}" if tx_data.get('throughput_gbps') is not None else 'N/A',
            'Goodput (Gbps)': f"{tx_data['goodput_gbps']:.4f}" if tx_data.get('goodput_gbps') is not None else 'N/A',
        }

        data_dict[col_name] = column_data

    if not data_dict:
        return None

    df = pd.DataFrame(data_dict)
    return df


def create_rx_dataframe(rx_files: List[Path]) -> Optional[pd.DataFrame]:
    """Create a DataFrame from receiver log data."""
    if not PANDAS_AVAILABLE or not rx_files:
        return None

    data_dict = {}

    # Track totals for summable fields
    totals = {
        'Events Received': 0,
        'Events Mangled': 0,
        'Events Lost (Reassembly)': 0,
        'Events Lost (Enqueue)': 0,
        'Data Errors': 0,
        'gRPC Errors': 0,
        'Total Packets': 0,
    }

    # Track which fields have valid data (not all N/A)
    has_data = {key: False for key in totals.keys()}

    for rx_file in rx_files:
        rx_data = parse_rx_log(rx_file)
        if not rx_data:
            continue

        col_name = rx_data['file']

        # Build column data
        column_data = {
            'Run ID': rx_data.get('run_id', 'N/A'),
            'Hostname': rx_data.get('hostname', 'N/A'),
            'Receiver IP': rx_data.get('receiver_ip', 'N/A'),
            'IP Version': rx_data.get('ip_version', 'N/A'),
            'Interface': rx_data.get('interface', 'N/A'),
            'Data Port': rx_data.get('data_port', 'N/A'),
            'Monitor Ports': rx_data.get('monitor_ports', 'N/A'),
            'RX Duration': rx_data.get('rx_duration', 'N/A'),
            'RX Buffer Size': rx_data.get('rx_buffer_size', 'N/A'),
            'RX Timeout': rx_data.get('rx_timeout', 'N/A'),
            'RX Cores': rx_data.get('rx_cores', 'N/A'),
            'RX Dequeue': rx_data.get('rx_dequeue', 'N/A'),
            'Monitor Interval': rx_data.get('monitor_interval', 'N/A'),
            'Control Plane': rx_data.get('use_control_plane', 'N/A'),
            'RX Index': rx_data.get('rx_index', 'N/A'),
            'Events Received': f"{rx_data['events_received']:,}" if rx_data.get('events_received') is not None else 'N/A',
            'Events Mangled': f"{rx_data['events_mangled']:,}" if rx_data.get('events_mangled') is not None else 'N/A',
            'Events Lost (Reassembly)': f"{rx_data['events_lost_reassembly']:,}" if rx_data.get('events_lost_reassembly') is not None else 'N/A',
            'Events Lost (Enqueue)': f"{rx_data['events_lost_enqueue']:,}" if rx_data.get('events_lost_enqueue') is not None else 'N/A',
            'Data Errors': f"{rx_data['data_errors']:,}" if rx_data.get('data_errors') is not None else 'N/A',
            'gRPC Errors': f"{rx_data['grpc_errors']:,}" if rx_data.get('grpc_errors') is not None else 'N/A',
            'Total Packets': f"{rx_data['total_packets']:,}" if rx_data.get('total_packets') is not None else 'N/A',
        }

        # Accumulate totals
        if rx_data.get('events_received') is not None:
            totals['Events Received'] += rx_data['events_received']
            has_data['Events Received'] = True
        if rx_data.get('events_mangled') is not None:
            totals['Events Mangled'] += rx_data['events_mangled']
            has_data['Events Mangled'] = True
        if rx_data.get('events_lost_reassembly') is not None:
            totals['Events Lost (Reassembly)'] += rx_data['events_lost_reassembly']
            has_data['Events Lost (Reassembly)'] = True
        if rx_data.get('events_lost_enqueue') is not None:
            totals['Events Lost (Enqueue)'] += rx_data['events_lost_enqueue']
            has_data['Events Lost (Enqueue)'] = True
        if rx_data.get('data_errors') is not None:
            totals['Data Errors'] += rx_data['data_errors']
            has_data['Data Errors'] = True
        if rx_data.get('grpc_errors') is not None:
            totals['gRPC Errors'] += rx_data['grpc_errors']
            has_data['gRPC Errors'] = True
        if rx_data.get('total_packets') is not None:
            totals['Total Packets'] += rx_data['total_packets']
            has_data['Total Packets'] = True

        data_dict[col_name] = column_data

    if not data_dict:
        return None

    # Add TOTAL column
    total_column = {
        'Run ID': '',
        'Hostname': '',
        'Receiver IP': '',
        'IP Version': '',
        'Interface': '',
        'Data Port': '',
        'Monitor Ports': '',
        'RX Duration': '',
        'RX Buffer Size': '',
        'RX Timeout': '',
        'RX Cores': '',
        'RX Dequeue': '',
        'Monitor Interval': '',
        'Control Plane': '',
        'RX Index': '',
        'Events Received': f"{totals['Events Received']:,}" if has_data['Events Received'] else 'N/A',
        'Events Mangled': f"{totals['Events Mangled']:,}" if has_data['Events Mangled'] else 'N/A',
        'Events Lost (Reassembly)': f"{totals['Events Lost (Reassembly)']:,}" if has_data['Events Lost (Reassembly)'] else 'N/A',
        'Events Lost (Enqueue)': f"{totals['Events Lost (Enqueue)']:,}" if has_data['Events Lost (Enqueue)'] else 'N/A',
        'Data Errors': f"{totals['Data Errors']:,}" if has_data['Data Errors'] else 'N/A',
        'gRPC Errors': f"{totals['gRPC Errors']:,}" if has_data['gRPC Errors'] else 'N/A',
        'Total Packets': f"{totals['Total Packets']:,}" if has_data['Total Packets'] else 'N/A',
    }

    data_dict['TOTAL'] = total_column

    df = pd.DataFrame(data_dict)
    return df


def main():
    """Main function to summarize all logs."""
    # Determine the log directory
    if len(sys.argv) > 1:
        log_dir = Path(sys.argv[1])
    else:
        log_dir = Path('run_output')

    if not log_dir.exists():
        print(f"Error: Directory '{log_dir}' does not exist")
        sys.exit(1)

    # Find all tx and rx log files
    tx_files = sorted(log_dir.glob('tx_*.log'))
    rx_files = sorted(log_dir.glob('rx_*.log'))

    if not tx_files and not rx_files:
        print(f"No tx_*.log or rx_*.log files found in {log_dir}")
        sys.exit(1)

    print()
    print_separator('=', 80)
    print(f"{'EJFAT LOG SUMMARY':^80}")
    print_separator('=', 80)
    print(f"Log Directory: {log_dir.resolve()}")
    print(f"Transmitter Logs Found: {len(tx_files)}")
    print(f"Receiver Logs Found: {len(rx_files)}")

    # Parse and display transmitter logs
    for tx_file in tx_files:
        tx_data = parse_tx_log(tx_file)
        if tx_data:
            print_tx_summary(tx_data)

    # Parse and display receiver logs
    for rx_file in rx_files:
        rx_data = parse_rx_log(rx_file)
        if rx_data:
            print_rx_summary(rx_data)

    # Print summary comparison
    if tx_files and rx_files:
        print()
        print_separator('=', 80)
        print(f"{'SUMMARY':^80}")
        print_separator('=', 80)

        # Calculate totals and collect run IDs
        total_tx_frames = 0
        total_tx_errors = 0
        run_ids = set()
        for tx_file in tx_files:
            tx_data = parse_tx_log(tx_file)
            if tx_data:
                if tx_data['frames_sent'] is not None:
                    total_tx_frames += tx_data['frames_sent']
                if tx_data['errors'] is not None:
                    total_tx_errors += tx_data['errors']
                if tx_data['run_id']:
                    run_ids.add(tx_data['run_id'])

        total_rx_events = 0
        total_rx_lost = 0
        total_rx_packets = 0
        rx_nodes = []
        for rx_file in rx_files:
            rx_data = parse_rx_log(rx_file)
            if rx_data:
                if rx_data['events_received'] is not None:
                    total_rx_events += rx_data['events_received']
                if rx_data['events_lost_reassembly'] is not None:
                    total_rx_lost += rx_data['events_lost_reassembly']
                if rx_data['total_packets'] is not None:
                    total_rx_packets += rx_data['total_packets']
                if rx_data['hostname']:
                    rx_nodes.append(rx_data['hostname'])
                if rx_data['run_id']:
                    run_ids.add(rx_data['run_id'])

        print()
        # Display Run ID if all logs have the same one
        if len(run_ids) == 1:
            print(f"Run ID: {list(run_ids)[0]}")
        elif len(run_ids) > 1:
            print(f"Run IDs: {', '.join(sorted(run_ids))} (multiple runs detected)")
        print()
        print(f"Receiver Nodes: {', '.join(rx_nodes) if rx_nodes else 'N/A'}")
        print()
        print(f"Total Frames Transmitted:  {total_tx_frames:,}")
        print(f"Total Transmit Errors:     {total_tx_errors:,}")
        print(f"Total Packets Received:    {total_rx_packets:,}")
        print(f"Total Events Received:     {total_rx_events:,}")
        print(f"Total Events Lost:         {total_rx_lost:,}")

        if total_tx_frames > 0:
            # Each frame generates multiple packets, so we compare events
            # The tx_frames count is the number of events sent
            if total_rx_events > 0:
                success_rate = (total_rx_events / total_tx_frames) * 100
                loss_rate = (total_rx_lost / total_tx_frames) * 100
                print(f"Event Success Rate:        {success_rate:.2f}%")
                print(f"Event Loss Rate:           {loss_rate:.2f}%")

    print()
    print_separator('=', 80)

    # Print DataFrames for side-by-side comparison
    if PANDAS_AVAILABLE:
        # Create transmitter comparison DataFrame
        if tx_files:
            print()
            print(f"{'TRANSMITTER COMPARISON':^80}")
            print_separator('=', 80)
            tx_df = create_tx_dataframe(tx_files)
            if tx_df is not None:
                # Configure pandas display options for better formatting
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                pd.set_option('display.max_colwidth', None)
                print(tx_df.to_string())
            else:
                print("No transmitter data available for comparison")
            print()
            print_separator('=', 80)

        # Create receiver comparison DataFrame
        if rx_files:
            print()
            print(f"{'RECEIVER COMPARISON':^80}")
            print_separator('=', 80)
            rx_df = create_rx_dataframe(rx_files)
            if rx_df is not None:
                # Configure pandas display options for better formatting
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                pd.set_option('display.max_colwidth', None)
                print(rx_df.to_string())
            else:
                print("No receiver data available for comparison")
            print()
            print_separator('=', 80)
    else:
        print()
        print("Note: Install pandas for side-by-side comparison tables")
        print("      pip install pandas")
        print()
        print_separator('=', 80)

    print()


if __name__ == '__main__':
    main()
