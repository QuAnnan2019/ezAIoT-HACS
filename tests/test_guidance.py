"""Contracts for local ZHA setup guidance."""

from types import SimpleNamespace
from unittest.mock import patch

from custom_components.ezaiot.guidance import (
    Guidance,
    GuidanceCode,
    async_sync_notification,
    build_guidance,
)
from custom_components.ezaiot.models import CompatibilityState, DiscoveryResult
from custom_components.ezaiot.release_models import ReleaseStatus, UnsignedReleaseState


def _release(
    *, installed: str | None, restart_required: bool
) -> UnsignedReleaseState:
    return UnsignedReleaseState(
        status=ReleaseStatus.UP_TO_DATE,
        installed_version=installed,
        backup_version=None,
        available_version=installed,
        release_notes="",
        restart_required=restart_required,
        message="",
    )


def test_build_guidance_for_new_user_without_matching_device() -> None:
    """A new user is directed to configure ZHA and pair the device."""
    guidance = build_guidance(
        DiscoveryResult(CompatibilityState.NOT_FOUND, ()),
        _release(installed=None, restart_required=False),
    )

    assert guidance.code is GuidanceCode.PAIR_DEVICE
    assert guidance.actionable is True
    assert "custom_quirks_path: /config/zha_quirks" in guidance.message


def test_build_guidance_for_existing_device_without_release() -> None:
    """A matched device without a managed Quirk needs reconfiguration guidance."""
    guidance = build_guidance(
        DiscoveryResult(CompatibilityState.SUPPORTED, ()),
        _release(installed=None, restart_required=False),
    )

    assert guidance.code is GuidanceCode.INSTALL_RELEASE
    assert "Reconfigure" in guidance.message


def test_build_guidance_requires_restart_after_install() -> None:
    """A deployed Quirk is not active until Home Assistant restarts."""
    guidance = build_guidance(
        DiscoveryResult(CompatibilityState.SUPPORTED, ()),
        _release(installed="0.0.2", restart_required=True),
    )

    assert guidance.code is GuidanceCode.RESTART_HOME_ASSISTANT


def test_build_guidance_marks_active_compatibility_complete() -> None:
    """An active managed Quirk is presented without advanced capability claims."""
    guidance = build_guidance(
        DiscoveryResult(CompatibilityState.SUPPORTED, ()),
        _release(installed="0.0.2", restart_required=False),
    )

    assert guidance.code is GuidanceCode.ACTIVE_COMPATIBILITY
    assert guidance.actionable is False


def test_actionable_guidance_creates_the_fixed_notification() -> None:
    """All actionable states replace the same persistent notification."""
    hass = SimpleNamespace()
    guidance = Guidance(GuidanceCode.PAIR_DEVICE, "Set up ZHA", "Add YAML", True)

    with patch(
        "custom_components.ezaiot.guidance.persistent_notification.async_create"
    ) as create:
        async_sync_notification(hass, guidance)

    create.assert_called_once_with(
        hass,
        "Add YAML",
        title="Set up ZHA",
        notification_id="ezaiot_zha_guidance",
    )


def test_active_guidance_dismisses_the_fixed_notification() -> None:
    """Active compatibility clears only the notification owned by ezAIoT."""
    hass = SimpleNamespace()
    guidance = Guidance(GuidanceCode.ACTIVE_COMPATIBILITY, "Compatibility active", "", False)

    with patch(
        "custom_components.ezaiot.guidance.persistent_notification.async_dismiss"
    ) as dismiss:
        async_sync_notification(hass, guidance)

    dismiss.assert_called_once_with(hass, "ezaiot_zha_guidance")
