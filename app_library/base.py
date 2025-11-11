"""Base classes for application plugins."""
from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock


class App(ABC):
    """Abstract base class for interactive applications.

    Subclasses are expected to override :meth:`start` and :meth:`stop` to
    manage any resources they allocate. The base implementation keeps track of
    whether the application is currently running and provides context-manager
    helpers so apps can be used with ``with`` statements.
    """

    def __init__(self) -> None:
        self._running = False
        self._state_lock = RLock()

    @property
    def running(self) -> bool:
        """Return ``True`` while the application is running."""

        with self._state_lock:
            return self._running

    def _mark_running(self) -> None:
        with self._state_lock:
            self._running = True

    def _mark_stopped(self) -> None:
        with self._state_lock:
            self._running = False

    @abstractmethod
    def start(self) -> None:
        """Start the application."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the application and free any acquired resources."""

    def __enter__(self) -> "App":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()
