#!/usr/bin/env python3
"""
Bluesky integration for Particle Collider Simulation

Provides ophyd Device classes to control the particle collider via XML-RPC
and integrate with Bluesky data acquisition framework.
"""

import xmlrpc.client
import time
from ophyd import Device, Signal, Component as Cpt
from ophyd.status import Status
import threading


class XMLRPCSignal(Signal):
    """
    Base class for signals that communicate via XML-RPC

    This provides a thread-safe Signal implementation that uses
    XML-RPC to get/set values on the remote particle collider.
    """

    def __init__(self, rpc_proxy, get_method=None, set_method=None, *args, **kwargs):
        """
        Parameters
        ----------
        rpc_proxy : xmlrpc.client.ServerProxy
            The XML-RPC proxy object
        get_method : str, optional
            Name of the RPC method to call for reading (e.g., 'get_status')
        set_method : str, optional
            Name of the RPC method to call for setting (e.g., 'set_speed_min')
        """
        super().__init__(*args, **kwargs)
        self._rpc_proxy = rpc_proxy
        self._get_method = get_method
        self._set_method = set_method
        self._readback_key = None  # Key to extract from get_status() response

    def get(self):
        """Read the current value via XML-RPC"""
        if self._get_method is None:
            return self._readback

        try:
            if self._get_method == 'get_status':
                status = self._rpc_proxy.get_status()
                if self._readback_key:
                    return status[self._readback_key]
                return status
            else:
                method = getattr(self._rpc_proxy, self._get_method)
                return method()
        except Exception as e:
            print(f"Error reading {self.name}: {e}")
            return self._readback

    def put(self, value, **kwargs):
        """Set a new value via XML-RPC"""
        if self._set_method is None:
            # Read-only signal
            self._readback = value
            return

        try:
            method = getattr(self._rpc_proxy, self._set_method)
            result = method(float(value))

            if result.get('success'):
                self._readback = result.get('value', value)
            else:
                print(f"Failed to set {self.name} to {value}")

        except Exception as e:
            print(f"Error setting {self.name} to {value}: {e}")


class ColliderControlSignal(XMLRPCSignal):
    """Signal for controllable parameters (speed, interval ranges)"""

    def __init__(self, rpc_proxy, param_name, set_method, *args, **kwargs):
        """
        Parameters
        ----------
        rpc_proxy : xmlrpc.client.ServerProxy
            The XML-RPC proxy object
        param_name : str
            Key name in get_status() response (e.g., 'speed_min')
        set_method : str
            Name of the RPC method to call for setting
        """
        super().__init__(rpc_proxy, get_method='get_status', set_method=set_method,
                        *args, **kwargs)
        self._readback_key = param_name


class ColliderReadbackSignal(XMLRPCSignal):
    """Signal for read-only measurements (time, particle counts)"""

    def __init__(self, rpc_proxy, readback_key, *args, **kwargs):
        """
        Parameters
        ----------
        rpc_proxy : xmlrpc.client.ServerProxy
            The XML-RPC proxy object
        readback_key : str
            Key name in get_status() response (e.g., 'time_elapsed')
        """
        super().__init__(rpc_proxy, get_method='get_status', set_method=None,
                        *args, **kwargs)
        self._readback_key = readback_key
        self.kind = 'hinted'  # Include in primary data stream


class ParticleColliderDevice(Device):
    """
    Ophyd Device for the Particle Collider Simulation

    This device provides Bluesky-compatible control and monitoring
    of the particle collider via its XML-RPC interface.

    Control Parameters (settable):
    - speed_min, speed_max: Particle speed range [0.1, 1.5]
    - interval_min, interval_max: Injection interval range [0.1, 2.0] seconds

    Measurements (read-only):
    - time_elapsed: Simulation time in seconds
    - active_particles: Number of currently active particles
    - total_particles: Total number of particles created
    """

    # Components will be created dynamically in __init__
    # to use custom XML-RPC backed signals

    def __init__(self, rpc_url='http://localhost:8000/', *args, **kwargs):
        """
        Parameters
        ----------
        rpc_url : str
            URL of the XML-RPC server (default: http://localhost:8000/)
        """
        super().__init__(*args, **kwargs)

        # Connect to XML-RPC server
        self._rpc_proxy = xmlrpc.client.ServerProxy(rpc_url)

        # Replace Signal components with XML-RPC backed signals
        self._setup_signals()

        # Verify connection
        self._verify_connection()

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
        but those are NOT recorded in Bluesky - they're saved
        separately by the simulation.
        """
        try:
            return self._rpc_proxy.get_statistics()
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}


def create_collider_device(name='collider', rpc_url='http://localhost:8000/'):
    """
    Convenience function to create a ParticleColliderDevice

    Parameters
    ----------
    name : str
        Device name (default: 'collider')
    rpc_url : str
        URL of the XML-RPC server (default: http://localhost:8000/)

    Returns
    -------
    ParticleColliderDevice
        Configured device ready for use with Bluesky
    """
    device = ParticleColliderDevice(rpc_url=rpc_url, name=name)
    return device


if __name__ == '__main__':
    # Simple test of the device
    print("Testing Particle Collider Bluesky Device")
    print("=" * 60)

    # Create device
    collider = create_collider_device()

    print("\nReading initial values...")
    print(f"Speed range: {collider.speed_min.get():.2f} - {collider.speed_max.get():.2f}")
    print(f"Interval range: {collider.interval_min.get():.2f} - {collider.interval_max.get():.2f}")
    print(f"Time elapsed: {collider.time_elapsed.get():.1f}s")
    print(f"Active particles: {collider.active_particles.get()}")
    print(f"Total particles: {collider.total_particles.get()}")

    print("\nSetting new speed range...")
    collider.speed_min.put(0.6)
    collider.speed_max.put(1.2)
    time.sleep(0.1)

    print(f"New speed range: {collider.speed_min.get():.2f} - {collider.speed_max.get():.2f}")

    print("\n" + "=" * 60)
    print("Device test complete!")
    print("\nTo use with Bluesky:")
    print("  from bluesky import RunEngine")
    print("  from bluesky.plans import count, scan")
    print("  RE = RunEngine({})")
    print("  RE(count([collider], num=10, delay=1))")
