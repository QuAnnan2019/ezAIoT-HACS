"""ezAIoT Home Assistant custom integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DATA_COORDINATOR,
    DATA_ONBOARDING_STATE,
    DATA_RELEASE_COORDINATOR,
    DATA_RELEASE_SERVICE,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import EzaiotCoordinator
from .guidance import async_sync_guidance_notification
from .onboarding import OnboardingState
from .panel import async_register_panel, async_remove_panel
from .release_coordinator import UnsignedReleaseCoordinator
from .release_service import UnsignedReleaseService
from .websocket import async_register_websocket_commands


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up local managed-Quirk discovery for a config entry."""
    if DOMAIN not in hass.data:
        await async_register_panel(hass)
        async_register_websocket_commands(hass)
        release_service = UnsignedReleaseService(hass)
        await hass.async_add_executor_job(release_service.ensure_managed_directory)
        await release_service.async_initialize()
        release_coordinator = UnsignedReleaseCoordinator(hass, release_service)
        release_coordinator.async_set_updated_data(release_service.state)
        onboarding = OnboardingState(hass)
        await onboarding.async_initialize()
        hass.data[DOMAIN] = {
            DATA_RELEASE_SERVICE: release_service,
            DATA_RELEASE_COORDINATOR: release_coordinator,
            DATA_ONBOARDING_STATE: onboarding,
        }

    coordinator = EzaiotCoordinator(hass, hass.data[DOMAIN][DATA_RELEASE_SERVICE])
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }
    async_sync_guidance_notification(hass, coordinator.data)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the discovery platform and release its coordinator."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not any(
            isinstance(data, dict) and DATA_COORDINATOR in data
            for data in hass.data[DOMAIN].values()
        ):
            hass.data.pop(DOMAIN)
            async_remove_panel(hass)
    return unload_ok
