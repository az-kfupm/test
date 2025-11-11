"""Base definition for Table OS applications."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(slots=True)
class AppMetadata:
    """Metadata describing an application that can run on Table OS."""

    name: str
    module: str
    class_name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


class App:
    """Base class for all Table OS applications.

    Subclasses should provide implementations for the :meth:`start` and
    :meth:`stop` lifecycle methods. The optional :meth:`setup_bluetooth`
    and :meth:`setup_wifi` hooks allow applications to prepare network
    connectivity as required.
    """

    metadata: AppMetadata

    def __init__(self, metadata: AppMetadata) -> None:
        self.metadata = metadata

    def setup_bluetooth(self) -> None:
        """Optional hook invoked before :meth:`start` for Bluetooth setup."""

    def setup_wifi(self) -> None:
        """Optional hook invoked before :meth:`start` for Wi-Fi setup."""

    def start(self) -> None:
        """Start the application."""
        raise NotImplementedError("Applications must implement start().")

    def stop(self) -> None:
        """Stop the application and clean up resources."""
        raise NotImplementedError("Applications must implement stop().")
