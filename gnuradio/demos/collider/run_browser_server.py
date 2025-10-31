#!/usr/bin/env python3
"""
Run Browser Server

Provides a REST API for browsing and analyzing DAQ runs from the
particle collider streaming DAQ system.

Features:
- Inventory all runs in a data directory
- Retrieve run metadata and statistics
- Access detector data (pixel and calorimeter)
- Generate summaries and visualizations
- Web-based UI for point-and-click browsing
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import pandas as pd
import numpy as np


class RunInventory:
    """
    Manages inventory of all DAQ runs in a directory

    Scans for pixel_detector_*.csv and calorimeter_detector_*.csv files
    and builds an index of all runs.
    """

    def __init__(self, data_dir='.'):
        """
        Initialize run inventory

        Parameters:
        -----------
        data_dir : str
            Directory containing DAQ data files
        """
        self.data_dir = Path(data_dir).absolute()
        self.runs = {}
        self.scan_runs()

    def scan_runs(self):
        """Scan data directory for all runs"""
        self.runs = {}

        if not self.data_dir.exists():
            print(f"Warning: Data directory does not exist: {self.data_dir}")
            return

        # Find all pixel detector files
        pixel_files = list(self.data_dir.glob("pixel_detector_*.csv"))

        for pixel_file in pixel_files:
            # Extract run_id from filename
            run_id = pixel_file.stem.replace("pixel_detector_", "")

            # Look for corresponding calorimeter file
            calo_file = self.data_dir / f"calorimeter_detector_{run_id}.csv"

            if calo_file.exists():
                # Create run entry
                self.runs[run_id] = {
                    'run_id': run_id,
                    'pixel_file': str(pixel_file),
                    'calorimeter_file': str(calo_file),
                    'pixel_file_name': pixel_file.name,
                    'calorimeter_file_name': calo_file.name,
                    'created': datetime.fromtimestamp(pixel_file.stat().st_mtime),
                    'size_pixel': pixel_file.stat().st_size,
                    'size_calorimeter': calo_file.stat().st_size
                }

        print(f"Found {len(self.runs)} runs in {self.data_dir}")

    def get_run_list(self):
        """
        Get list of all runs sorted by creation time

        Returns:
        --------
        list : List of run dictionaries
        """
        runs = list(self.runs.values())
        runs.sort(key=lambda r: r['created'], reverse=True)
        return runs

    def get_run(self, run_id):
        """
        Get information about a specific run

        Parameters:
        -----------
        run_id : str
            Run identifier

        Returns:
        --------
        dict : Run information or None if not found
        """
        return self.runs.get(run_id)

    def get_run_summary(self, run_id):
        """
        Get detailed summary of a run including statistics

        Parameters:
        -----------
        run_id : str
            Run identifier

        Returns:
        --------
        dict : Run summary with statistics
        """
        run = self.get_run(run_id)
        if not run:
            return None

        summary = run.copy()

        # Load pixel data and compute statistics
        try:
            pixel_df = pd.read_csv(run['pixel_file'])
            summary['pixel_stats'] = {
                'total_hits': len(pixel_df),
                'unique_particles': pixel_df['particle_id'].nunique(),
                'pixel_range': [int(pixel_df['pixel_number'].min()),
                               int(pixel_df['pixel_number'].max())],
                'time_range': [float(pixel_df['simulation_time'].min()),
                              float(pixel_df['simulation_time'].max())],
                'duration': float(pixel_df['simulation_time'].max() -
                                pixel_df['simulation_time'].min())
            }

            # Pixel hit distribution
            pixel_hist, _ = np.histogram(pixel_df['pixel_number'], bins=64)
            summary['pixel_stats']['hit_distribution'] = pixel_hist.tolist()

        except Exception as e:
            print(f"Error loading pixel data for {run_id}: {e}")
            summary['pixel_stats'] = {'error': str(e)}

        # Load calorimeter data and compute statistics
        try:
            calo_df = pd.read_csv(run['calorimeter_file'])
            summary['calorimeter_stats'] = {
                'total_hits': len(calo_df),
                'unique_particles': calo_df['particle_id'].nunique(),
                'segment_range': [int(calo_df['segment_number'].min()),
                                 int(calo_df['segment_number'].max())],
                'speed_range': [float(calo_df['particle_speed'].min()),
                               float(calo_df['particle_speed'].max())],
                'angle_range': [float(calo_df['deflection_angle'].min()),
                               float(calo_df['deflection_angle'].max())],
                'time_range': [float(calo_df['simulation_time'].min()),
                              float(calo_df['simulation_time'].max())],
                'duration': float(calo_df['simulation_time'].max() -
                                calo_df['simulation_time'].min())
            }

            # Segment hit distribution
            segment_hist, _ = np.histogram(calo_df['segment_number'], bins=64)
            summary['calorimeter_stats']['hit_distribution'] = segment_hist.tolist()

            # Speed distribution
            speed_hist, speed_bins = np.histogram(calo_df['particle_speed'], bins=20)
            summary['calorimeter_stats']['speed_histogram'] = {
                'counts': speed_hist.tolist(),
                'bins': speed_bins.tolist()
            }

            # Angle distribution
            angle_hist, angle_bins = np.histogram(calo_df['deflection_angle'], bins=20)
            summary['calorimeter_stats']['angle_histogram'] = {
                'counts': angle_hist.tolist(),
                'bins': angle_bins.tolist()
            }

        except Exception as e:
            print(f"Error loading calorimeter data for {run_id}: {e}")
            summary['calorimeter_stats'] = {'error': str(e)}

        # Format datetime for JSON serialization
        summary['created'] = summary['created'].isoformat()

        return summary

    def get_run_data(self, run_id, detector='pixel', limit=None):
        """
        Get raw data from a run

        Parameters:
        -----------
        run_id : str
            Run identifier
        detector : str
            'pixel' or 'calorimeter'
        limit : int, optional
            Maximum number of rows to return

        Returns:
        --------
        list : List of data rows as dictionaries
        """
        run = self.get_run(run_id)
        if not run:
            return None

        file_path = run['pixel_file'] if detector == 'pixel' else run['calorimeter_file']

        try:
            df = pd.read_csv(file_path)
            if limit:
                df = df.head(limit)
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading {detector} data for {run_id}: {e}")
            return None


class RunBrowserHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for run browser API and UI"""

    inventory = None  # Will be set by server

    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # API endpoints
        if path == '/api/runs':
            self.serve_run_list()
        elif path.startswith('/api/run/'):
            run_id = path.replace('/api/run/', '').split('/')[0]
            if '/summary' in path:
                self.serve_run_summary(run_id)
            elif '/data' in path:
                detector = query.get('detector', ['pixel'])[0]
                limit = query.get('limit', [None])[0]
                limit = int(limit) if limit else None
                self.serve_run_data(run_id, detector, limit)
            else:
                self.serve_run_info(run_id)
        elif path == '/api/refresh':
            self.refresh_inventory()
        else:
            # Serve static files
            super().do_GET()

    def serve_run_list(self):
        """Serve list of all runs"""
        runs = self.inventory.get_run_list()

        # Format for JSON
        runs_json = []
        for run in runs:
            run_copy = run.copy()
            run_copy['created'] = run_copy['created'].isoformat()
            runs_json.append(run_copy)

        self.send_json_response(runs_json)

    def serve_run_info(self, run_id):
        """Serve basic run information"""
        run = self.inventory.get_run(run_id)
        if not run:
            self.send_error(404, f"Run {run_id} not found")
            return

        run_copy = run.copy()
        run_copy['created'] = run_copy['created'].isoformat()
        self.send_json_response(run_copy)

    def serve_run_summary(self, run_id):
        """Serve detailed run summary with statistics"""
        summary = self.inventory.get_run_summary(run_id)
        if not summary:
            self.send_error(404, f"Run {run_id} not found")
            return

        self.send_json_response(summary)

    def serve_run_data(self, run_id, detector, limit):
        """Serve raw run data"""
        data = self.inventory.get_run_data(run_id, detector, limit)
        if data is None:
            self.send_error(404, f"Data for run {run_id} not found")
            return

        self.send_json_response(data)

    def refresh_inventory(self):
        """Refresh run inventory"""
        self.inventory.scan_runs()
        self.send_json_response({'status': 'success', 'runs': len(self.inventory.runs)})

    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())


