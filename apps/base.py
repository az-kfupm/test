"""Base application infrastructure for Table OS demo apps."""

from __future__ import annotations

import logging
from typing import Optional

from table_os.hardware_interface import BluetoothManager, MockConnection


class App:
    """Base class for demo applications.

    Applications can optionally receive a :class:`BluetoothManager` during
    initialisation.  When present, the app will be notified about companion
    device events through the :meth:`on_companion_connect` and
    :meth:`on_companion_disconnect` hooks.
    """

    def __init__(self, *, name: str, bluetooth: Optional[BluetoothManager] = None) -> None:
        self.name = name
        self.log = logging.getLogger(name)
        self._bluetooth = bluetooth
        if bluetooth is not None:
            bluetooth.on_connect(self._handle_companion_connect)
            bluetooth.on_disconnect(self._handle_companion_disconnect)

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    def on_start(self) -> None:
        """Called when the application starts running."""

    def on_stop(self) -> None:
        """Called when the application stops running."""

    # ------------------------------------------------------------------
    # Companion lifecycle hooks
    # ------------------------------------------------------------------
    def on_companion_connect(self, connection: MockConnection) -> None:
        """Invoked when a companion connects to the system.

        Subclasses may override the method to react to the connection event.
        The default implementation is a no-op.
        """

    def on_companion_disconnect(self, connection: MockConnection) -> None:
        """Invoked when a companion disconnects from the system.

        Subclasses may override the method to react to the disconnect event.
        The default implementation is a no-op.
        """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _handle_companion_connect(self, connection: MockConnection) -> None:
        try:
            self.on_companion_connect(connection)
        except Exception:  # pragma: no cover - defensive logging path
            self.log.exception("Unhandled error while processing companion connect event")

    def _handle_companion_disconnect(self, connection: MockConnection) -> None:
        try:
            self.on_companion_disconnect(connection)
        except Exception:  # pragma: no cover - defensive logging path
            self.log.exception("Unhandled error while processing companion disconnect event")

    @property
    def bluetooth(self) -> Optional[BluetoothManager]:
        """Expose the configured Bluetooth manager, if available."""

        return self._bluetooth
