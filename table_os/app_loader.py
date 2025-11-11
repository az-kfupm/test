"""Utilities for loading Table OS applications from manifest files."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from collections.abc import Iterable
from typing import Dict, Iterator, List, Tuple

from .app_base import App, AppMetadata


def _optional_yaml_module():
    import importlib.util

    spec = importlib.util.find_spec("yaml")
    if spec is None:
        return None
    module = importlib.import_module("yaml")
    return module


class ManifestParser:
    """Parse application manifests that describe Table OS applications."""

    SUPPORTED_EXTENSIONS = {".json", ".yaml", ".yml"}

    def __init__(self) -> None:
        self._yaml = _optional_yaml_module()

    def discover(self, *locations: str | Path) -> Iterator[Path]:
        """Yield manifest file paths from the provided locations."""

        for location in locations:
            path = Path(location).expanduser().resolve()
            if path.is_file():
                if path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    yield path
                continue
            if path.is_dir():
                for candidate in path.rglob("*"):
                    if (
                        candidate.is_file()
                        and candidate.suffix.lower() in self.SUPPORTED_EXTENSIONS
                    ):
                        yield candidate

    def load_manifest(self, manifest_path: Path) -> Dict[str, object]:
        """Load raw manifest data from *manifest_path*."""

        suffix = manifest_path.suffix.lower()
        with manifest_path.open("r", encoding="utf-8") as handle:
            if suffix == ".json":
                return json.load(handle)
            if suffix in {".yaml", ".yml"}:
                if self._yaml is None:
                    raise RuntimeError(
                        "YAML manifest encountered but PyYAML is not installed."
                    )
                data = self._yaml.safe_load(handle)
                return data if data is not None else {}
        raise ValueError(f"Unsupported manifest type: {manifest_path}")

    def parse_metadata(self, manifest_path: Path) -> AppMetadata:
        """Parse :class:`AppMetadata` from a manifest file."""

        raw = self.load_manifest(manifest_path)
        if not isinstance(raw, dict):
            raise ValueError("Manifest must define a mapping at the top level.")

        def _require_string(value: object, field: str) -> str:
            if not isinstance(value, str):
                raise ValueError(f"Manifest field {field!r} must be a string.")
            trimmed = value.strip()
            if not trimmed:
                raise ValueError(f"Manifest field {field!r} cannot be empty.")
            return trimmed

        try:
            name = _require_string(raw.get("name"), "name")
            module = _require_string(raw.get("module"), "module")
        except ValueError as exc:
            raise ValueError(
                "Manifest requires 'name' and 'module' string fields."
            ) from exc

        class_value = raw.get("class", raw.get("class_name"))
        try:
            class_name = _require_string(class_value, "class")
        except ValueError as exc:
            raise ValueError(
                "Manifest requires 'class' or 'class_name' string field."
            ) from exc

        description = raw.get("description")
        icon = raw.get("icon")
        extra_keys = {"name", "module", "class", "class_name", "description", "icon"}
        extra = {key: value for key, value in raw.items() if key not in extra_keys}

        metadata = AppMetadata(
            name=name,
            module=module,
            class_name=class_name,
            description=description,
            icon=icon,
            extra=extra,
        )
        return metadata


class AppLoader:
    """Load and instantiate Table OS applications from manifests."""

    def __init__(self, parser: ManifestParser | None = None) -> None:
        self.parser = parser or ManifestParser()

    def load_metadata(
        self, *locations: Iterable[str | Path] | str | Path
    ) -> List[Tuple[AppMetadata, Path]]:
        """Discover and parse metadata from the provided manifest locations."""

        flattened: List[str | Path] = []
        for location in locations:
            if isinstance(location, (str, Path)):
                flattened.append(location)
            else:
                flattened.extend(list(location))

        manifests = list(self.parser.discover(*flattened))
        return [(self.parser.parse_metadata(manifest), manifest) for manifest in manifests]

    def instantiate(self, metadata: AppMetadata) -> App:
        """Instantiate the application described by *metadata*."""

        module = importlib.import_module(metadata.module)
        try:
            app_cls = getattr(module, metadata.class_name)
        except AttributeError as exc:  # pragma: no cover - defensive path
            raise AttributeError(
                f"Module {metadata.module!r} does not define {metadata.class_name!r}"
            ) from exc
        if not issubclass(app_cls, App):
            raise TypeError(
                f"Manifest class {metadata.class_name} in {metadata.module}"
                " is not a subclass of table_os.App"
            )

        init_kwargs = {}
        if isinstance(metadata.extra.get("init_kwargs"), dict):
            init_kwargs = dict(metadata.extra["init_kwargs"])
        app = app_cls(metadata=metadata, **init_kwargs)
        return app
