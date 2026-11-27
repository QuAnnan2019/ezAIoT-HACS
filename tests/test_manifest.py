"""Contracts for ezAIoT Home Assistant integration metadata."""

import json
from pathlib import Path

from custom_components.ezaiot.const import INTEGRATION_VERSION


def test_manifest_uses_the_standard_integration_category() -> None:
    """The config entry belongs on Home Assistant's Integrations tab."""
    manifest = json.loads(Path("custom_components/ezaiot/manifest.json").read_text())

    assert "integration_type" not in manifest
    assert manifest["config_flow"] is True


def test_config_abort_translations_cover_duplicate_entry() -> None:
    """The Config Flow abort reason must not be shown as a raw key."""
    for path in (
        Path("custom_components/ezaiot/strings.json"),
        Path("custom_components/ezaiot/translations/zh-Hans.json"),
    ):
        translation = json.loads(path.read_text(encoding="utf-8"))
        assert translation["config"]["abort"]["already_configured"]


def test_runtime_version_matches_manifest() -> None:
    """Diagnostics must report the version HACS installs."""
    manifest = json.loads(Path("custom_components/ezaiot/manifest.json").read_text())
    assert INTEGRATION_VERSION == manifest["version"]


def test_panel_module_url_is_versioned() -> None:
    """A HACS upgrade must load its matching panel module."""
    from custom_components.ezaiot.const import PANEL_MODULE_URL

    assert PANEL_MODULE_URL.endswith(f"?v={INTEGRATION_VERSION}")
