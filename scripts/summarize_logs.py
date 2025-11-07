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
from typing import Dict, List, Optional, Tuple
import pandas as pd
import configparser

PANDAS_AVAILABLE = True
CONFIGPARSER_AVAILABLE = True


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
        'thread_mode': None,
        'tx_cores': None,
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

    thread_mode_match = re.search(r'Thread Mode:\s*(.+)', content)
    if thread_mode_match:
        data['thread_mode'] = thread_mode_match.group(1).strip()

    tx_cores_match = re.search(r'TX Cores:\s*(.+)', content)
    if tx_cores_match:
        data['tx_cores'] = tx_cores_match.group(1).strip()

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
    if tx_data['thread_mode']:
        print(f"  Thread Mode:       {tx_data['thread_mode']}")
    if tx_data['tx_cores']:
        print(f"  TX Cores:          {tx_data['tx_cores']}")
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


def create_tx_dataframes_by_host(tx_files: List[Path]) -> Tuple[Dict[str, 'pd.DataFrame'], Dict]:
    """Create DataFrames from transmitter log data, grouped by hostname.

    Returns:
        tuple: (dict of {hostname: DataFrame}, grand_totals dict)
    """
    if not PANDAS_AVAILABLE or not tx_files:
        return {}, {}

    # Group files by hostname
    hosts_data = {}

    # Parse all files and group by hostname
    for tx_file in tx_files:
        tx_data = parse_tx_log(tx_file)
        if not tx_data:
            continue

        hostname = tx_data.get('hostname', 'Unknown')
        if hostname not in hosts_data:
            hosts_data[hostname] = []
        hosts_data[hostname].append(tx_data)

    # Create a DataFrame for each hostname
    host_dataframes = {}
    grand_totals = {
        'Frames Sent': 0,
        'Errors': 0,
        'Throughput (Gbps)': 0.0,
        'Goodput (Gbps)': 0.0,
    }
    has_grand_data = {key: False for key in grand_totals.keys()}

    for hostname, tx_data_list in sorted(hosts_data.items()):
        data_dict = {}

        # Track host totals for summable fields
        host_totals = {
            'Frames Sent': 0,
            'Errors': 0,
            'Throughput (Gbps)': 0.0,
            'Goodput (Gbps)': 0.0,
        }
        has_host_data = {key: False for key in host_totals.keys()}

        for tx_data in tx_data_list:
            col_name = tx_data['file']

            # Build column data
            column_data = {
                'Run ID': tx_data.get('run_id', 'N/A'),
                'Sender IP': tx_data.get('sender_ip', 'N/A'),
                'IP Version': tx_data.get('ip_version', 'N/A'),
                'TX Rate': tx_data.get('tx_rate', 'N/A'),
                'TX Length': tx_data.get('tx_length', 'N/A'),
                'Frames (target)': f"{tx_data['frames']:,}" if tx_data.get('frames') is not None else 'N/A',
                'Thread Mode': tx_data.get('thread_mode', 'N/A'),
                'TX Cores': tx_data.get('tx_cores', 'N/A'),
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

            # Accumulate host totals
            if tx_data.get('frames_sent') is not None:
                host_totals['Frames Sent'] += tx_data['frames_sent']
                has_host_data['Frames Sent'] = True
            if tx_data.get('errors') is not None:
                host_totals['Errors'] += tx_data['errors']
                has_host_data['Errors'] = True
            if tx_data.get('throughput_gbps') is not None:
                host_totals['Throughput (Gbps)'] += tx_data['throughput_gbps']
                has_host_data['Throughput (Gbps)'] = True
            if tx_data.get('goodput_gbps') is not None:
                host_totals['Goodput (Gbps)'] += tx_data['goodput_gbps']
                has_host_data['Goodput (Gbps)'] = True

            # Accumulate grand totals
            if tx_data.get('frames_sent') is not None:
                grand_totals['Frames Sent'] += tx_data['frames_sent']
                has_grand_data['Frames Sent'] = True
            if tx_data.get('errors') is not None:
                grand_totals['Errors'] += tx_data['errors']
                has_grand_data['Errors'] = True
            if tx_data.get('throughput_gbps') is not None:
                grand_totals['Throughput (Gbps)'] += tx_data['throughput_gbps']
                has_grand_data['Throughput (Gbps)'] = True
            if tx_data.get('goodput_gbps') is not None:
                grand_totals['Goodput (Gbps)'] += tx_data['goodput_gbps']
                has_grand_data['Goodput (Gbps)'] = True

            data_dict[col_name] = column_data

        # Add TOTAL column for this host
        if data_dict:
            total_column = {
                'Run ID': '',
                'Sender IP': '',
                'IP Version': '',
                'TX Rate': '',
                'TX Length': '',
                'Frames (target)': '',
                'Thread Mode': '',
                'TX Cores': '',
                'Send Sockets': '',
                'Data ID': '',
                'Control Plane': '',
                'MTU': '',
                'Frames Sent': f"{host_totals['Frames Sent']:,}" if has_host_data['Frames Sent'] else 'N/A',
                'Errors': host_totals['Errors'] if has_host_data['Errors'] else 'N/A',
                'Elapsed Time (sec)': '',
                'Throughput (Gbps)': f"{host_totals['Throughput (Gbps)']:.4f}" if has_host_data['Throughput (Gbps)'] else 'N/A',
                'Goodput (Gbps)': f"{host_totals['Goodput (Gbps)']:.4f}" if has_host_data['Goodput (Gbps)'] else 'N/A',
            }
            data_dict['TOTAL'] = total_column
            host_dataframes[hostname] = pd.DataFrame(data_dict)

    # Format grand totals
    formatted_grand_totals = {
        'Frames Sent': f"{grand_totals['Frames Sent']:,}" if has_grand_data['Frames Sent'] else 'N/A',
        'Errors': grand_totals['Errors'] if has_grand_data['Errors'] else 'N/A',
        'Throughput (Gbps)': f"{grand_totals['Throughput (Gbps)']:.4f}" if has_grand_data['Throughput (Gbps)'] else 'N/A',
        'Goodput (Gbps)': f"{grand_totals['Goodput (Gbps)']:.4f}" if has_grand_data['Goodput (Gbps)'] else 'N/A',
    }

    return host_dataframes, formatted_grand_totals


def create_rx_dataframes_by_host(rx_files: List[Path]) -> Tuple[Dict[str, 'pd.DataFrame'], Dict]:
    """Create DataFrames from receiver log data, grouped by hostname.

    Returns:
        tuple: (dict of {hostname: DataFrame}, grand_totals dict)
    """
    if not PANDAS_AVAILABLE or not rx_files:
        return {}, {}

    # Group files by hostname
    hosts_data = {}

    # Parse all files and group by hostname
    for rx_file in rx_files:
        rx_data = parse_rx_log(rx_file)
        if not rx_data:
            continue

        hostname = rx_data.get('hostname', 'Unknown')
        if hostname not in hosts_data:
            hosts_data[hostname] = []
        hosts_data[hostname].append(rx_data)

    # Create a DataFrame for each hostname
    host_dataframes = {}
    grand_totals = {
        'Events Received': 0,
        'Events Mangled': 0,
        'Events Lost (Reassembly)': 0,
        'Events Lost (Enqueue)': 0,
        'Data Errors': 0,
        'gRPC Errors': 0,
        'Total Packets': 0,
    }
    has_grand_data = {key: False for key in grand_totals.keys()}

    for hostname, rx_data_list in sorted(hosts_data.items()):
        data_dict = {}

        # Track host totals for summable fields
        host_totals = {
            'Events Received': 0,
            'Events Mangled': 0,
            'Events Lost (Reassembly)': 0,
            'Events Lost (Enqueue)': 0,
            'Data Errors': 0,
            'gRPC Errors': 0,
            'Total Packets': 0,
        }
        has_host_data = {key: False for key in host_totals.keys()}

        for rx_data in rx_data_list:
            col_name = rx_data['file']

            # Build column data
            column_data = {
                'Run ID': rx_data.get('run_id', 'N/A'),
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

            # Accumulate host totals
            if rx_data.get('events_received') is not None:
                host_totals['Events Received'] += rx_data['events_received']
                has_host_data['Events Received'] = True
            if rx_data.get('events_mangled') is not None:
                host_totals['Events Mangled'] += rx_data['events_mangled']
                has_host_data['Events Mangled'] = True
            if rx_data.get('events_lost_reassembly') is not None:
                host_totals['Events Lost (Reassembly)'] += rx_data['events_lost_reassembly']
                has_host_data['Events Lost (Reassembly)'] = True
            if rx_data.get('events_lost_enqueue') is not None:
                host_totals['Events Lost (Enqueue)'] += rx_data['events_lost_enqueue']
                has_host_data['Events Lost (Enqueue)'] = True
            if rx_data.get('data_errors') is not None:
                host_totals['Data Errors'] += rx_data['data_errors']
                has_host_data['Data Errors'] = True
            if rx_data.get('grpc_errors') is not None:
                host_totals['gRPC Errors'] += rx_data['grpc_errors']
                has_host_data['gRPC Errors'] = True
            if rx_data.get('total_packets') is not None:
                host_totals['Total Packets'] += rx_data['total_packets']
                has_host_data['Total Packets'] = True

            # Accumulate grand totals
            if rx_data.get('events_received') is not None:
                grand_totals['Events Received'] += rx_data['events_received']
                has_grand_data['Events Received'] = True
            if rx_data.get('events_mangled') is not None:
                grand_totals['Events Mangled'] += rx_data['events_mangled']
                has_grand_data['Events Mangled'] = True
            if rx_data.get('events_lost_reassembly') is not None:
                grand_totals['Events Lost (Reassembly)'] += rx_data['events_lost_reassembly']
                has_grand_data['Events Lost (Reassembly)'] = True
            if rx_data.get('events_lost_enqueue') is not None:
                grand_totals['Events Lost (Enqueue)'] += rx_data['events_lost_enqueue']
                has_grand_data['Events Lost (Enqueue)'] = True
            if rx_data.get('data_errors') is not None:
                grand_totals['Data Errors'] += rx_data['data_errors']
                has_grand_data['Data Errors'] = True
            if rx_data.get('grpc_errors') is not None:
                grand_totals['gRPC Errors'] += rx_data['grpc_errors']
                has_grand_data['gRPC Errors'] = True
            if rx_data.get('total_packets') is not None:
                grand_totals['Total Packets'] += rx_data['total_packets']
                has_grand_data['Total Packets'] = True

            data_dict[col_name] = column_data

        # Add TOTAL column for this host
        if data_dict:
            total_column = {
                'Run ID': '',
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
                'Events Received': f"{host_totals['Events Received']:,}" if has_host_data['Events Received'] else 'N/A',
                'Events Mangled': f"{host_totals['Events Mangled']:,}" if has_host_data['Events Mangled'] else 'N/A',
                'Events Lost (Reassembly)': f"{host_totals['Events Lost (Reassembly)']:,}" if has_host_data['Events Lost (Reassembly)'] else 'N/A',
                'Events Lost (Enqueue)': f"{host_totals['Events Lost (Enqueue)']:,}" if has_host_data['Events Lost (Enqueue)'] else 'N/A',
                'Data Errors': f"{host_totals['Data Errors']:,}" if has_host_data['Data Errors'] else 'N/A',
                'gRPC Errors': f"{host_totals['gRPC Errors']:,}" if has_host_data['gRPC Errors'] else 'N/A',
                'Total Packets': f"{host_totals['Total Packets']:,}" if has_host_data['Total Packets'] else 'N/A',
            }
            data_dict['TOTAL'] = total_column
            host_dataframes[hostname] = pd.DataFrame(data_dict)

    # Format grand totals
    formatted_grand_totals = {
        'Events Received': f"{grand_totals['Events Received']:,}" if has_grand_data['Events Received'] else 'N/A',
        'Events Mangled': f"{grand_totals['Events Mangled']:,}" if has_grand_data['Events Mangled'] else 'N/A',
        'Events Lost (Reassembly)': f"{grand_totals['Events Lost (Reassembly)']:,}" if has_grand_data['Events Lost (Reassembly)'] else 'N/A',
        'Events Lost (Enqueue)': f"{grand_totals['Events Lost (Enqueue)']:,}" if has_grand_data['Events Lost (Enqueue)'] else 'N/A',
        'Data Errors': f"{grand_totals['Data Errors']:,}" if has_grand_data['Data Errors'] else 'N/A',
        'gRPC Errors': f"{grand_totals['gRPC Errors']:,}" if has_grand_data['gRPC Errors'] else 'N/A',
        'Total Packets': f"{grand_totals['Total Packets']:,}" if has_grand_data['Total Packets'] else 'N/A',
    }

    return host_dataframes, formatted_grand_totals


def parse_ini_file(ini_path: Path) -> Dict[str, str]:
    """Parse an INI file and return a flat dictionary of all settings."""
    if not CONFIGPARSER_AVAILABLE:
        return {}

    config = configparser.ConfigParser()
    try:
        config.read(ini_path)
    except Exception as e:
        return {}

    # Flatten the config into a single dict with section.key format
    flat_dict = {}
    for section in config.sections():
        for key in config[section]:
            flat_key = f"[{section}] {key}"
            flat_dict[flat_key] = config[section][key]

    return flat_dict


def compare_ini_files(log_dir: Path, file_pattern: str) -> Optional[pd.DataFrame]:
    """Compare INI files and create a DataFrame showing differences."""
    if not PANDAS_AVAILABLE or not CONFIGPARSER_AVAILABLE:
        return None

    # Find all matching .ini files
    ini_files = sorted(log_dir.glob(file_pattern))
    if not ini_files:
        return None

    # Parse all INI files
    all_configs = {}
    for ini_file in ini_files:
        # Extract index from filename (e.g., "rx_0" from "reassembler_config_rx_0.ini")
        # or "tx_1" from "segmenter_config_tx_1.ini"
        parts = ini_file.stem.split('_')
        if len(parts) >= 3:
            # Format: segmenter_config_tx_0 or reassembler_config_rx_0
            index_key = f"{parts[-2]}_{parts[-1]}"  # e.g., "tx_0" or "rx_0"
        else:
            # Fallback to last part if format doesn't match
            index_key = parts[-1]
        all_configs[index_key] = parse_ini_file(ini_file)

    if not all_configs:
        return None

    # Get all unique keys across all configs
    all_keys = set()
    for config in all_configs.values():
        all_keys.update(config.keys())

    all_keys = sorted(all_keys)

    # Build DataFrame
    data_dict = {}
    for hostname, config in all_configs.items():
        column_data = {}
        for key in all_keys:
            column_data[key] = config.get(key, 'N/A')
        data_dict[hostname] = column_data

    df = pd.DataFrame(data_dict)

    # Identify rows where values differ across columns
    df['DIFFERS'] = df.apply(lambda row: '***' if len(set(row.dropna())) > 1 else '', axis=1)

    return df


def parse_instance_uri(log_dir: Path) -> Optional[str]:
    """Parse the INSTANCE_URI file to extract load balancer information."""
    # Check in the parent directory (where INSTANCE_URI is typically stored)
    instance_uri_file = log_dir.parent / 'INSTANCE_URI'

    if not instance_uri_file.exists():
        # Also check in the log directory itself
        instance_uri_file = log_dir / 'INSTANCE_URI'

    if not instance_uri_file.exists():
        return None

    try:
        with open(instance_uri_file, 'r') as f:
            content = f.read()

        # Extract the URI from export statement
        # Format: export EJFAT_URI='ejfats://...@host:port/...'
        match = re.search(r"ejfats?://[^@]+@([^:/]+)", content)
        if match:
            return match.group(1)

        # Also try to extract data plane IPs
        data_ips = re.findall(r'data=([^&\'"]+)', content)
        if data_ips:
            return match.group(1) if match else None
    except Exception as e:
        return None

    return None


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

    # Parse load balancer info
    lb_host = parse_instance_uri(log_dir)

    print()
    print_separator('=', 80)
    print(f"{'EJFAT LOG SUMMARY':^80}")
    print_separator('=', 80)
    print(f"Log Directory: {log_dir.resolve()}")
    print(f"Transmitter Logs Found: {len(tx_files)}")
    print(f"Receiver Logs Found: {len(rx_files)}")
    if lb_host:
        print(f"Load Balancer: {lb_host}")

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

    # Filter files by the latest RUN_ID
    latest_run_id = None
    all_run_ids = set()

    # Collect all run IDs
    for tx_file in tx_files:
        tx_data = parse_tx_log(tx_file)
        if tx_data and tx_data.get('run_id'):
            all_run_ids.add(tx_data['run_id'])

    for rx_file in rx_files:
        rx_data = parse_rx_log(rx_file)
        if rx_data and rx_data.get('run_id'):
            all_run_ids.add(rx_data['run_id'])

    # Pick the latest run ID (alphabetically sorted, since format is YYYYMMDD_HHMMSS)
    if all_run_ids:
        latest_run_id = sorted(all_run_ids)[-1]
        ignored_run_ids = sorted(all_run_ids - {latest_run_id})

        if ignored_run_ids:
            print()
            print_separator('=', 80)
            print(f"{'WARNING: Multiple Run IDs Detected':^80}")
            print_separator('=', 80)
            print(f"Latest Run ID (used for analysis): {latest_run_id}")
            print(f"Ignored Run IDs: {', '.join(ignored_run_ids)}")
            print()
            print("Only logs matching the latest Run ID will be included in the analysis.")
            print_separator('=', 80)

        # Filter files by latest run ID
        filtered_tx_files = []
        for tx_file in tx_files:
            tx_data = parse_tx_log(tx_file)
            if tx_data and tx_data.get('run_id') == latest_run_id:
                filtered_tx_files.append(tx_file)

        filtered_rx_files = []
        for rx_file in rx_files:
            rx_data = parse_rx_log(rx_file)
            if rx_data and rx_data.get('run_id') == latest_run_id:
                filtered_rx_files.append(rx_file)

        # Use filtered files for the rest of the analysis
        tx_files = filtered_tx_files
        rx_files = filtered_rx_files

        print()
        print_separator('=', 80)
        print(f"Analysis for Run ID: {latest_run_id}")
        print_separator('=', 80)
        print(f"Transmitter Logs (filtered): {len(tx_files)}")
        print(f"Receiver Logs (filtered): {len(rx_files)}")

    # Print DataFrames for side-by-side comparison
    if PANDAS_AVAILABLE:
        # Compare segmenter config files FIRST
        print()
        print(f"{'SEGMENTER CONFIG COMPARISON':^80}")
        print_separator('=', 80)
        segmenter_df = compare_ini_files(log_dir, 'segmenter_config_tx_*.ini')
        if segmenter_df is not None:
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', None)
            print(segmenter_df.to_string())
            print()
            # Show only differing rows
            diff_rows = segmenter_df[segmenter_df['DIFFERS'] == '***']
            if not diff_rows.empty:
                print()
                print("DIFFERENCES FOUND (*** marked):")
                print(diff_rows.to_string())
        else:
            print("No segmenter config files found for comparison")
        print()
        print_separator('=', 80)

        # Compare reassembler config files SECOND
        print()
        print(f"{'REASSEMBLER CONFIG COMPARISON':^80}")
        print_separator('=', 80)
        reassembler_df = compare_ini_files(log_dir, 'reassembler_config_rx_*.ini')
        if reassembler_df is not None:
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', None)
            print(reassembler_df.to_string())
            print()
            # Show only differing rows
            diff_rows = reassembler_df[reassembler_df['DIFFERS'] == '***']
            if not diff_rows.empty:
                print()
                print("DIFFERENCES FOUND (*** marked):")
                print(diff_rows.to_string())
        else:
            print("No reassembler config files found for comparison")
        print()
        print_separator('=', 80)

        # Create transmitter comparison DataFrames grouped by host - THIRD
        tx_host_dfs = {}
        tx_grand_totals = {}
        if tx_files:
            print()
            print(f"{'TRANSMITTER COMPARISON BY HOST':^80}")
            print_separator('=', 80)
            tx_host_dfs, tx_grand_totals = create_tx_dataframes_by_host(tx_files)
            if tx_host_dfs:
                # Configure pandas display options for better formatting
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                pd.set_option('display.max_colwidth', None)

                # Print one table per host
                for hostname in sorted(tx_host_dfs.keys()):
                    print()
                    print(f"Transmitter: {hostname}")
                    print_separator('-', 80)
                    print(tx_host_dfs[hostname].to_string())
                    print()
            else:
                print("No transmitter data available for comparison")
            print()
            print_separator('=', 80)

        # Create receiver comparison DataFrames grouped by host - FOURTH
        rx_host_dfs = {}
        rx_grand_totals = {}
        if rx_files:
            print()
            print(f"{'RECEIVER COMPARISON BY HOST':^80}")
            print_separator('=', 80)
            rx_host_dfs, rx_grand_totals = create_rx_dataframes_by_host(rx_files)
            if rx_host_dfs:
                # Configure pandas display options for better formatting
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                pd.set_option('display.max_colwidth', None)

                # Print one table per host
                for hostname in sorted(rx_host_dfs.keys()):
                    print()
                    print(f"Receiver: {hostname}")
                    print_separator('-', 80)
                    print(rx_host_dfs[hostname].to_string())
                    print()
            else:
                print("No receiver data available for comparison")
            print()
            print_separator('=', 80)

        # Print combined grand totals - FIFTH
        if tx_grand_totals or rx_grand_totals:
            print()
            print_separator('=', 80)
            print(f"{'GRAND TOTALS':^80}")
            print_separator('=', 80)

            if tx_grand_totals:
                print()
                print("TRANSMITTER:")
                print(f"  Frames Sent:       {tx_grand_totals['Frames Sent']}")
                print(f"  Errors:            {tx_grand_totals['Errors']}")
                print(f"  Throughput (Gbps): {tx_grand_totals['Throughput (Gbps)']}")
                print(f"  Goodput (Gbps):    {tx_grand_totals['Goodput (Gbps)']}")

            if rx_grand_totals:
                print()
                print("RECEIVER:")
                print(f"  Events Received:           {rx_grand_totals['Events Received']}")
                print(f"  Events Mangled:            {rx_grand_totals['Events Mangled']}")
                print(f"  Events Lost (Reassembly):  {rx_grand_totals['Events Lost (Reassembly)']}")
                print(f"  Events Lost (Enqueue):     {rx_grand_totals['Events Lost (Enqueue)']}")
                print(f"  Data Errors:               {rx_grand_totals['Data Errors']}")
                print(f"  gRPC Errors:               {rx_grand_totals['gRPC Errors']}")
                print(f"  Total Packets:             {rx_grand_totals['Total Packets']}")

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
