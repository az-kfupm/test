"""Virtual clock demonstration application."""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Optional

from .base import App
from table_os.hardware_interface import BluetoothManager, MockConnection


class VirtualClockApp(App):
    """Simple app that exposes the current time.

    The class purposefully keeps its business logic small – a `now()` helper
    returning the current UTC time – so it can focus on demonstrating how apps
    can respond to companion connectivity hooks provided by :class:`App`.
    """

    def __init__(self, *, bluetooth: Optional[BluetoothManager] = None) -> None:
        super().__init__(name="VirtualClock", bluetooth=bluetooth)
        self._log = logging.getLogger("VirtualClock")

    def now(self) -> _dt.datetime:
        """Return the current UTC time."""

        return _dt.datetime.now(tz=_dt.timezone.utc)

    # ------------------------------------------------------------------
    # Companion lifecycle hooks
    # ------------------------------------------------------------------
    def on_companion_connect(self, connection: MockConnection) -> None:
        self._log.info("Companion '%s' connected", connection.device_id)

    def on_companion_disconnect(self, connection: MockConnection) -> None:
        self._log.info("Companion '%s' disconnected", connection.device_id)
