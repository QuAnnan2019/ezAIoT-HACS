"""Coordinator for local ezAIoT registry discovery."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL
from .discovery import discover_trvzb_devices
from .models import DiscoveryResult

_LOGGER = logging.getLogger(__name__)


class EzaiotCoordinator(DataUpdateCoordinator[DiscoveryResult]):
    """Refresh the local compatibility state without contacting devices."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> DiscoveryResult:
        """Read Home Assistant registries and produce a redacted result."""
        try:
            device_registry = dr.async_get(self.hass)
            entity_registry = er.async_get(self.hass)
            return discover_trvzb_devices(
                device_registry.devices.values(),
                entity_registry.entities.values(),
            )
        except Exception as err:
            raise UpdateFailed("Unable to scan Home Assistant registries") from err
