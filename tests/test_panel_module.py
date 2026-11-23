"""Static contracts for the local-only ezAIoT panel module."""

from pathlib import Path

PANEL_MODULE = (
    Path(__file__).parents[1]
    / "custom_components"
    / "ezaiot"
    / "frontend"
    / "ezaiot-panel.js"
)


def test_panel_uses_only_local_websocket_commands() -> None:
    """The frontend must not fetch or reference external release sources."""
    source = PANEL_MODULE.read_text(encoding="utf-8")

    assert 'type: "ezaiot/status"' in source
    assert 'data-release-action="ezaiot/check_release"' in source
    assert 'data-release-action="ezaiot/install_release"' in source
    assert 'data-release-action="ezaiot/rollback_release"' in source
    assert ".callWS(" in source
    assert "fetch(" not in source
    assert "github.com" not in source.lower()
    assert "raw.githubusercontent.com" not in source.lower()


def test_panel_renders_unsigned_test_release_controls() -> None:
    """The panel must label test mode and confirm file-changing actions."""
    source = PANEL_MODULE.read_text(encoding="utf-8")

    assert "Quirk updates" in source
    assert "Unsigned test mode" in source
    assert "Install this unsigned test Release?" in source
    assert "Restore the previous unsigned test Release?" in source
    assert "Diagnostics and help" in source
    assert 'customElements.define("ezaiot-panel", EzaiotPanel)' in source