def run_server(data_dir='.', port=8080):
    """
    Start the run browser server

    Parameters:
    -----------
    data_dir : str
        Directory containing DAQ data files
    port : int
        Port to run server on (default: 8080)
    """
    # Create inventory
    inventory = RunInventory(data_dir)

    # Set inventory for handler
    RunBrowserHandler.inventory = inventory

    # Create server
    server = HTTPServer(('localhost', port), RunBrowserHandler)

    print("=" * 60)
    print("Run Browser Server")
    print("=" * 60)
    print(f"Data directory: {inventory.data_dir}")
    print(f"Runs found: {len(inventory.runs)}")
    print(f"\nServer running at: http://localhost:{port}")
    print(f"Web UI: http://localhost:{port}/run_browser.html")
    print(f"\nAPI Endpoints:")
    print(f"  GET /api/runs - List all runs")
    print(f"  GET /api/run/<run_id> - Get run info")
    print(f"  GET /api/run/<run_id>/summary - Get detailed summary")
    print(f"  GET /api/run/<run_id>/data?detector=pixel&limit=100 - Get data")
    print(f"  GET /api/refresh - Refresh run inventory")
    print(f"\nPress Ctrl+C to stop")
    print("=" * 60 + "\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.shutdown()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run Browser Server')
    parser.add_argument('--data-dir', '-d', default='.',
                       help='Data directory (default: current directory)')
    parser.add_argument('--port', '-p', type=int, default=8080,
                       help='Port to run server on (default: 8080)')

    args = parser.parse_args()

    run_server(data_dir=args.data_dir, port=args.port)
