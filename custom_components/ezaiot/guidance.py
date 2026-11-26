"""State-based, manual setup guidance for the ZHA Quirk workflow."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant

from .const import DATA_RELEASE_SERVICE, DOMAIN, GUIDANCE_NOTIFICATION_ID
from .models import CompatibilityState, DiscoveryResult
from .release_models import UnsignedReleaseState

_ZHA_CONFIGURATION = "zha:\n  custom_quirks_path: /config/zha_quirks/ezaiot/"
_LOGGER = logging.getLogger(__name__)


class GuidanceCode(StrEnum):
    """The complete set of setup states shown to a user."""

    PAIR_DEVICE = "pair_device"
    INSTALL_RELEASE = "install_release"
    RESTART_HOME_ASSISTANT = "restart_home_assistant"
    ACTIVE_COMPATIBILITY = "active_compatibility"


@dataclass(frozen=True, slots=True)
class Guidance:
    """Redacted, display-ready manual setup guidance."""

    code: GuidanceCode
    title: str
    message: str
    actionable: bool


def build_guidance(
    discovery: DiscoveryResult,
    release: UnsignedReleaseState,
) -> Guidance:
    """Classify the next safe manual action from local integration state."""
    if discovery.state is CompatibilityState.NOT_FOUND:
        return _guidance(GuidanceCode.PAIR_DEVICE)
    if release.restart_required:
        return _guidance(GuidanceCode.RESTART_HOME_ASSISTANT)
    if release.installed_version is None:
        return _guidance(GuidanceCode.INSTALL_RELEASE)
    return _guidance(GuidanceCode.ACTIVE_COMPATIBILITY)


def async_sync_guidance_notification(
    hass: HomeAssistant,
    discovery: DiscoveryResult,
) -> Guidance:
    """Refresh owned guidance notification without interrupting the integration."""
    release = hass.data[DOMAIN][DATA_RELEASE_SERVICE].state
    guidance = build_guidance(discovery, release)
    try:
        async_sync_notification(hass, guidance)
    except Exception:  # pragma: no cover - Home Assistant storage boundary
        _LOGGER.exception("Unable to synchronize ZHA setup guidance notification")
    return guidance


def async_sync_notification(hass: HomeAssistant, guidance: Guidance) -> None:
    """Create or dismiss only the persistent notification owned by ezAIoT."""
    if guidance.actionable:
        persistent_notification.async_create(
            hass,
            guidance.message,
            title=guidance.title,
            notification_id=GUIDANCE_NOTIFICATION_ID,
        )
        return
    persistent_notification.async_dismiss(hass, GUIDANCE_NOTIFICATION_ID)


def _guidance(code: GuidanceCode) -> Guidance:
    """Return static content so guidance never includes local identifiers."""
    if code is GuidanceCode.PAIR_DEVICE:
        return Guidance(
            code=code,
            title="Set up ZHA before pairing",
            message=(
                f"Add this to configuration.yaml:\n{_ZHA_CONFIGURATION}\n\n"
                "Restart Home Assistant, then pair a device supported by the managed Quirk Release."
            ),
            actionable=True,
        )
    if code is GuidanceCode.INSTALL_RELEASE:
        return Guidance(
            code=code,
            title="Install the managed Quirk Release",
            message=(
                f"Confirm configuration.yaml contains:\n{_ZHA_CONFIGURATION}\n\n"
                "Restart Home Assistant, install the approved Quirk Release, then "
                "use Reconfigure or re-pair the device."
            ),
            actionable=True,
        )
    if code is GuidanceCode.RESTART_HOME_ASSISTANT:
        return Guidance(
            code=code,
            title="Restart Home Assistant",
            message=(
                f"Keep this in configuration.yaml:\n{_ZHA_CONFIGURATION}\n\n"
                "Restart Home Assistant to load the installed Quirk, then use "
                "Reconfigure or re-pair the device."
            ),
            actionable=True,
        )
    return Guidance(
        code=code,
        title="Managed Quirk compatibility is active",
        message="The managed Quirk is active. Advanced device capabilities are not enabled yet.",
        actionable=False,
    )
