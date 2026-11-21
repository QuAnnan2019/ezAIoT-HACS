"""Static contracts for the local-only ezAIoT panel module."""

from pathlib import Path

PANEL_MODULE = (
    Path(__file__).parents[1]
    / "custom_components"
    / "ezaiot"
    / "frontend"
    / "ezaiot-panel.js"
)


def test_panel_uses_only_the_local_status_websocket() -> None:
    """The Demo frontend must not fetch or reference external release sources."""
    source = PANEL_MODULE.read_text(encoding="utf-8")

    assert 'type: "ezaiot/status"' in source
    assert ".callWS(" in source
    assert "fetch(" not in source
    assert "github.com" not in source.lower()
    assert "raw.githubusercontent.com" not in source.lower()


def test_panel_renders_demo_safety_boundaries() -> None:
    """The user-facing panel must explain the intentionally limited Demo."""
    source = PANEL_MODULE.read_text(encoding="utf-8")

    assert "Quirk updates" in source
    assert "No GitHub request is made" in source
    assert "Diagnostics and help" in source
    assert 'customElements.define("ezaiot-panel", EzaiotPanel)' in source
