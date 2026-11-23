"""Home Assistant coordinator for unsigned test Release state."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, RELEASE_CHECK_INTERVAL
from .release_models import UnsignedReleaseState
from .release_service import UnsignedReleaseService


class UnsignedReleaseCoordinator(DataUpdateCoordinator[UnsignedReleaseState]):
    """Refresh test Release availability without affecting local discovery."""

    def __init__(self, hass: HomeAssistant, service: UnsignedReleaseService) -> None:
        """Initialize periodic Release metadata checks."""
        self.service = service
        super().__init__(
            hass,
            logger=None,
            name=f"{DOMAIN} unsigned test Release",
            update_interval=RELEASE_CHECK_INTERVAL,
        )

    async def _async_update_data(self) -> UnsignedReleaseState:
        """Return a redacted failure state rather than break platform startup."""
        try:
            return await self.service.async_check()
        except Exception as err:
            raise UpdateFailed("Unable to update test Release status") from err
