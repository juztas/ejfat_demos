#!/usr/bin/env python3
"""
Bluesky Streaming DAQ Integration for Particle Collider

Provides an ophyd Device with Resource/Datum document support for streaming
detector data to disk during Bluesky runs. Uses the Resource/Datum model
to link external DAQ files to Bluesky's document stream.
"""

import xmlrpc.client
import time
import uuid
from pathlib import Path
from ophyd import Device, Signal, Component as Cpt
from ophyd.status import Status
import threading

# Import base classes from existing integration
from bluesky_collider import XMLRPCSignal, ColliderControlSignal, ColliderReadbackSignal


class StreamingColliderDevice(Device):
    """
    Ophyd Device for Particle Collider with streaming DAQ support

    This device extends the basic ParticleColliderDevice with:
    - Automatic DAQ file creation on staging (start of run)
    - Resource/Datum document emission for external data files
    - Separate data streams for pixel detector and calorimeter
    - Timestamped data for joining streams in analysis

    Control Parameters (settable):
    - speed_min, speed_max: Particle speed range [0.1, 1.5]
    - interval_min, interval_max: Injection interval range [0.1, 2.0] seconds

    Measurements (read-only):
    - time_elapsed: Simulation time in seconds
    - active_particles: Number of currently active particles
    - total_particles: Total number of particles created

    Streaming DAQ:
    - Pixel detector hits → CSV file
    - Calorimeter hits → CSV file
    - Both files timestamped for joining
    """

    def __init__(self, rpc_url='http://localhost:8000/', data_dir='.', *args, **kwargs):
        """
        Parameters
        ----------
        rpc_url : str
            URL of the XML-RPC server (default: http://localhost:8000/)
        data_dir : str
            Directory for DAQ data files (default: current directory)
        """
        super().__init__(*args, **kwargs)

        # Connect to XML-RPC server
        self._rpc_proxy = xmlrpc.client.ServerProxy(rpc_url)
        self.data_dir = Path(data_dir).absolute()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Replace Signal components with XML-RPC backed signals
        self._setup_signals()

        # Verify connection
        self._verify_connection()

        # Resource/Datum tracking
        self._resource_uids = {}  # {'pixel': uid, 'calorimeter': uid}
        self._datum_uids = {}     # {'pixel': uid, 'calorimeter': uid}
        self._asset_docs_cache = []  # Cache for resource/datum documents
        self._run_id = None
        self._file_paths = {}

    def _setup_signals(self):
        """Create XML-RPC backed signals as attributes"""
        # Control signals (read/write)
        object.__setattr__(self, 'speed_min', ColliderControlSignal(
            self._rpc_proxy, 'speed_min', 'set_speed_min',
            name='speed_min', parent=self
        ))
        self.speed_min.kind = 'config'

        object.__setattr__(self, 'speed_max', ColliderControlSignal(
            self._rpc_proxy, 'speed_max', 'set_speed_max',
            name='speed_max', parent=self
        ))
        self.speed_max.kind = 'config'

        object.__setattr__(self, 'interval_min', ColliderControlSignal(
            self._rpc_proxy, 'interval_min', 'set_interval_min',
            name='interval_min', parent=self
        ))
        self.interval_min.kind = 'config'

        object.__setattr__(self, 'interval_max', ColliderControlSignal(
            self._rpc_proxy, 'interval_max', 'set_interval_max',
            name='interval_max', parent=self
        ))
        self.interval_max.kind = 'config'

        # Readback signals (read-only)
        object.__setattr__(self, 'time_elapsed', ColliderReadbackSignal(
            self._rpc_proxy, 'time_elapsed',
            name='time_elapsed', parent=self
        ))
        self.time_elapsed.kind = 'hinted'

        object.__setattr__(self, 'active_particles', ColliderReadbackSignal(
            self._rpc_proxy, 'active_particles',
            name='active_particles', parent=self
        ))
        self.active_particles.kind = 'hinted'

        object.__setattr__(self, 'total_particles', ColliderReadbackSignal(
            self._rpc_proxy, 'particle_count',  # Note: XML-RPC uses 'particle_count'
            name='total_particles', parent=self
        ))
        self.total_particles.kind = 'hinted'

    def _verify_connection(self):
        """Verify XML-RPC connection is working"""
        try:
            status = self._rpc_proxy.get_status()
            print(f"Connected to particle collider at {self._rpc_proxy._ServerProxy__host}")
            print(f"Current status: {status['particle_count']} particles, "
                  f"{'PAUSED' if status['paused'] else 'RUNNING'}")
        except Exception as e:
            print(f"WARNING: Could not connect to particle collider: {e}")
            print("Make sure the simulation is running!")

    def stage(self):
        """
        Stage the device (called at start of run)

        This:
        1. Generates a unique run ID
        2. Starts streaming DAQ on the simulator
        3. Creates Resource documents for pixel and calorimeter data files
        4. Caches these documents for emission during collection
        """
        super().stage()

        # Generate unique run ID
        self._run_id = str(uuid.uuid4())[:8]  # Short UID for filenames

        print(f"\n[Bluesky] Staging device for run: {self._run_id}")

        try:
            # Start DAQ run on simulator
            result = self._rpc_proxy.start_daq_run(self._run_id, str(self.data_dir))

            if not result['success']:
                raise RuntimeError(f"Failed to start DAQ run: {result.get('error')}")

            self._file_paths = result['files']

            print(f"[Bluesky] DAQ files created:")
            print(f"  Pixel: {self._file_paths['pixel']}")
            print(f"  Calorimeter: {self._file_paths['calorimeter']}")

            # Create Resource documents for each data file
            self._asset_docs_cache = []

            # Pixel detector resource
            pixel_resource_uid = str(uuid.uuid4())
            self._resource_uids['pixel'] = pixel_resource_uid

            pixel_resource = {
                'spec': 'CSV',
                'root': str(self.data_dir),
                'resource_path': Path(self._file_paths['pixel']).name,
                'resource_kwargs': {},
                'path_semantics': 'posix',
                'uid': pixel_resource_uid
            }
            self._asset_docs_cache.append(('resource', pixel_resource))

            # Calorimeter resource
            calo_resource_uid = str(uuid.uuid4())
            self._resource_uids['calorimeter'] = calo_resource_uid

            calo_resource = {
                'spec': 'CSV',
                'root': str(self.data_dir),
                'resource_path': Path(self._file_paths['calorimeter']).name,
                'resource_kwargs': {},
                'path_semantics': 'posix',
                'uid': calo_resource_uid
            }
            self._asset_docs_cache.append(('resource', calo_resource))

            print(f"[Bluesky] Resource documents created")

        except Exception as e:
            print(f"Error during staging: {e}")
            raise

        return [self]

    def unstage(self):
        """
        Unstage the device (called at end of run)

        This:
        1. Stops streaming DAQ on the simulator
        2. Closes data files
        3. Prints statistics
        """
        print(f"\n[Bluesky] Unstaging device for run: {self._run_id}")

        try:
            # Stop DAQ run on simulator
            result = self._rpc_proxy.stop_daq_run()

            if result['success']:
                stats = result['statistics']
                print(f"[Bluesky] DAQ run completed:")
                print(f"  Pixel hits: {stats['pixel_hits']}")
                print(f"  Calorimeter hits: {stats['calorimeter_hits']}")
                print(f"  Duration: {stats['elapsed_time']:.1f}s")
            else:
                print(f"Warning: Error stopping DAQ run: {result.get('error')}")

        except Exception as e:
            print(f"Error during unstaging: {e}")

        # Clear run state
        self._run_id = None
        self._file_paths = {}
        self._resource_uids = {}
        self._datum_uids = {}

        super().unstage()
        return [self]

    def describe_collect(self):
        """
        Describe the data that collect() will return

        This tells Bluesky that we have external data referenced by datum IDs.
        """
        return {
            self.name: {
                'pixel_data': {
                    'source': 'file',
                    'dtype': 'string',
                    'shape': [],
                    'external': 'FILESTORE:'
                },
                'calorimeter_data': {
                    'source': 'file',
                    'dtype': 'string',
                    'shape': [],
                    'external': 'FILESTORE:'
                }
            }
        }

    def collect(self):
        """
        Collect data and emit Datum documents

        This is called at the end of the run to emit:
        1. Datum documents pointing to specific data within the files
        2. Event documents with references to those datums
        """
        # Create Datum documents for pixel and calorimeter data
        pixel_datum_uid = str(uuid.uuid4())
        self._datum_uids['pixel'] = pixel_datum_uid

        pixel_datum = {
            'resource': self._resource_uids['pixel'],
            'datum_id': pixel_datum_uid,
            'datum_kwargs': {}
        }
        self._asset_docs_cache.append(('datum', pixel_datum))

        calo_datum_uid = str(uuid.uuid4())
        self._datum_uids['calorimeter'] = calo_datum_uid

        calo_datum = {
            'resource': self._resource_uids['calorimeter'],
            'datum_id': calo_datum_uid,
            'datum_kwargs': {}
        }
        self._asset_docs_cache.append(('datum', calo_datum))

        # Yield event with references to external data
        yield {
            'data': {
                'pixel_data': pixel_datum_uid,
                'calorimeter_data': calo_datum_uid
            },
            'timestamps': {
                'pixel_data': time.time(),
                'calorimeter_data': time.time()
            },
            'time': time.time(),
            'filled': {}
        }

    def collect_asset_docs(self):
        """
        Yield cached Resource and Datum documents

        This is called by Bluesky to retrieve the Resource/Datum documents
        that were created during staging and collection.
        """
        for doc in self._asset_docs_cache:
            yield doc

        # Clear cache after emission
        self._asset_docs_cache = []

    def pause(self):
        """Pause the simulation"""
        try:
            result = self._rpc_proxy.pause()
            print(f"Simulation paused: {result}")
            return result
        except Exception as e:
            print(f"Error pausing simulation: {e}")
            return {'success': False, 'error': str(e)}

    def resume(self):
        """Resume the simulation"""
        try:
            result = self._rpc_proxy.resume()
            print(f"Simulation resumed: {result}")
            return result
        except Exception as e:
            print(f"Error resuming simulation: {e}")
            return {'success': False, 'error': str(e)}

    def reset(self):
        """Reset the simulation"""
        try:
            result = self._rpc_proxy.reset()
            print(f"Simulation reset: {result}")
            return result
        except Exception as e:
            print(f"Error resetting simulation: {e}")
            return {'success': False, 'error': str(e)}

    def get_statistics(self):
        """
        Get detailed statistics from the simulation

        Note: This includes calorimeter and pixel detector data,
        which are also saved to the streaming DAQ files.
        """
        try:
            return self._rpc_proxy.get_statistics()
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}


