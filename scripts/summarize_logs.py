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
        'config_file': None,
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
    config_match = re.search(r'Config file:\s*(.+)', content)
    if config_match:
        data['config_file'] = config_match.group(1).strip()

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
    # Find all Stats blocks and get the last complete one
    stats_pattern = r'Stats:\s+Events Received:\s*([\d,]+)\s+Events Mangled:\s*([\d,]+)\s+Events Lost in reassembly:\s*([\d,]+)\s+Events Lost in enqueue:\s*([\d,]+)\s+Data Errors:\s*([\d,]+)\s+gRPC Errors:\s*([\d,]+)'
    stats_matches = list(re.finditer(stats_pattern, content))
    if stats_matches:
        # Get the last stats block before "Stopping threads"
        stopping_pos = content.find('Stopping threads')
        if stopping_pos != -1:
            # Find the last stats block before stopping
            for match in reversed(stats_matches):
                if match.start() < stopping_pos:
                    data['events_received'] = int(match.group(1).replace(',', ''))
                    data['events_mangled'] = int(match.group(2).replace(',', ''))
                    data['events_lost_reassembly'] = int(match.group(3).replace(',', ''))
                    data['events_lost_enqueue'] = int(match.group(4).replace(',', ''))
                    data['data_errors'] = int(match.group(5).replace(',', ''))
                    data['grpc_errors'] = int(match.group(6).replace(',', ''))
                    break

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

    if tx_data['config_file']:
        print(f"Config File:         {tx_data['config_file']}")

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

        # Calculate totals
        total_tx_frames = 0
        total_tx_errors = 0
        for tx_file in tx_files:
            tx_data = parse_tx_log(tx_file)
            if tx_data and tx_data['frames_sent'] is not None:
                total_tx_frames += tx_data['frames_sent']
            if tx_data and tx_data['errors'] is not None:
                total_tx_errors += tx_data['errors']

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
    print()


if __name__ == '__main__':
    main()
