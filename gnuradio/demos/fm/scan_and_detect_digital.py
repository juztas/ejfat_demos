#!/usr/bin/env python3
"""
Scan Ottawa FM stations and detect digital FM content.

This script:
1. Tunes to each Ottawa FM station
2. Waits for measurements to settle
3. Reads the digital FM indicator (0=analog, 1=digital)
4. Reports which stations have digital content
5. Records data using Bluesky databroker
"""

import xmlrpc.client
import time
import sys
from datetime import datetime
from event_model import compose_run
import uuid

# Ottawa FM Radio Stations (frequencies in MHz)
# Comprehensive list of Ottawa-Gatineau region FM stations
OTTAWA_FM_STATIONS = [
    # Canadian stations (88-108 MHz)
    {"freq": 88.5, "name": "CKCU-FM", "format": "Campus/Community", "location": "Ottawa"},
    {"freq": 89.9, "name": "CIHT-FM (Hot 89.9)", "format": "CHR/Top 40", "location": "Ottawa"},
    {"freq": 90.7, "name": "CFFX-FM (Move 90.7)", "format": "Hot AC", "location": "Kingston"},
    {"freq": 91.5, "name": "CBON-FM (CBC Radio One)", "format": "CBC French", "location": "Sudbury"},
    {"freq": 93.9, "name": "CJOT-FM (Boom 99.7)", "format": "Adult Contemporary", "location": "Ottawa"},
    {"freq": 94.5, "name": "CJMJ-FM (Majic 100)", "format": "Adult Contemporary", "location": "Ottawa"},
    {"freq": 95.7, "name": "CHEY-FM (Y95.7)", "format": "Country", "location": "Arnprior"},
    {"freq": 96.5, "name": "CKBY-FM (Y101)", "format": "Country", "location": "Smiths Falls"},
    {"freq": 97.9, "name": "CIMF-FM (NOW! 97.9)", "format": "Hot AC", "location": "Gatineau"},
    {"freq": 99.7, "name": "CKQB-FM (The Bear)", "format": "Classic Rock", "location": "Ottawa"},
    {"freq": 100.3, "name": "CKKL-FM (Bob FM)", "format": "Adult Hits", "location": "Ottawa"},
    {"freq": 101.1, "name": "CIBO-FM (CBC Radio One)", "format": "CBC English", "location": "Ottawa"},
    {"freq": 101.9, "name": "CKOI-FM", "format": "CHR/Top 40 French", "location": "Gatineau"},
    {"freq": 102.5, "name": "CFRA", "format": "News/Talk", "location": "Ottawa"},
    {"freq": 103.3, "name": "CJFO-FM (104.7 FM)", "format": "Hot AC French", "location": "Ottawa"},
    {"freq": 104.1, "name": "CJRC-FM (Rythme FM)", "format": "AC French", "location": "Gatineau"},
    {"freq": 104.7, "name": "CFFX-FM (104.7 The Wolf)", "format": "Rock", "location": "Pembroke"},
    {"freq": 105.3, "name": "CKBY-FM (Y101)", "format": "Country", "location": "Ottawa"},
    {"freq": 106.1, "name": "CHEZ-FM", "format": "Classic Rock", "location": "Ottawa"},
    {"freq": 106.9, "name": "CISS-FM (Kiss FM)", "format": "Hot AC", "location": "Ottawa"},
]

