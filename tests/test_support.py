"""Contracts for display-only support resources."""

from custom_components.ezaiot.support import support_placeholders


def test_support_placeholders_expose_contact_and_unconfigured_resources() -> None:
    """Unset public resources use the common display marker."""
    assert support_placeholders() == {
        "support_email": "support@ezaiot.com",
        "documentation": "—",
        "tutorial_playlist": "—",
        "review": "—",
    }
