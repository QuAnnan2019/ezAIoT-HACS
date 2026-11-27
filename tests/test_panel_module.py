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
    assert 'type: "ezaiot/download_diagnostics"' in source
    assert "new Blob(" in source
    assert "URL.createObjectURL" in source
    assert "ezaiot-diagnostics.json" in source
    assert ".callWS(" in source
    assert "fetch(" not in source
    assert "github.com" not in source.lower()
    assert "raw.githubusercontent.com" not in source.lower()


def test_panel_renders_unsigned_test_release_controls() -> None:
    """The panel must expose safe controls and recoverable setup guidance."""
    source = PANEL_MODULE.read_text(encoding="utf-8")

    assert "data-dismiss-guidance" in source
    assert "data-resume-guidance" in source
    assert "Continue setup" in source
    assert "Step 1 of 3" in source
    assert "Step 2 of 3" in source
    assert "Step 3 of 3" in source
    assert "<h2>Guided Quirk setup</h2>" not in source
    assert "Check approved Release" in source
    assert "Install approved Quirk" in source
    assert "Unsigned test mode" in source
    assert "Install this approved Quirk Release?" in source
    assert "Restore the previous unsigned test Release?" in source
    assert "custom_quirks_path: /config/zha_quirks/ezaiot/" in source
    assert "Reconfigure or re-pair" in source
    assert "Technical support" in source
    assert "Download ZHA diagnostics" in source
    assert "Setup complete" in source
    assert "ezaiot/dismiss_completion" in source
    assert 'customElements.define("ezaiot-panel", EzaiotPanel)' in source


def test_options_guidance_mentions_the_required_zha_path() -> None:
    """Both shipped Options translations explain the manual prerequisite."""
    english = Path("custom_components/ezaiot/strings.json").read_text(encoding="utf-8")
    chinese = Path(
        "custom_components/ezaiot/translations/zh-Hans.json"
    ).read_text(encoding="utf-8")

    assert "custom_quirks_path: /config/zha_quirks/ezaiot/" in english
    assert "custom_quirks_path: /config/zha_quirks/ezaiot/" in chinese
