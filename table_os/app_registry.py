"""Application registry for Table OS."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .app_base import App, AppMetadata
from .app_loader import AppLoader, ManifestParser


@dataclass
class RegisteredApp:
    """Container for registered application metadata."""

    metadata: AppMetadata
    manifest_path: Optional[Path] = None


class AppRegistry:
    """Registry that discovers, tracks, and launches Table OS applications."""

    def __init__(
        self,
        loader: AppLoader | None = None,
    ) -> None:
        self.loader = loader or AppLoader()
        self._registered: Dict[str, RegisteredApp] = {}
        self._running: Dict[str, App] = {}

    @property
    def parser(self) -> ManifestParser:
        """Shortcut to access the registry's manifest parser."""

        return self.loader.parser

    def discover(self, *locations: Iterable[str | Path] | str | Path) -> List[AppMetadata]:
        """Discover manifests and register their applications."""

        discovered = self.loader.load_metadata(*locations)
        metadata_items: List[AppMetadata] = []
        for metadata, manifest in discovered:
            self._registered[metadata.name] = RegisteredApp(metadata, manifest)
            metadata_items.append(metadata)
        return metadata_items

    def list_apps(self) -> List[AppMetadata]:
        """Return metadata for registered applications sorted by name."""

        return sorted((entry.metadata for entry in self._registered.values()), key=lambda m: m.name)

    def get_metadata(self, name: str) -> AppMetadata:
        """Return metadata for the application named *name*."""

        return self._registered[name].metadata

    def is_running(self, name: str) -> bool:
        """Return ``True`` if the application named *name* is running."""

        return name in self._running

    def launch(self, name: str) -> App:
        """Instantiate and start the application named *name*."""

        if name not in self._registered:
            raise KeyError(f"Application {name!r} is not registered")
        if name in self._running:
            return self._running[name]

        metadata = self._registered[name].metadata
        app = self.loader.instantiate(metadata)

        if metadata.extra.get("requires_bluetooth"):
            app.setup_bluetooth()
        if metadata.extra.get("requires_wifi"):
            app.setup_wifi()

        app.start()
        self._running[name] = app
        return app

    def stop(self, name: str) -> None:
        """Stop the running application named *name*."""

        app = self._running.pop(name, None)
        if app is not None:
            app.stop()

    def stop_all(self) -> None:
        """Stop all running applications."""

        for name in list(self._running):
            self.stop(name)
