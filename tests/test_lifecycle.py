"""Lifecycle wiring contracts for the ezAIoT custom integration."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from custom_components.ezaiot import async_setup_entry, async_unload_entry
from custom_components.ezaiot.const import (
    DATA_COORDINATOR,
    DATA_RELEASE_COORDINATOR,
    DATA_RELEASE_SERVICE,
    DOMAIN,
)
from custom_components.ezaiot.models import CompatibilityState, DiscoveryResult


def test_first_entry_registers_panel_websocket_and_coordinator() -> None:
    """The first entry owns panel, WebSocket and coordinator initialization."""
    forward_setups = AsyncMock()
    hass = SimpleNamespace(
        data={},
        async_add_executor_job=AsyncMock(),
        config_entries=SimpleNamespace(async_forward_entry_setups=forward_setups),
    )
    entry = SimpleNamespace(entry_id="entry-1")

    with (
        patch(
            "custom_components.ezaiot.async_register_panel",
            new=AsyncMock(),
        ) as register_panel,
        patch("custom_components.ezaiot.async_register_websocket_commands") as register_ws,
        patch("custom_components.ezaiot.async_sync_guidance_notification") as sync_guidance,
        patch("custom_components.ezaiot.EzaiotCoordinator") as coordinator_type,
        patch("custom_components.ezaiot.UnsignedReleaseService") as service_type,
        patch("custom_components.ezaiot.UnsignedReleaseCoordinator") as release_type,
        patch("custom_components.ezaiot.OnboardingState") as onboarding_type,
    ):
        coordinator = coordinator_type.return_value
        coordinator.async_config_entry_first_refresh = AsyncMock()
        coordinator.data = DiscoveryResult(CompatibilityState.NOT_FOUND, ())
        service_type.return_value.async_initialize = AsyncMock()
        release_type.return_value.async_config_entry_first_refresh = AsyncMock()
        onboarding_type.return_value.async_initialize = AsyncMock()

        assert asyncio.run(async_setup_entry(hass, entry)) is True

    register_panel.assert_awaited_once_with(hass)
    register_ws.assert_called_once_with(hass)
    hass.async_add_executor_job.assert_awaited_once_with(
        service_type.return_value.ensure_managed_directory
    )
    service_type.return_value.async_initialize.assert_awaited_once_with()
    coordinator.async_config_entry_first_refresh.assert_awaited_once_with()
    assert hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR] is coordinator
    assert hass.data[DOMAIN][DATA_RELEASE_SERVICE] is service_type.return_value
    assert hass.data[DOMAIN][DATA_RELEASE_COORDINATOR] is release_type.return_value
    assert hass.data[DOMAIN]["onboarding_state"] is onboarding_type.return_value
    sync_guidance.assert_called_once_with(hass, coordinator.data)
    forward_setups.assert_awaited_once()


def test_last_entry_removes_the_sidebar_panel() -> None:
    """Unloading the final entry removes the panel and runtime domain data."""
    unload_platforms = AsyncMock(return_value=True)
    hass = SimpleNamespace(
        data={},
        config_entries=SimpleNamespace(async_unload_platforms=unload_platforms),
    )
    entry = SimpleNamespace(entry_id="entry-1")
    hass.data[DOMAIN] = {
        DATA_RELEASE_SERVICE: object(),
        DATA_RELEASE_COORDINATOR: object(),
        entry.entry_id: {DATA_COORDINATOR: object()},
    }

    with patch("custom_components.ezaiot.async_remove_panel") as remove_panel:
        assert asyncio.run(async_unload_entry(hass, entry)) is True

    remove_panel.assert_called_once_with(hass)
    assert DOMAIN not in hass.data
