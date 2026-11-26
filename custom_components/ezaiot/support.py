"""Display-only support resources for the ezAIoT Options Flow."""

from __future__ import annotations

SUPPORT_EMAIL = "support@ezaiot.com"
DOCUMENTATION_URL: str | None = None
TUTORIAL_PLAYLIST_URL: str | None = None
REVIEW_URL: str | None = None
_UNCONFIGURED_RESOURCE = "—"


def support_placeholders() -> dict[str, str]:
    """Return Options Flow display values without collecting configuration."""
    return {
        "support_email": SUPPORT_EMAIL,
        "documentation": DOCUMENTATION_URL or _UNCONFIGURED_RESOURCE,
        "tutorial_playlist": TUTORIAL_PLAYLIST_URL or _UNCONFIGURED_RESOURCE,
        "review": REVIEW_URL or _UNCONFIGURED_RESOURCE,
    }


def support_resources() -> dict[str, str | None]:
    """Return only public support destinations for the local panel."""
    return {
        "email": SUPPORT_EMAIL,
        "documentation_url": "https://github.com/QuAnnan2019/ezAIoT-HACS#readme",
        "tutorial_url": TUTORIAL_PLAYLIST_URL,
        "review_url": REVIEW_URL,
    }
