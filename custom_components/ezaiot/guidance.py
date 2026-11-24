"""State-based, manual setup guidance for the ZHA Quirk workflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .models import CompatibilityState, DiscoveryResult
from .release_models import UnsignedReleaseState

_ZHA_CONFIGURATION = "zha:\n  custom_quirks_path: /config/zha_quirks"


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


def _guidance(code: GuidanceCode) -> Guidance:
    """Return static content so guidance never includes local identifiers."""
    if code is GuidanceCode.PAIR_DEVICE:
        return Guidance(
            code=code,
            title="Set up ZHA before pairing",
            message=(
                f"Add this to configuration.yaml:\n{_ZHA_CONFIGURATION}\n\n"
                "Restart Home Assistant, then pair the eTRV-ZB01 device."
            ),
            actionable=True,
        )
    if code is GuidanceCode.INSTALL_RELEASE:
        return Guidance(
            code=code,
            title="Install the eTRV-ZB01 Quirk",
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
        title="eTRV-ZB01 compatibility is active",
        message="The managed Quirk is active. Advanced device capabilities are not enabled yet.",
        actionable=False,
    )
