"""
Ophyd device definitions for GNU Radio and EJFAT experiments.

This module provides Bluesky-compatible device wrappers for:
- GNU Radio flowgraph control (via XML-RPC)
- Custom detectors and signal sources
- Future: EJFAT data sources
"""

import xmlrpc.client
import time
from ophyd import Device, Component as Cpt, Signal
from ophyd import DeviceStatus

# Import the XMLRPCSignal from widget directory
import sys
from pathlib import Path
widget_path = Path(__file__).parent.parent.parent / "widget"
sys.path.insert(0, str(widget_path))

try:
    from gnuradio_bluesky.gnuradio_device import XMLRPCSignal, GNURadioSignalGenerator
except ImportError:
    # Fallback: define XMLRPCSignal here if not available
    class XMLRPCSignal(Signal):
        """Custom Signal subclass that communicates via XML-RPC."""

        def __init__(self, rpc_client, getter_name, setter_name, **kwargs):
            super().__init__(**kwargs)
            self._rpc_client = rpc_client
            self._getter_name = getter_name
            self._setter_name = setter_name

        def put(self, value, **kwargs):
            """Override put to use XML-RPC."""
            try:
                setter = getattr(self._rpc_client, self._setter_name)
                setter(float(value))
                time.sleep(0.01)

                getter = getattr(self._rpc_client, self._getter_name)
                self._readback = getter()

                return super().put(self._readback, **kwargs)
            except Exception as e:
                raise IOError(f"Failed to set value via XML-RPC: {e}")

    class GNURadioSignalGenerator(Device):
        """Ophyd device for controlling a GNU Radio signal generator via XML-RPC."""

        def __init__(self, prefix='', *, host='localhost', port=8080, name=None,
                     timeout=5.0, **kwargs):
            self._host = host
            self._port = port
            self._timeout = timeout
            self._rpc_client = None
            self._connected = False

            self._connect()
            super().__init__(prefix, name=name, **kwargs)

            freq_signal = XMLRPCSignal(
                self._rpc_client,
                'get_frequency',
                'set_frequency',
                name=f'{name}_frequency',
                value=self._rpc_client.get_frequency(),
                kind='hinted'
            )
            freq_signal._parent = self
            self.frequency = freq_signal

        def _connect(self):
            """Establish connection to GNU Radio XML-RPC server."""
            try:
                url = f'http://{self._host}:{self._port}'
                self._rpc_client = xmlrpc.client.ServerProxy(url)
                current_freq = self._rpc_client.get_frequency()
                self._connected = True
                print(f"Connected to GNU Radio at {url}")
                print(f"Current frequency: {current_freq} Hz")
            except Exception as e:
                self._connected = False
                raise ConnectionError(
                    f"Failed to connect to GNU Radio XML-RPC server at "
                    f"{self._host}:{self._port}: {e}"
                )

        def set_frequency(self, value):
            """Set the signal generator frequency."""
            return self.frequency.set(value)

        def get_frequency(self):
            """Get the current signal generator frequency."""
            if not self._connected:
                raise ConnectionError("Not connected to GNU Radio XML-RPC server")
            try:
                return self._rpc_client.get_frequency()
            except Exception as e:
                raise IOError(f"Failed to get frequency: {e}")

        def stage(self):
            """Stage the device (called by Bluesky before a scan)."""
            super().stage()
            if self._connected:
                current_freq = self.get_frequency()
                self.frequency._readback = current_freq
                self.frequency._set_value(current_freq)
            return [self]

        def unstage(self):
            """Unstage the device (called by Bluesky after a scan)."""
            super().unstage()
            return [self]

        @property
        def connected(self):
            """Check if connected to GNU Radio XML-RPC server."""
            return self._connected

        def reconnect(self):
            """Reconnect to the GNU Radio XML-RPC server."""
            self._connect()


