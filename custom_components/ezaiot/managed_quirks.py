"""Strict catalog parsing for ezAIoT-managed ZHA Quirk packages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

CATALOG_FILE_NAME = "ezaiot-managed-quirks.json"
_CATALOG_KEYS = {"schema_version", "quirks"}
_QUIRK_KEYS = {"file", "manufacturer", "model"}


class ManagedQuirkCatalogError(ValueError):
    """Raised when a Release catalog does not declare an exact safe package."""


@dataclass(frozen=True, slots=True)
class ManagedQuirk:
    """One exact ZHA device signature and its managed root module."""

    file: str
    manufacturer: str
    model: str


@dataclass(frozen=True, slots=True)
class ManagedQuirkCatalog:
    """The complete safe file and device-signature set for one Release."""

    quirks: tuple[ManagedQuirk, ...]

    @property
    def files(self) -> tuple[str, ...]:
        """Return sorted root module names owned by this release."""
        return tuple(quirk.file for quirk in self.quirks)


def parse_catalog(
    contents: bytes, package_files: set[str] | None = None
) -> ManagedQuirkCatalog:
    """Parse a Release catalog and optionally bind it to package members."""
    try:
        payload = json.loads(contents)
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ManagedQuirkCatalogError("Invalid managed Quirk catalog") from err
    if not isinstance(payload, dict) or set(payload) != _CATALOG_KEYS:
        raise ManagedQuirkCatalogError("Invalid managed Quirk catalog")
    if payload.get("schema_version") != 1:
        raise ManagedQuirkCatalogError("Unsupported managed Quirk catalog")
    raw_quirks = payload.get("quirks")
    if not isinstance(raw_quirks, list) or not raw_quirks:
        raise ManagedQuirkCatalogError("Invalid managed Quirk catalog")

    quirks = tuple(_parse_quirk(item) for item in raw_quirks)
    files = tuple(quirk.file for quirk in quirks)
    signatures = tuple((quirk.manufacturer, quirk.model) for quirk in quirks)
    if len(set(files)) != len(files) or len(set(signatures)) != len(signatures):
        raise ManagedQuirkCatalogError("Duplicate managed Quirk catalog entry")

    expected_package_files = set(files) | {CATALOG_FILE_NAME}
    if package_files is not None and package_files != expected_package_files:
        raise ManagedQuirkCatalogError("Managed Quirk catalog does not match package")
    return ManagedQuirkCatalog(tuple(sorted(quirks, key=lambda quirk: quirk.file)))


def _parse_quirk(value: Any) -> ManagedQuirk:
    if not isinstance(value, dict) or set(value) != _QUIRK_KEYS:
        raise ManagedQuirkCatalogError("Invalid managed Quirk catalog entry")
    file = value.get("file")
    manufacturer = value.get("manufacturer")
    model = value.get("model")
    if (
        not _is_safe_module_name(file)
        or not _is_exact_text(manufacturer)
        or not _is_exact_text(model)
    ):
        raise ManagedQuirkCatalogError("Invalid managed Quirk catalog entry")
    return ManagedQuirk(file=file, manufacturer=manufacturer, model=model)


def _is_safe_module_name(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith(".py"):
        return False
    path = PurePosixPath(value)
    return (
        path.name == value
        and path.name not in {"", ".", ".."}
        and "\\" not in value
        and not path.is_absolute()
    )


def _is_exact_text(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip()
