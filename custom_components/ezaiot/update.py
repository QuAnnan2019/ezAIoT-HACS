"""Update entity for the manually installed unsigned test Release."""

from __future__ import annotations

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DATA_RELEASE_COORDINATOR, DOMAIN
from .guidance import async_sync_guidance_notification
from .release_coordinator import UnsignedReleaseCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the single manually-controlled test Release update entity."""
    coordinator: UnsignedReleaseCoordinator = hass.data[DOMAIN][
        DATA_RELEASE_COORDINATOR
    ]
    async_add_entities([EzaiotTestReleaseUpdate(coordinator, entry)])


class EzaiotTestReleaseUpdate(
    CoordinatorEntity[UnsignedReleaseCoordinator], UpdateEntity
):
    """Expose the latest checked unsigned package as a manual HA update."""

    _attr_has_entity_name = True
    _attr_name = "Test quirk release"
    _attr_auto_update = False
    _attr_supported_features = UpdateEntityFeature.INSTALL
    _attr_title = "ezAIoT test quirk release"

    def __init__(
        self,
        coordinator: UnsignedReleaseCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize stable identity for the singleton integration entry."""
        super().__init__(coordinator)
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_test_quirk_release"

    @property
    def installed_version(self) -> str | None:
        """Return the test Release currently recorded as deployed."""
        return self.coordinator.data.installed_version

    @property
    def latest_version(self) -> str | None:
        """Return the candidate version supplied by the last check."""
        return self.coordinator.data.available_version

    @property
    def release_summary(self) -> str | None:
        """Return bounded notes from the checked test Release."""
        return self.coordinator.data.release_notes or None

    @property
    def in_progress(self) -> bool:
        """Show only active file-changing operations as in progress."""
        return self.coordinator.data.status.value in {"installing", "rolling_back"}

    async def async_install(
        self,
        version: str | None,
        backup: bool,
        **kwargs: object,
    ) -> None:
        """Install only the checked latest test Release without HA backup control."""
        if version is not None or backup:
            raise ValueError("Only the latest test Release can be installed")
        state = await self.coordinator.service.async_install()
        self.coordinator.async_set_updated_data(state)
        discovery = self.coordinator.hass.data[DOMAIN][self._entry_id][
            DATA_COORDINATOR
        ].data
        async_sync_guidance_notification(self.coordinator.hass, discovery)
