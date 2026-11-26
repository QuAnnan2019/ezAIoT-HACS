"""Contracts for display-only support resources."""

import json
from pathlib import Path

from custom_components.ezaiot.support import support_placeholders, support_resources


def test_support_placeholders_expose_contact_and_unconfigured_resources() -> None:
    """Unset public resources use the common display marker."""
    assert support_placeholders() == {
        "support_email": "support@ezaiot.com",
        "documentation": "—",
        "tutorial_playlist": "—",
        "review": "—",
    }


def test_support_resources_only_publish_real_links() -> None:
    """Unset destinations must never be presented as clickable links."""
    assert support_resources()["documentation_url"]
    assert support_resources()["tutorial_url"] is None
    assert support_resources()["review_url"] is None


def test_option_translations_use_real_newlines_and_managed_path() -> None:
    """Options text is readable in Home Assistant's support dialog."""
    for path in ("strings.json", "translations/zh-Hans.json"):
        payload = json.loads(
            Path("custom_components/ezaiot", path).read_text(encoding="utf-8")
        )
        description = payload["options"]["step"]["init"]["description"]
        assert "\\n" not in description
        assert "custom_quirks_path: /config/zha_quirks/ezaiot/" in description