def create_streaming_collider_device(name='collider', rpc_url='http://localhost:8000/',
                                     data_dir='.'):
    """
    Convenience function to create a StreamingColliderDevice

    Parameters
    ----------
    name : str
        Device name (default: 'collider')
    rpc_url : str
        URL of the XML-RPC server (default: http://localhost:8000/)
    data_dir : str
        Directory for DAQ data files (default: current directory)

    Returns
    -------
    StreamingColliderDevice
        Configured device ready for use with Bluesky
    """
    device = StreamingColliderDevice(rpc_url=rpc_url, data_dir=data_dir, name=name)
    return device


if __name__ == '__main__':
    # Simple test of the device
    print("Testing Streaming Particle Collider Bluesky Device")
    print("=" * 60)

    # Create device
    collider = create_streaming_collider_device(data_dir='./test_daq_data')

    print("\nReading initial values...")
    print(f"Speed range: {collider.speed_min.get():.2f} - {collider.speed_max.get():.2f}")
    print(f"Interval range: {collider.interval_min.get():.2f} - {collider.interval_max.get():.2f}")
    print(f"Time elapsed: {collider.time_elapsed.get():.1f}s")
    print(f"Active particles: {collider.active_particles.get()}")
    print(f"Total particles: {collider.total_particles.get()}")

    print("\nTesting staging (start of run)...")
    collider.stage()

    print("\nWaiting 5 seconds for data collection...")
    time.sleep(5)

    print("\nTesting unstaging (end of run)...")
    collider.unstage()

    print("\n" + "=" * 60)
    print("Device test complete!")
    print("\nTo use with Bluesky:")
    print("  from bluesky import RunEngine")
    print("  from bluesky.plans import count")
    print("  RE = RunEngine({})")
    print("  RE(count([collider], num=1))")
