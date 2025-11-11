# Table OS Applications

This directory contains sample applications built on top of the experimental
Table OS runtime.

## Companion connectivity hooks

Apps that need to react to events from a companion device (for example a
mobile phone running a pairing experience) can rely on the optional hooks
exposed by the :class:`App` base class:

- `on_companion_connect(connection: MockConnection)`
- `on_companion_disconnect(connection: MockConnection)`

Both hooks receive a :class:`MockConnection` instance describing the mock
companion managed by :class:`table_os.hardware_interface.BluetoothManager`.

To use the hooks:

1. Request an instance of :class:`BluetoothManager` when constructing your app.
2. Advertise at least one service via `advertise_service()`.
3. Override the hooks of interest and implement any domain-specific logic.

```python
from apps.base import App
from table_os.hardware_interface import BluetoothManager, MockConnection


class MediaPlayer(App):
    def __init__(self, bluetooth: BluetoothManager) -> None:
        super().__init__(name="MediaPlayer", bluetooth=bluetooth)
        bluetooth.advertise_service("media-control", metadata={"version": "1"})

    def on_companion_connect(self, connection: MockConnection) -> None:
        self.log.info("Companion %s connected", connection.device_id)
        # Perform handshake or synchronise state here.

    def on_companion_disconnect(self, connection: MockConnection) -> None:
        self.log.info("Companion %s disconnected", connection.device_id)
        # Tear down any session state if needed.
```

The hooks are optional – if your app does not override them nothing happens.
This allows existing applications to remain unchanged while progressively
adopting companion-aware features.
