"""Hardware abstractions for Table OS.

This module currently exposes a Bluetooth manager stub that mimics the
behaviour of a simple BLE stack.  The goal is to provide enough surface area
for application code to experiment with companion connectivity flows while the
real hardware layer is still under development.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

Logger = logging.getLogger(__name__)


@dataclass
class MockConnection:
    """Representation of a connection to a companion device.

    The class stores a `device_id` alongside optional metadata describing the
    mock companion.  In the future the structure can be expanded with richer
    state without affecting the public API.
    """

    device_id: str
    metadata: Optional[Dict[str, str]] = None


class BluetoothManager:
    """Tiny Bluetooth LE façade for development.

    The manager keeps track of advertised services and exposes helper methods
    to simulate the connection lifecycle.  Applications can register
    callbacks to react to mock connection and disconnection events, enabling a
    consistent testing experience without real hardware.
    """

    def __init__(self) -> None:
        self._advertised_services: Dict[str, Dict[str, str]] = {}
        self._connection_callbacks: List[Callable[[MockConnection], None]] = []
        self._disconnection_callbacks: List[Callable[[MockConnection], None]] = []
        self._active_connection: Optional[MockConnection] = None

    # ------------------------------------------------------------------
    # Service advertisement helpers
    # ------------------------------------------------------------------
    def advertise_service(self, service_name: str, *, metadata: Optional[Dict[str, str]] = None) -> None:
        """Register a service that should appear in advertisements.

        Parameters
        ----------
        service_name:
            Human readable identifier for the advertised service.
        metadata:
            Optional dictionary with additional information (such as UUIDs or
            versioning details) that higher level tests may inspect.
        """

        Logger.debug("Advertising service '%s' with metadata: %s", service_name, metadata)
        self._advertised_services[service_name] = metadata or {}

    def stop_advertising(self, service_name: Optional[str] = None) -> None:
        """Stop advertising either a specific service or all services."""

        if service_name is None:
            Logger.debug("Clearing all advertised services")
            self._advertised_services.clear()
            return

        Logger.debug("Stopping advertisement for service '%s'", service_name)
        self._advertised_services.pop(service_name, None)

    # ------------------------------------------------------------------
    # Listener registration
    # ------------------------------------------------------------------
    def on_connect(self, callback: Callable[[MockConnection], None]) -> None:
        """Register a callback triggered when a companion connects."""

        self._connection_callbacks.append(callback)

    def on_disconnect(self, callback: Callable[[MockConnection], None]) -> None:
        """Register a callback triggered when a companion disconnects."""

        self._disconnection_callbacks.append(callback)

    # ------------------------------------------------------------------
    # Mock lifecycle controls
    # ------------------------------------------------------------------
    def connect_mock(self, *, device_id: str = "mock-companion", metadata: Optional[Dict[str, str]] = None) -> MockConnection:
        """Simulate an incoming connection from a companion device.

        The method raises a :class:`RuntimeError` if no service is advertised –
        mirroring the expectation that a real device would not discover the
        host.  Successful connections are broadcast to registered listeners.
        """

        if not self._advertised_services:
            raise RuntimeError("Cannot connect without advertising at least one service")

        connection = MockConnection(device_id=device_id, metadata=metadata)
        Logger.info("Mock companion '%s' connected", device_id)
        self._active_connection = connection
        for callback in list(self._connection_callbacks):
            callback(connection)
        return connection

    def disconnect_mock(self) -> None:
        """Simulate the active companion disconnecting."""

        if not self._active_connection:
            Logger.debug("disconnect_mock() called without an active connection")
            return

        Logger.info("Mock companion '%s' disconnected", self._active_connection.device_id)
        connection = self._active_connection
        self._active_connection = None
        for callback in list(self._disconnection_callbacks):
            callback(connection)

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    @property
    def advertised_services(self) -> Dict[str, Dict[str, str]]:
        """Expose a copy of the advertised services for diagnostics."""

        return dict(self._advertised_services)

    @property
    def active_connection(self) -> Optional[MockConnection]:
        """Return the currently active mock connection, if any."""

        return self._active_connection
