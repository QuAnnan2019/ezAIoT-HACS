"""Sensor platform for ezAIoT compatibility state."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import EzaiotCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ezAIoT sensor from a config entry."""
    coordinator: EzaiotCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([EzaiotSupportedDevicesSensor(coordinator, entry)])


class EzaiotSupportedDevicesSensor(CoordinatorEntity[EzaiotCoordinator], SensorEntity):
    """Expose the number of exact-match managed Quirk devices."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:zigbee"
    _attr_name = "Supported managed Quirk devices"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: EzaiotCoordinator, entry: ConfigEntry) -> None:
        """Initialize the aggregate sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_managed_quirk_devices"

    @property
    def native_value(self) -> int:
        """Return the count of exact-match devices."""
        return self.coordinator.data.supported_count

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Expose only stable, non-identifying compatibility attributes."""
        return {
            "compatibility_state": self.coordinator.data.state.value,
            "discovery_source": "managed_quirk_catalog",
        }
