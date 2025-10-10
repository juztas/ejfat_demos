"""
Ophyd Device Wrappers for FM Shared Memory Beamline

This module provides Bluesky-compatible device wrappers for the FM transmitter
and receiver GNU Radio flowgraphs that communicate via EJFAT shared memory.

Device Hierarchy:
    FMSHMBeamline (composite)
    ├── transmitter (FMTransmitterSHM)
    │   ├── frequency
    │   ├── sample_rate
    │   └── rf_power
    ├── receiver (FMReceiverSHM)
    │   ├── volume
    │   ├── audio_rate
    │   └── audio_power
    └── buffer (SHMMonitor)
        ├── buffer_fill
        ├── data_rate
        ├── overruns
        └── underruns
"""

import xmlrpc.client
import time
import subprocess
import sys
import signal as sig
from pathlib import Path

from ophyd import Device, Component as Cpt, Signal
from ophyd import DeviceStatus

from .fm_beamline_config import (
    FM_TX_FLOWGRAPH,
    FM_RX_FLOWGRAPH,
    XMLRPC_CONFIG,
    DEVICE_DEFAULTS,
    SHM_CONFIG,
)


class XMLRPCSignal(Signal):
    """
    Custom Signal subclass that communicates via XML-RPC.

    This signal wrapper allows Bluesky to control GNU Radio flowgraph
    variables through XML-RPC get/set methods.
    """

    def __init__(self, rpc_client, getter_name, setter_name, **kwargs):
        """
        Parameters
        ----------
        rpc_client : xmlrpc.client.ServerProxy
            XML-RPC client connection
        getter_name : str
            Name of the getter method (e.g., 'get_freq')
        setter_name : str
            Name of the setter method (e.g., 'set_freq')
        """
        super().__init__(**kwargs)
        self._rpc_client = rpc_client
        self._getter_name = getter_name
        self._setter_name = setter_name

    def put(self, value, **kwargs):
        """
        Set value via XML-RPC.

        Parameters
        ----------
        value : float
            Value to set

        Returns
        -------
        DeviceStatus
            Status object indicating completion
        """
        try:
            # Call setter
            setter = getattr(self._rpc_client, self._setter_name)
            setter(float(value))

            # Small delay for processing
            time.sleep(0.01)

            # Read back actual value
            getter = getattr(self._rpc_client, self._getter_name)
            self._readback = getter()

            # Update internal value
            return super().put(self._readback, **kwargs)

        except Exception as e:
            raise IOError(f"Failed to set value via XML-RPC: {e}")

    def get(self, **kwargs):
        """
        Get current value via XML-RPC.

        Returns
        -------
        float
            Current value
        """
        try:
            getter = getattr(self._rpc_client, self._getter_name)
            current_value = getter()
            self._readback = current_value
            return current_value
        except Exception as e:
            raise IOError(f"Failed to get value via XML-RPC: {e}")


