import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from table_os.app_loader import ManifestParser


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
