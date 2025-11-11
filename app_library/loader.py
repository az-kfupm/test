"""Helpers for discovering and launching applications."""
from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .base import App

_BASE_DIR = Path(__file__).resolve().parent.parent
_GLOBAL_MANIFEST_PATH = _BASE_DIR / "apps" / "manifest.json"


def load_global_manifest(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the global manifest as a dictionary."""

    manifest_path = Path(path) if path else _GLOBAL_MANIFEST_PATH
    with manifest_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def list_apps(manifest: Optional[Dict[str, Any]] = None) -> Iterable[Dict[str, Any]]:
    """Return the list of registered applications."""

    data = manifest or load_global_manifest()
    return data.get("apps", [])


def get_app_entry(app_id: str, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return the manifest entry for *app_id* or raise :class:`KeyError`."""

    for entry in list_apps(manifest):
        if entry.get("id") == app_id:
            return entry
    raise KeyError(f"No app with id '{app_id}' found in manifest.")


def load_app_class(entry_point: str):
    """Load the application class referenced by the ``module:Class`` entry point."""

    module_name, class_name = entry_point.split(":", 1)
    module = import_module(module_name)
    return getattr(module, class_name)


def create_app(app_id: str) -> App:
    """Instantiate the application registered under *app_id*."""

    entry = get_app_entry(app_id)
    app_cls = load_app_class(entry["entry_point"])
    app = app_cls()
    if not isinstance(app, App):
        raise TypeError(
            f"Application '{app_id}' is expected to inherit from App; got {type(app).__name__}"
        )
    return app


def launch_app(app_id: str, *, start: bool = True) -> App:
    """Instantiate and optionally start the application registered under *app_id*."""

    app = create_app(app_id)
    if start:
        app.start()
    return app