def scan_stations(dwell_time=10, host='localhost', port=8080, record_data=True):
    """
    Scan through Ottawa FM stations and detect digital content.

    Parameters
    ----------
    dwell_time : float
        Seconds to dwell on each frequency
    host : str
        XML-RPC server hostname
    port : int
        XML-RPC server port
    record_data : bool
        Whether to record data using Bluesky documents
    """
    print("="*80)
    print("OTTAWA FM DIGITAL DETECTION SCAN")
    print("="*80)
    print(f"Stations: {len(OTTAWA_FM_STATIONS)}")
    print(f"Dwell time: {dwell_time} seconds per station")
    print(f"Total time: ~{len(OTTAWA_FM_STATIONS) * dwell_time:.0f} seconds")
    if record_data:
        print(f"Data recording: ENABLED (Bluesky documents)")
    print("="*80)
    print()

    # Connect to XML-RPC server
    try:
        url = f'http://{host}:{port}'
        rpc = xmlrpc.client.ServerProxy(url)

        # Test connection
        current_freq = rpc.get_freq()
        print(f"✓ Connected to digital detector at {host}:{port}")
        print(f"  Current frequency: {current_freq/1e6:.1f} MHz")
        print()
    except Exception as e:
        print(f"✗ Failed to connect to digital detector: {e}")
        print(f"\nMake sure the digital detector flowgraph is running")
        print(f"with XML-RPC server on {host}:{port}")
        sys.exit(1)

    # Results storage
    digital_stations = []
    analog_stations = []

    # Initialize Bluesky document generation if recording
    documents = []
    if record_data:
        # Create a run
        metadata = {
            'scan_type': 'fm_digital_detection',
            'num_stations': len(OTTAWA_FM_STATIONS),
            'dwell_time': dwell_time,
            'detector_host': host,
            'detector_port': port,
        }

        run_bundle = compose_run(metadata=metadata)
        start_doc = run_bundle.start_doc
        compose_descriptor = run_bundle.compose_descriptor
        compose_stop = run_bundle.compose_stop

        documents.append(('start', start_doc))
        print(f"Run UID: {start_doc['uid']}")
        print()

        # Create descriptor for FM station measurements
        data_keys = {
            'frequency': {
                'source': 'fm_detector',
                'dtype': 'number',
                'shape': [],
                'units': 'MHz',
            },
            'signal_level': {
                'source': 'fm_detector',
                'dtype': 'number',
                'shape': [],
                'units': 'dB',
            },
            'digital_detected': {
                'source': 'fm_detector',
                'dtype': 'boolean',
                'shape': [],
            },
            'station_name': {
                'source': 'fm_detector',
                'dtype': 'string',
                'shape': [],
            },
            'station_format': {
                'source': 'fm_detector',
                'dtype': 'string',
                'shape': [],
            },
            'station_location': {
                'source': 'fm_detector',
                'dtype': 'string',
                'shape': [],
            },
        }

        configuration = {
            'fm_detector': {
                'data': {
                    'dwell_time': dwell_time,
                },
                'timestamps': {
                    'dwell_time': time.time(),
                },
            }
        }

        descriptor_bundle = compose_descriptor(
            name='primary',
            data_keys=data_keys,
            configuration=configuration,
        )
        descriptor_doc = descriptor_bundle.descriptor_doc
        compose_event = descriptor_bundle.compose_event
        documents.append(('descriptor', descriptor_doc))

    print("Starting scan...")
    print()
    print(f"{'#':<4} {'Freq':<8} {'Station':<35} {'Format':<20} {'Location':<15} {'Signal':<10} {'Digital'}")
    print("-" * 110)

    for i, station in enumerate(OTTAWA_FM_STATIONS, 1):
        freq_hz = station['freq'] * 1e6

        # Set frequency
        try:
            rpc.set_freq(freq_hz)
        except Exception as e:
            print(f"[{i:2d}] {station['freq']:6.1f} MHz  ERROR setting frequency: {e}")
            continue

        # Dwell to allow measurements to settle
        time.sleep(dwell_time)

        # Read signal level and digital indicator via XML-RPC
        signal_level_db = None
        try:
            digital_value = rpc.get_digital_indicator()
            # digital_value will be 0.0 (analog) or 1.0 (digital)
            digital_detected = (digital_value > 0.5)
            digital_str = "DIGITAL" if digital_detected else "Analog"
        except Exception as e:
            digital_str = f"ERROR ({e})"
            digital_detected = None

        # Read signal level (FM power in dB)
        try:
            signal_level_db = rpc.get_signal_level()
        except Exception as e:
            signal_level_db = None

        # Format signal level display
        if signal_level_db is not None:
            signal_str = f"{signal_level_db:5.1f} dB"
        else:
            signal_str = "N/A"

        print(f"[{i:2d}] {station['freq']:6.1f} MHz  "
              f"{station['name']:<35} "
              f"{station['format']:<20} "
              f"{station['location']:<15} "
              f"{signal_str:<10} "
              f"{digital_str}")

        # Store results with signal level
        station_with_level = station.copy()
        station_with_level['signal_level_db'] = signal_level_db

        if digital_detected is True:
            digital_stations.append(station_with_level)
        elif digital_detected is False:
            analog_stations.append(station_with_level)

        # Record event in Bluesky documents
        if record_data and digital_detected is not None:
            current_time = time.time()
            event_data = {
                'frequency': station['freq'],
                'signal_level': signal_level_db if signal_level_db is not None else float('nan'),
                'digital_detected': bool(digital_detected),
                'station_name': station['name'],
                'station_format': station['format'],
                'station_location': station['location'],
            }
            event_timestamps = {
                'frequency': current_time,
                'signal_level': current_time,
                'digital_detected': current_time,
                'station_name': current_time,
                'station_format': current_time,
                'station_location': current_time,
            }

            event_doc = compose_event(
                data=event_data,
                timestamps=event_timestamps,
            )
            documents.append(('event', event_doc))

    print("-" * 110)
    print()
    print("="*80)
    print("SCAN COMPLETE")
    print("="*80)
    print()

    # Calculate average signal levels
    def calc_avg_signal(stations):
        levels = [s['signal_level_db'] for s in stations if s['signal_level_db'] is not None]
        return sum(levels) / len(levels) if levels else None

    digital_avg = calc_avg_signal(digital_stations)
    analog_avg = calc_avg_signal(analog_stations)

    if digital_stations:
        print(f"Digital FM Stations Found: {len(digital_stations)}")
        if digital_avg is not None:
            print(f"  Average signal level: {digital_avg:.1f} dB")
        for station in digital_stations:
            signal_info = f" ({station['signal_level_db']:.1f} dB)" if station['signal_level_db'] is not None else ""
            print(f"  {station['freq']:6.1f} MHz - {station['name']}{signal_info}")
    else:
        print("No digital FM stations detected.")

    print()
    if analog_stations:
        print(f"Analog-only stations: {len(analog_stations)}")
        if analog_avg is not None:
            print(f"  Average signal level: {analog_avg:.1f} dB")
        for station in analog_stations:
            signal_info = f" ({station['signal_level_db']:.1f} dB)" if station['signal_level_db'] is not None else ""
            print(f"  {station['freq']:6.1f} MHz - {station['name']}{signal_info}")
    else:
        print(f"Analog-only stations: 0")
    print()

    if not digital_stations and not analog_stations:
        print("NOTE: No stations were successfully classified.")
        print("Make sure the digital detector flowgraph is running with")
        print("the digital_indicator variable exposed via XML-RPC.")

    # Close the run and save documents
    if record_data:
        # Add stop document
        stop_doc = compose_stop()
        documents.append(('stop', stop_doc))

        # Save documents to msgpack file
        from suitcase.msgpack import Serializer
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fm_scan_{timestamp}"

        with Serializer(filename) as serializer:
            for doc_name, doc in documents:
                serializer(doc_name, doc)

        print()
        print(f"Data saved to: {filename}/")
        print(f"Run UID: {start_doc['uid']}")
        print(f"Total events recorded: {len([d for d in documents if d[0] == 'event'])}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Scan Ottawa FM stations for digital content',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--dwell', type=float, default=10,
                       metavar='SECONDS',
                       help='Dwell time per frequency in seconds (default: 10)')
    parser.add_argument('--host', type=str, default='localhost',
                       help='XML-RPC server hostname (default: localhost)')
    parser.add_argument('--port', type=int, default=8080,
                       help='XML-RPC server port (default: 8080)')
    parser.add_argument('--no-record', action='store_true',
                       help='Disable data recording (default: recording enabled)')

    args = parser.parse_args()

    try:
        scan_stations(args.dwell, args.host, args.port, record_data=not args.no_record)
    except KeyboardInterrupt:
        print("\n\n✗ Scan interrupted by user")
        sys.exit(0)


if __name__ == '__main__':
    main()
