"""Redacted diagnostics for ezAIoT config entries."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATOR, DATA_RELEASE_SERVICE, DOMAIN, INTEGRATION_VERSION
from .coordinator import EzaiotCoordinator
from .release_service import UnsignedReleaseService
from .zha_diagnostics import collect_zha_summaries, environment_versions


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, object]:
    """Return diagnostics without registry identifiers or raw device data."""
    coordinator: EzaiotCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    result = coordinator.data
    release_service: UnsignedReleaseService = hass.data[DOMAIN][DATA_RELEASE_SERVICE]
    release = release_service.state
    managed_quirks = getattr(release_service, "managed_quirks", ())
    return {
        "integration_version": INTEGRATION_VERSION,
        "home_assistant_version": HA_VERSION,
        "compatibility_state": result.state.value,
        "supported_devices": [
            {
                "ordinal": record.ordinal,
                "manufacturer": record.manufacturer,
                "model": record.model,
                "entity_count": record.entity_count,
            }
            for record in result.records
        ],
        "test_release": {
            "status": release.status.value,
            "installed_version": release.installed_version,
            "backup_version": release.backup_version,
            "available_version": release.available_version,
            "restart_required": release.restart_required,
        },
        "environment": environment_versions(),
        "managed_quirk_files": [quirk.file for quirk in managed_quirks],
        "zha_devices": collect_zha_summaries(hass, managed_quirks),
    }