class FMTransmitter(GNURadioSignalGenerator):
    """
    Ophyd device for FM transmitter control.

    This extends GNURadioSignalGenerator to use get_freq/set_freq
    instead of get_frequency/set_frequency (FM transmitter naming convention).
    """

    def _connect(self):
        """Override to use FM transmitter's method names."""
        try:
            url = f'http://{self._host}:{self._port}'
            self._rpc_client = xmlrpc.client.ServerProxy(url)
            # Test with get_freq (FM transmitter uses this)
            current_freq = self._rpc_client.get_freq()
            self._connected = True
            print(f"Connected to FM transmitter at {url}")
            print(f"Current frequency: {current_freq/1e6:.1f} MHz")
        except Exception as e:
            self._connected = False
            raise ConnectionError(
                f"Failed to connect to FM transmitter at "
                f"{self._host}:{self._port}: {e}"
            )

    def __init__(self, *args, **kwargs):
        # Store parameters
        self._host = kwargs.get('host', 'localhost')
        self._port = kwargs.get('port', 8080)
        self._timeout = kwargs.get('timeout', 5.0)
        self._rpc_client = None
        self._connected = False

        # Connect first
        self._connect()

        # Initialize Device parent
        Device.__init__(self, '', name=kwargs.get('name', 'fm_tx'))

        # Create frequency signal with get_freq/set_freq
        freq_signal = XMLRPCSignal(
            self._rpc_client,
            'get_freq',
            'set_freq',
            name=f"{kwargs.get('name', 'fm_tx')}_frequency",
            value=self._rpc_client.get_freq(),
            kind='hinted'
        )
        freq_signal._parent = self
        self.frequency = freq_signal


class MockDetector(Device):
    """
    Mock detector for testing without hardware.

    Generates synthetic data based on current time or can be configured
    to return specific patterns.
    """

    value = Cpt(Signal, value=0, kind='hinted')

    def __init__(self, *args, noise_level=0.1, **kwargs):
        super().__init__(*args, **kwargs)
        self.noise_level = noise_level
        self._reading_counter = 0

    def trigger(self):
        """Simulate detector trigger."""
        import random

        # Generate synthetic reading
        base_value = 1.0
        noise = random.gauss(0, self.noise_level)
        reading = base_value + noise

        self.value.put(reading)
        self._reading_counter += 1

        status = DeviceStatus(self)
        status._finished()
        return status

    def read(self):
        """Read the detector."""
        return {
            f'{self.name}_value': {
                'value': self.value.get(),
                'timestamp': time.time(),
            }
        }

    def describe(self):
        """Describe the detector signals."""
        return {
            f'{self.name}_value': {
                'source': 'simulation',
                'dtype': 'number',
                'shape': [],
                'units': 'arb',
            }
        }


class PowerMeter(Device):
    """
    Simulated RF power meter device.

    In a real implementation, this would interface with actual
    power measurement hardware via EPICS, serial, or other protocol.
    """

    power = Cpt(Signal, value=0, kind='hinted')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._baseline_power = -50.0  # dBm

    def trigger(self):
        """Take a power measurement."""
        import random

        # Simulate power reading with some variation
        reading = self._baseline_power + random.gauss(0, 2.0)
        self.power.put(reading)

        status = DeviceStatus(self)
        status._finished()
        return status

    def read(self):
        """Read the power meter."""
        return {
            f'{self.name}_power': {
                'value': self.power.get(),
                'timestamp': time.time(),
            }
        }

    def describe(self):
        """Describe the power meter signals."""
        return {
            f'{self.name}_power': {
                'source': 'simulated_power_meter',
                'dtype': 'number',
                'shape': [],
                'units': 'dBm',
            }
        }


# Example of how to add more devices:
#
# class EJFATReassembler(Device):
#     """Ophyd device for EJFAT E2SAR reassembler control."""
#
#     buffer_level = Cpt(Signal, value=0, kind='hinted')
#     packet_rate = Cpt(Signal, value=0, kind='hinted')
#
#     def trigger(self):
#         """Trigger data collection."""
#         # Implementation here
#         pass
