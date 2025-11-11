import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from table_os.app_loader import AppLoader, ManifestParser


def write_manifest(tmp_path: Path, data: dict) -> Path:
    manifest = tmp_path / "app.json"
    manifest.write_text(json.dumps(data))
    return manifest


def test_parse_metadata_requires_string_fields(tmp_path: Path) -> None:
    parser = ManifestParser()
    manifest = write_manifest(
        tmp_path,
        {"name": "Example", "module": None, "class": "ExampleApp"},
    )

    with pytest.raises(ValueError):
        parser.parse_metadata(manifest)


@pytest.mark.parametrize(
    "module_value",
    ["", "   "],
)
def test_parse_metadata_rejects_blank_strings(tmp_path: Path, module_value: str) -> None:
    parser = ManifestParser()
    manifest = write_manifest(
        tmp_path,
        {"name": "Example", "module": module_value, "class": "ExampleApp"},
    )

    with pytest.raises(ValueError):
        parser.parse_metadata(manifest)


def test_parse_metadata_strips_whitespace(tmp_path: Path) -> None:
    parser = ManifestParser()
    manifest = write_manifest(
        tmp_path,
        {"name": " Example ", "module": " apps.example ", "class": " ExampleApp "},
    )

    metadata = parser.parse_metadata(manifest)

    assert metadata.name == "Example"
    assert metadata.module == "apps.example"
    assert metadata.class_name == "ExampleApp"


def test_parse_metadata_supports_entry_point(tmp_path: Path) -> None:
    parser = ManifestParser()
    manifest = write_manifest(
        tmp_path,
        {
            "name": "Virtual Clock",
            "entry_point": " apps.virtual_clock.app:VirtualClockApp ",
        },
    )

    metadata = parser.parse_metadata(manifest)

    assert metadata.name == "Virtual Clock"
    assert metadata.module == "apps.virtual_clock.app"
    assert metadata.class_name == "VirtualClockApp"


def test_load_metadata_supports_aggregate_manifest(tmp_path: Path) -> None:
    app_dir = tmp_path / "apps"
    app_dir.mkdir()
    nested_manifest = app_dir / "virtual_clock.json"
    nested_manifest.write_text(
        json.dumps(
            {
                "name": "Old Name",
                "description": "Nested description",
                "capabilities": ["timekeeping"],
            }
        )
    )

    aggregate_manifest = app_dir / "manifest.json"
    aggregate_manifest.write_text(
        json.dumps(
            {
                "apps": [
                    {
                        "id": "virtual_clock",
                        "name": "Virtual Clock",
                        "description": "Aggregate description",
                        "entry_point": "apps.virtual_clock.app:VirtualClockApp",
                        "manifest": "virtual_clock.json",
                        "extra_field": "value",
                    }
                ]
            }
        )
    )

    loader = AppLoader()
    results = loader.load_metadata(str(aggregate_manifest))

    assert len(results) == 1
    metadata, manifest_path = results[0]
    assert manifest_path == aggregate_manifest.resolve()
    assert metadata.name == "Virtual Clock"
    assert metadata.module == "apps.virtual_clock.app"
    assert metadata.class_name == "VirtualClockApp"
    assert metadata.description == "Aggregate description"
    assert metadata.extra["capabilities"] == ["timekeeping"]
    assert metadata.extra["extra_field"] == "value"
    assert metadata.extra["manifest"] == "virtual_clock.json"
