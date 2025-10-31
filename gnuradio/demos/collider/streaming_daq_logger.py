#!/usr/bin/env python3
"""
Streaming DAQ Data Loggers

Provides separate streaming data loggers for pixel detector and calorimeter detector
that write data continuously to timestamped files during a Bluesky run.

Each logger creates CSV files with timestamps for later joining and analysis.
"""

import csv
import time
from datetime import datetime
from pathlib import Path
import threading


class PixelDetectorLogger:
    """
    Streaming logger for pixel detector hits

    Writes each pixel hit to CSV file immediately with timestamp.
    File format: timestamp, particle_id, pixel_number, hit_time
    """

    def __init__(self, run_id=None, data_dir='.'):
        """
        Initialize pixel detector logger

        Parameters:
        -----------
        run_id : str, optional
            Unique run identifier (e.g., Bluesky run UID)
        data_dir : str
            Directory for data files (default: current directory)
        """
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        self.filename = self.data_dir / f"pixel_detector_{self.run_id}.csv"

        # Open file and write header
        self.file = open(self.filename, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow([
            'wall_time',           # Wall clock time (seconds since epoch)
            'simulation_time',     # Simulation time (seconds)
            'particle_id',         # Particle ID number
            'pixel_number',        # Pixel number (0-6399)
            'hit_time'            # Simulation time when pixel was hit
        ])
        self.file.flush()

        # Statistics
        self.hit_count = 0
        self.is_open = True

        # Thread safety
        self.lock = threading.Lock()

        print(f"Pixel detector logger started: {self.filename}")

    def log_hit(self, particle_id, pixel_number, hit_time, simulation_time):
        """
        Log a pixel detector hit

        Parameters:
        -----------
        particle_id : int
            Unique particle identifier
        pixel_number : int
            Pixel number that was hit (0-6399)
        hit_time : float
            Simulation time when pixel was hit
        simulation_time : float
            Current simulation time
        """
        if not self.is_open:
            return

        with self.lock:
            wall_time = time.time()
            self.writer.writerow([
                wall_time,
                simulation_time,
                particle_id,
                pixel_number,
                hit_time
            ])
            self.file.flush()
            self.hit_count += 1

    def close(self):
        """Close the data file"""
        if self.is_open:
            with self.lock:
                self.file.close()
                self.is_open = False
                print(f"Pixel detector logger closed: {self.hit_count} hits recorded")

    def get_filename(self):
        """Return the absolute path to the data file"""
        return str(self.filename.absolute())

    def __del__(self):
        """Ensure file is closed on deletion"""
        if hasattr(self, 'is_open') and self.is_open:
            self.close()


class CalorimeterDetectorLogger:
    """
    Streaming logger for calorimeter detector hits

    Writes each calorimeter hit to CSV file immediately with timestamp.
    File format: timestamp, particle_id, segment_number, hit_time, particle_speed
    """

    def __init__(self, run_id=None, data_dir='.'):
        """
        Initialize calorimeter detector logger

        Parameters:
        -----------
        run_id : str, optional
            Unique run identifier (e.g., Bluesky run UID)
        data_dir : str
            Directory for data files (default: current directory)
        """
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        self.filename = self.data_dir / f"calorimeter_detector_{self.run_id}.csv"

        # Open file and write header
        self.file = open(self.filename, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow([
            'wall_time',           # Wall clock time (seconds since epoch)
            'simulation_time',     # Simulation time (seconds)
            'particle_id',         # Particle ID number
            'segment_number',      # Calorimeter segment (0-63)
            'hit_time',           # Simulation time when calorimeter was hit
            'particle_speed',     # Particle speed (for pulse amplitude)
            'deflection_angle'    # Deflection angle (degrees)
        ])
        self.file.flush()

        # Statistics
        self.hit_count = 0
        self.is_open = True

        # Thread safety
        self.lock = threading.Lock()

        print(f"Calorimeter detector logger started: {self.filename}")

    def log_hit(self, particle_id, segment_number, hit_time, particle_speed,
                deflection_angle, simulation_time):
        """
        Log a calorimeter detector hit

        Parameters:
        -----------
        particle_id : int
            Unique particle identifier
        segment_number : int
            Calorimeter segment that was hit (0-63)
        hit_time : float
            Simulation time when calorimeter was hit
        particle_speed : float
            Speed of the particle (used for pulse amplitude)
        deflection_angle : float
            Particle deflection angle in degrees
        simulation_time : float
            Current simulation time
        """
        if not self.is_open:
            return

        with self.lock:
            wall_time = time.time()
            self.writer.writerow([
                wall_time,
                simulation_time,
                particle_id,
                segment_number,
                hit_time,
                particle_speed,
                deflection_angle
            ])
            self.file.flush()
            self.hit_count += 1

    def close(self):
        """Close the data file"""
        if self.is_open:
            with self.lock:
                self.file.close()
                self.is_open = False
                print(f"Calorimeter detector logger closed: {self.hit_count} hits recorded")

    def get_filename(self):
        """Return the absolute path to the data file"""
        return str(self.filename.absolute())

    def __del__(self):
        """Ensure file is closed on deletion"""
        if hasattr(self, 'is_open') and self.is_open:
            self.close()


class StreamingDAQManager:
    """
    Manager for all streaming DAQ loggers

    Coordinates pixel and calorimeter loggers for a single run.
    """

    def __init__(self, run_id=None, data_dir='.'):
        """
        Initialize DAQ manager for a run

        Parameters:
        -----------
        run_id : str, optional
            Unique run identifier (e.g., Bluesky run UID)
        data_dir : str
            Directory for data files (default: current directory)
        """
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = data_dir

        # Create loggers
        self.pixel_logger = PixelDetectorLogger(run_id=self.run_id, data_dir=data_dir)
        self.calorimeter_logger = CalorimeterDetectorLogger(run_id=self.run_id, data_dir=data_dir)

        self.start_time = time.time()

        print(f"Streaming DAQ started for run: {self.run_id}")

    def log_pixel_hit(self, particle_id, pixel_number, hit_time, simulation_time):
        """Log a pixel detector hit"""
        self.pixel_logger.log_hit(particle_id, pixel_number, hit_time, simulation_time)

    def log_calorimeter_hit(self, particle_id, segment_number, hit_time,
                           particle_speed, deflection_angle, simulation_time):
        """Log a calorimeter detector hit"""
        self.calorimeter_logger.log_hit(particle_id, segment_number, hit_time,
                                        particle_speed, deflection_angle, simulation_time)

    def get_file_paths(self):
        """
        Get absolute paths to all data files

        Returns:
        --------
        dict
            Dictionary with 'pixel' and 'calorimeter' file paths
        """
        return {
            'pixel': self.pixel_logger.get_filename(),
            'calorimeter': self.calorimeter_logger.get_filename()
        }

    def get_statistics(self):
        """
        Get logging statistics

        Returns:
        --------
        dict
            Statistics for pixel and calorimeter loggers
        """
        return {
            'run_id': self.run_id,
            'elapsed_time': time.time() - self.start_time,
            'pixel_hits': self.pixel_logger.hit_count,
            'calorimeter_hits': self.calorimeter_logger.hit_count,
            'files': self.get_file_paths()
        }

    def close(self):
        """Close all loggers"""
        self.pixel_logger.close()
        self.calorimeter_logger.close()

        stats = self.get_statistics()
        print(f"\nStreaming DAQ closed for run: {self.run_id}")
        print(f"  Duration: {stats['elapsed_time']:.1f} seconds")
        print(f"  Pixel hits: {stats['pixel_hits']}")
        print(f"  Calorimeter hits: {stats['calorimeter_hits']}")
        print(f"  Files:")
        print(f"    Pixel: {stats['files']['pixel']}")
        print(f"    Calorimeter: {stats['files']['calorimeter']}")


if __name__ == '__main__':
    # Simple test
    print("Testing Streaming DAQ Loggers")
    print("=" * 60)

    # Create manager
    manager = StreamingDAQManager(run_id="test_run_001")

    # Simulate some hits
    print("\nSimulating detector hits...")
    for i in range(10):
        # Pixel hit
        manager.log_pixel_hit(
            particle_id=i+1,
            pixel_number=i * 100,
            hit_time=i * 0.5,
            simulation_time=i * 0.5
        )

        # Calorimeter hit
        manager.log_calorimeter_hit(
            particle_id=i+1,
            segment_number=i % 64,
            hit_time=i * 0.5 + 0.1,
            particle_speed=0.5 + i * 0.05,
            deflection_angle=-135 + i * 27,
            simulation_time=i * 0.5 + 0.1
        )

    # Show statistics
    print("\nStatistics:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        if key != 'files':
            print(f"  {key}: {value}")

    # Close
    manager.close()

    print("\n" + "=" * 60)
    print("Test complete!")
