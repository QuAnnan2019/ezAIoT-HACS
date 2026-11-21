"""Redacted diagnostics for ezAIoT config entries."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATOR, DOMAIN, INTEGRATION_VERSION
from .coordinator import EzaiotCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, object]:
    """Return diagnostics without registry identifiers or raw device data."""
    coordinator: EzaiotCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    result = coordinator.data
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
    }