class FMTransmitterSHM(Device):
    """
    Ophyd device for FM Transmitter with shared memory output.

    Controls the fm_transmitter_shm.py GNU Radio flowgraph which:
    - Captures FM signals from RTL-SDR
    - Applies low-pass filtering
    - Writes to EJFAT shared memory

    Controllable Parameters:
    - frequency: FM frequency to tune (88-108 MHz)

    Readable Signals:
    - sample_rate: Sample rate (read-only)
    - shm_name: Shared memory name (read-only)
    - rf_power: Measured RF power (future)
    """

    # Signals
    frequency = Cpt(Signal, value=DEVICE_DEFAULTS['tx_frequency'], kind='hinted')
    sample_rate = Cpt(Signal, value=2.4e6, kind='config')
    shm_name = Cpt(Signal, value=SHM_CONFIG['name'], kind='config')
    rf_power = Cpt(Signal, value=0.0, kind='hinted')

    def __init__(self, *args,
                 flowgraph_path=None,
                 xmlrpc_host=None,
                 xmlrpc_port=None,
                 autostart=False,
                 **kwargs):
        """
        Parameters
        ----------
        flowgraph_path : str or Path, optional
            Path to fm_transmitter_shm.py
            Default: from fm_beamline_config
        xmlrpc_host : str, optional
            XML-RPC server host
            Default: from XMLRPC_CONFIG
        xmlrpc_port : int, optional
            XML-RPC server port
            Default: from XMLRPC_CONFIG
        autostart : bool
            Automatically start flowgraph on init
        """
        # Configuration
        self._flowgraph_path = Path(flowgraph_path or FM_TX_FLOWGRAPH)
        self._xmlrpc_host = xmlrpc_host or XMLRPC_CONFIG['tx_host']
        self._xmlrpc_port = xmlrpc_port or XMLRPC_CONFIG['tx_port']
        self._timeout = XMLRPC_CONFIG['timeout']

        # Process management
        self._process = None
        self._rpc_client = None
        self._connected = False

        # Initialize Device
        super().__init__(*args, **kwargs)

        # Auto-start if requested
        if autostart:
            self.start_flowgraph()

    def start_flowgraph(self):
        """
        Launch the GNU Radio flowgraph in a subprocess.

        Returns
        -------
        bool
            True if started successfully
        """
        if self._process is not None:
            print(f"{self.name}: Flowgraph already running (PID {self._process.pid})")
            return True

        if not self._flowgraph_path.exists():
            raise FileNotFoundError(
                f"Flowgraph not found: {self._flowgraph_path}"
            )

        try:
            # Launch flowgraph
            print(f"{self.name}: Starting flowgraph: {self._flowgraph_path}")
            self._process = subprocess.Popen(
                [sys.executable, str(self._flowgraph_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for XML-RPC server to be ready
            print(f"{self.name}: Waiting for XML-RPC server...")
            self._connect_xmlrpc(max_retries=10, retry_delay=1.0)

            print(f"{self.name}: Flowgraph started successfully (PID {self._process.pid})")
            return True

        except Exception as e:
            print(f"{self.name}: Failed to start flowgraph: {e}")
            if self._process:
                self._process.terminate()
                self._process = None
            raise

    def stop_flowgraph(self):
        """
        Stop the GNU Radio flowgraph.

        Returns
        -------
        bool
            True if stopped successfully
        """
        if self._process is None:
            print(f"{self.name}: Flowgraph not running")
            return True

        try:
            print(f"{self.name}: Stopping flowgraph (PID {self._process.pid})")

            # Send SIGINT for graceful shutdown
            self._process.send_signal(sig.SIGINT)

            # Wait for process to terminate
            try:
                self._process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                print(f"{self.name}: Graceful shutdown timed out, forcing...")
                self._process.kill()
                self._process.wait()

            self._process = None
            self._rpc_client = None
            self._connected = False

            print(f"{self.name}: Flowgraph stopped")
            return True

        except Exception as e:
            print(f"{self.name}: Error stopping flowgraph: {e}")
            return False

    def _connect_xmlrpc(self, max_retries=10, retry_delay=1.0):
        """
        Connect to XML-RPC server with retries.

        Parameters
        ----------
        max_retries : int
            Maximum connection attempts
        retry_delay : float
            Delay between retries (seconds)
        """
        url = f'http://{self._xmlrpc_host}:{self._xmlrpc_port}'

        for attempt in range(max_retries):
            try:
                # Create client
                self._rpc_client = xmlrpc.client.ServerProxy(url)

                # Test connection by reading frequency
                current_freq = self._rpc_client.get_freq()

                self._connected = True
                print(f"{self.name}: Connected to XML-RPC at {url}")
                print(f"{self.name}: Current frequency: {current_freq/1e6:.1f} MHz")

                # Update frequency signal with XML-RPC wrapper
                self._setup_xmlrpc_signals()

                return

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise ConnectionError(
                        f"Failed to connect to XML-RPC server at {url} "
                        f"after {max_retries} attempts: {e}"
                    )

    def _setup_xmlrpc_signals(self):
        """Update frequency signal to use XML-RPC backend."""
        if not self._connected:
            return

        # Store RPC client reference for use in control methods
        # The frequency component remains as-is, we just use RPC in get/set methods
        current_freq = self._rpc_client.get_freq()
        self.frequency.put(current_freq)

    def set_frequency(self, value):
        """
        Set the FM frequency.

        Parameters
        ----------
        value : float
            Frequency in Hz

        Returns
        -------
        DeviceStatus
            Status object
        """
        if self._connected:
            # Use XML-RPC to set the frequency
            self._rpc_client.set_freq(float(value))
            time.sleep(0.01)  # Allow time for processing

            # Read back and update signal
            actual_freq = self._rpc_client.get_freq()
            self.frequency.put(actual_freq)

            # Create and return status
            status = DeviceStatus(self)
            status.set_finished()
            return status
        else:
            # No connection, just update the signal
            return self.frequency.set(value)

    def get_frequency(self):
        """
        Get current FM frequency.

        Returns
        -------
        float
            Frequency in Hz
        """
        if self._connected:
            # Read from XML-RPC server
            current_freq = self._rpc_client.get_freq()
            self.frequency.put(current_freq)
            return current_freq
        else:
            # Not connected, return signal value
            return self.frequency.get()

    @property
    def connected(self):
        """Check if connected to flowgraph XML-RPC server."""
        return self._connected

    @property
    def running(self):
        """Check if flowgraph process is running."""
        if self._process is None:
            return False
        return self._process.poll() is None

    def stage(self):
        """Stage the device (called by Bluesky before scan)."""
        super().stage()

        if not self.running:
            print(f"{self.name}: Starting flowgraph (auto-staged)")
            self.start_flowgraph()

        if self._connected:
            current_freq = self.get_frequency()
            print(f"{self.name}: Staged at {current_freq/1e6:.1f} MHz")

        return [self]

    def unstage(self):
        """Unstage the device (called by Bluesky after scan)."""
        super().unstage()
        return [self]


class FMReceiverSHM(Device):
    """
    Ophyd device for FM Receiver from shared memory.

    Controls the fm_receiver_shm.py GNU Radio flowgraph which:
    - Reads from EJFAT shared memory
    - Demodulates FM signal
    - Outputs to audio

    Controllable Parameters:
    - volume: Audio volume (0-10)

    Readable Signals:
    - audio_rate: Audio sample rate (read-only)
    - shm_name: Shared memory name (read-only)
    - audio_power: Measured audio power (future)
    """

    # Signals
    volume = Cpt(Signal, value=DEVICE_DEFAULTS['rx_volume'], kind='hinted')
    audio_rate = Cpt(Signal, value=48000, kind='config')
    shm_name = Cpt(Signal, value=SHM_CONFIG['name'], kind='config')
    audio_power = Cpt(Signal, value=0.0, kind='hinted')

    def __init__(self, *args,
                 flowgraph_path=None,
                 xmlrpc_host=None,
                 xmlrpc_port=None,
                 autostart=False,
                 **kwargs):
        """
        Parameters
        ----------
        flowgraph_path : str or Path, optional
            Path to fm_receiver_shm.py
        xmlrpc_host : str, optional
            XML-RPC server host
        xmlrpc_port : int, optional
            XML-RPC server port
        autostart : bool
            Automatically start flowgraph on init
        """
        # Configuration
        self._flowgraph_path = Path(flowgraph_path or FM_RX_FLOWGRAPH)
        self._xmlrpc_host = xmlrpc_host or XMLRPC_CONFIG['rx_host']
        self._xmlrpc_port = xmlrpc_port or XMLRPC_CONFIG['rx_port']

        # Process management
        self._process = None
        self._rpc_client = None
        self._connected = False

        # Initialize Device
        super().__init__(*args, **kwargs)

        # Auto-start if requested
        if autostart:
            self.start_flowgraph()

    def start_flowgraph(self):
        """Launch the GNU Radio flowgraph."""
        if self._process is not None:
            print(f"{self.name}: Flowgraph already running (PID {self._process.pid})")
            return True

        if not self._flowgraph_path.exists():
            raise FileNotFoundError(
                f"Flowgraph not found: {self._flowgraph_path}"
            )

        try:
            print(f"{self.name}: Starting flowgraph: {self._flowgraph_path}")
            self._process = subprocess.Popen(
                [sys.executable, str(self._flowgraph_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            print(f"{self.name}: Flowgraph started (PID {self._process.pid})")
            # Note: RX flowgraph may not have XML-RPC server currently
            return True

        except Exception as e:
            print(f"{self.name}: Failed to start flowgraph: {e}")
            if self._process:
                self._process.terminate()
                self._process = None
            raise

    def stop_flowgraph(self):
        """Stop the GNU Radio flowgraph."""
        if self._process is None:
            print(f"{self.name}: Flowgraph not running")
            return True

        try:
            print(f"{self.name}: Stopping flowgraph (PID {self._process.pid})")

            self._process.send_signal(sig.SIGINT)

            try:
                self._process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                print(f"{self.name}: Forcing termination...")
                self._process.kill()
                self._process.wait()

            self._process = None
            self._connected = False

            print(f"{self.name}: Flowgraph stopped")
            return True

        except Exception as e:
            print(f"{self.name}: Error stopping flowgraph: {e}")
            return False

    @property
    def running(self):
        """Check if flowgraph process is running."""
        if self._process is None:
            return False
        return self._process.poll() is None

    def stage(self):
        """Stage the device."""
        super().stage()

        if not self.running:
            print(f"{self.name}: Starting flowgraph (auto-staged)")
            self.start_flowgraph()

        return [self]

    def unstage(self):
        """Unstage the device."""
        super().unstage()
        return [self]


class SHMMonitor(Device):
    """
    Monitor EJFAT shared memory buffer health.

    Uses the ejfat_shm Python API to read buffer statistics
    and detect overruns/underruns.

    Signals:
    - buffer_fill: Percentage full (0-100)
    - data_rate: Data rate (samples/sec)
    - overruns: Total overrun count
    - underruns: Total underrun count
    """

    buffer_fill = Cpt(Signal, value=0.0, kind='hinted')
    data_rate = Cpt(Signal, value=0.0, kind='hinted')
    overruns = Cpt(Signal, value=0, kind='normal')
    underruns = Cpt(Signal, value=0, kind='normal')

    def __init__(self, *args, shm_name=None, **kwargs):
        """
        Parameters
        ----------
        shm_name : str, optional
            Shared memory segment name
        """
        self._shm_name = shm_name or SHM_CONFIG['name']
        super().__init__(*args, **kwargs)

    def trigger(self):
        """
        Read current buffer statistics.

        Returns
        -------
        DeviceStatus
            Status object indicating completion
        """
        # TODO: Implement actual SHM monitoring via ejfat_shm API
        # For now, return simulated values

        import random

        # Simulate buffer statistics
        fill = random.uniform(40, 60)
        rate = 2.4e6 + random.uniform(-1e5, 1e5)
        overruns = 0
        underruns = 0

        self.buffer_fill.put(fill)
        self.data_rate.put(rate)
        self.overruns.put(overruns)
        self.underruns.put(underruns)

        status = DeviceStatus(self)
        status.set_finished()

        return status

    def read(self):
        """Read the device signals."""
        return {
            f'{self.name}_buffer_fill': {
                'value': self.buffer_fill.get(),
                'timestamp': time.time(),
            },
            f'{self.name}_data_rate': {
                'value': self.data_rate.get(),
                'timestamp': time.time(),
            },
            f'{self.name}_overruns': {
                'value': self.overruns.get(),
                'timestamp': time.time(),
            },
            f'{self.name}_underruns': {
                'value': self.underruns.get(),
                'timestamp': time.time(),
            },
        }

    def describe(self):
        """Describe the device signals."""
        return {
            f'{self.name}_buffer_fill': {
                'source': 'ejfat_shm',
                'dtype': 'number',
                'shape': [],
                'units': '%',
            },
            f'{self.name}_data_rate': {
                'source': 'ejfat_shm',
                'dtype': 'number',
                'shape': [],
                'units': 'samples/s',
            },
            f'{self.name}_overruns': {
                'source': 'ejfat_shm',
                'dtype': 'integer',
                'shape': [],
                'units': 'count',
            },
            f'{self.name}_underruns': {
                'source': 'ejfat_shm',
                'dtype': 'integer',
                'shape': [],
                'units': 'count',
            },
        }


class FMSHMBeamline(Device):
    """
    Complete FM shared memory beamline.

    Combines transmitter, receiver, and buffer monitoring into a
    single composite device representing the complete beamline.

    Components:
    - transmitter: FMTransmitterSHM
    - receiver: FMReceiverSHM
    - buffer: SHMMonitor

    Example
    -------
    >>> beamline = FMSHMBeamline(name='fm_shm')
    >>> beamline.startup()
    >>> beamline.transmitter.set_frequency(98.5e6)
    >>> beamline.shutdown()
    """

    transmitter = Cpt(FMTransmitterSHM, name='fm_tx')
    receiver = Cpt(FMReceiverSHM, name='fm_rx')
    buffer = Cpt(SHMMonitor, name='shm_buffer')

    def startup(self, start_rx=True):
        """
        Start both transmitter and receiver flowgraphs.

        Parameters
        ----------
        start_rx : bool
            Whether to start receiver (default True)
            NOTE: This parameter is now ignored - both flowgraphs always start

        Returns
        -------
        bool
            True if startup successful
        """
        print("=" * 60)
        print("FM SHM Beamline Startup")
        print("=" * 60)

        try:
            # Start transmitter first (fills buffer)
            print("\n[1/2] Starting transmitter...")
            self.transmitter.start_flowgraph()

            # Always start receiver - wait for buffer to fill first
            print("\n[2/2] Waiting for buffer to fill (2 seconds)...")
            time.sleep(2.0)

            # Start receiver
            print("Starting receiver...")
            self.receiver.start_flowgraph()

            print("\n" + "=" * 60)
            print("Beamline startup complete!")
            print("  - Transmitter: Running")
            print("  - Receiver: Running")
            print("=" * 60)

            return True

        except Exception as e:
            print(f"\nERROR: Startup failed: {e}")
            self.shutdown()
            raise

    def shutdown(self):
        """
        Stop both transmitter and receiver flowgraphs.

        Returns
        -------
        bool
            True if shutdown successful
        """
        print("\n" + "=" * 60)
        print("FM SHM Beamline Shutdown")
        print("=" * 60)

        success = True

        # Stop receiver first
        print("\n[1/2] Stopping receiver...")
        if not self.receiver.stop_flowgraph():
            success = False

        # Stop transmitter
        print("\n[2/2] Stopping transmitter...")
        if not self.transmitter.stop_flowgraph():
            success = False

        print("\n" + "=" * 60)
        print("Beamline shutdown complete!")
        print("=" * 60)

        return success

    @property
    def ready(self):
        """Check if beamline is ready for operation."""
        return (self.transmitter.running and
                self.transmitter.connected)

    def __del__(self):
        """Cleanup on deletion."""
        try:
            if self.transmitter.running or self.receiver.running:
                self.shutdown()
        except:
            pass
