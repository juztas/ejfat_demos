"""
Ophyd device wrapper for GNU Radio XML-RPC control.

This module provides a Bluesky-compatible device interface for controlling
GNU Radio flowgraphs via their XML-RPC server.
"""

import xmlrpc.client
from ophyd import Device, Component as Cpt, Signal
from ophyd import DeviceStatus
import time


class XMLRPCSignal(Signal):
    """
    Custom Signal subclass that communicates via XML-RPC.

    This signal overrides the put method to send values directly to
    a GNU Radio XML-RPC server instead of storing them locally.
    """

    def __init__(self, rpc_client, getter_name, setter_name, **kwargs):
        super().__init__(**kwargs)
        self._rpc_client = rpc_client
        self._getter_name = getter_name
        self._setter_name = setter_name

    def put(self, value, **kwargs):
        """Override put to use XML-RPC."""
        try:
            # Call the setter via XML-RPC
            setter = getattr(self._rpc_client, self._setter_name)
            setter(float(value))

            # Small delay to allow GNU Radio to update
            time.sleep(0.01)

            # Update internal readback value
            getter = getattr(self._rpc_client, self._getter_name)
            self._readback = getter()

            return super().put(self._readback, **kwargs)
        except Exception as e:
            raise IOError(f"Failed to set value via XML-RPC: {e}")


class GNURadioSignalGenerator(Device):
    """
    Ophyd device for controlling a GNU Radio signal generator via XML-RPC.

    This device wraps the XML-RPC interface provided by GNU Radio's
    xmlrpc_server block, allowing Bluesky plans to control signal
    generation parameters.

    Parameters
    ----------
    prefix : str
        Device prefix (not used for XML-RPC, but required by Ophyd)
    host : str, optional
        Hostname or IP address of GNU Radio XML-RPC server (default: 'localhost')
    port : int, optional
        Port number of GNU Radio XML-RPC server (default: 8080)
    name : str, optional
        Device name for Bluesky
    timeout : float, optional
        XML-RPC connection timeout in seconds (default: 5.0)

    Attributes
    ----------
    frequency : XMLRPCSignal
        Signal generator frequency in Hz

    Examples
    --------
    >>> # Create device and connect to GNU Radio
    >>> sig_gen = GNURadioSignalGenerator('', name='sig_gen', host='localhost', port=8080)
    >>>
    >>> # Read current frequency
    >>> print(sig_gen.frequency.get())
    >>>
    >>> # Set frequency
    >>> sig_gen.frequency.set(2500).wait()
    >>>
    >>> # Use in a Bluesky plan
    >>> from bluesky.plans import scan
    >>> RE(scan([], sig_gen.frequency, 100, 5000, 50))
    """

    def __init__(self, prefix='', *, host='localhost', port=8080, name=None, timeout=5.0, **kwargs):
        """Initialize the GNU Radio signal generator device."""
        self._host = host
        self._port = port
        self._timeout = timeout
        self._rpc_client = None
        self._connected = False

        # Connect to XML-RPC server first
        self._connect()

        # Now initialize the parent class
        super().__init__(prefix, name=name, **kwargs)

        # Create the frequency signal with XML-RPC backend
        # Set parent via _parent attribute (internal way) instead of the property
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

            # Test connection by reading current frequency
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
        """
        Set the signal generator frequency.

        Parameters
        ----------
        value : float
            Frequency in Hz

        Returns
        -------
        DeviceStatus
            Status object that completes when frequency is set

        Examples
        --------
        >>> sig_gen.set_frequency(1500)
        >>> status = sig_gen.set_frequency(2000)
        >>> status.wait()  # Wait for completion
        """
        return self.frequency.set(value)

    def get_frequency(self):
        """
        Get the current signal generator frequency.

        Returns
        -------
        float
            Current frequency in Hz

        Examples
        --------
        >>> freq = sig_gen.get_frequency()
        >>> print(f"Current frequency: {freq} Hz")
        """
        if not self._connected:
            raise ConnectionError("Not connected to GNU Radio XML-RPC server")

        try:
            return self._rpc_client.get_frequency()
        except Exception as e:
            raise IOError(f"Failed to get frequency: {e}")

    def stage(self):
        """
        Stage the device (called by Bluesky before a scan).

        Reads current frequency from GNU Radio and updates the local cache.
        """
        super().stage()
        if self._connected:
            current_freq = self.get_frequency()
            self.frequency._readback = current_freq
            # Also update the internal value
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


class GNURadioVariable(Device):
    """
    Generic Ophyd device for any GNU Radio variable exposed via XML-RPC.

    This is a more generic version that can control any variable in a
    GNU Radio flowgraph, not just frequency.

    Parameters
    ----------
    prefix : str
        Device prefix (not used for XML-RPC)
    variable_name : str
        Name of the GNU Radio variable to control
    initial_value : float, optional
        Initial value for the variable (default: 0)
    host : str, optional
        Hostname of GNU Radio XML-RPC server (default: 'localhost')
    port : int, optional
        Port of GNU Radio XML-RPC server (default: 8080)
    name : str, optional
        Device name for Bluesky

    Examples
    --------
    >>> # Control a custom GNU Radio variable
    >>> amplitude = GNURadioVariable('', variable_name='amplitude',
    ...                              initial_value=1.0, name='amplitude')
    >>> amplitude.value.set(0.5).wait()
    """

    value = Cpt(Signal, value=0, kind='hinted')

    def __init__(self, prefix='', *, variable_name, initial_value=0,
                 host='localhost', port=8080, name=None, **kwargs):
        """Initialize the GNU Radio variable device."""
        super().__init__(prefix, name=name, **kwargs)

        self._variable_name = variable_name
        self._host = host
        self._port = port

        # Connect to XML-RPC server
        url = f'http://{self._host}:{self._port}'
        self._rpc_client = xmlrpc.client.ServerProxy(url)

        # Set initial value
        self.value._readback = initial_value

        # Override the value signal's put method
        self.value._write_signal = self._set_value_rpc

    def _set_value_rpc(self, value):
        """Set variable value via XML-RPC."""
        try:
            # GNU Radio XML-RPC uses set_<variable_name> method
            setter_method = getattr(self._rpc_client, f'set_{self._variable_name}')
            setter_method(value)

            time.sleep(0.01)

            # Read back using get_<variable_name> method
            getter_method = getattr(self._rpc_client, f'get_{self._variable_name}')
            actual_value = getter_method()

            return actual_value

        except Exception as e:
            raise IOError(f"Failed to set {self._variable_name}: {e}")

    def get_value(self):
        """Get current variable value."""
        try:
            getter_method = getattr(self._rpc_client, f'get_{self._variable_name}')
            return getter_method()
        except Exception as e:
            raise IOError(f"Failed to get {self._variable_name}: {e}")
