"""Persistent state for the one-time guided setup completion prompt."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.storage import Store

_STORE_KEY = "ezaiot.onboarding_state"
_STORE_VERSION = 1


class OnboardingState:
    """Store only whether the active-compatibility completion was shown."""

    def __init__(self, hass: Any) -> None:
        self._store: Store[dict[str, bool]] = Store(
            hass, _STORE_VERSION, _STORE_KEY, private=True, atomic_writes=True
        )
        self._completion_shown = False

    async def async_initialize(self) -> None:
        """Load the minimal local display state."""
        self._completion_shown = bool((await self._store.async_load() or {}).get("completion_shown"))

    async def async_should_show_completion(
        self, has_installed_release: bool, restart_required: bool, supported_count: int
    ) -> bool:
        """Return whether the successful guided setup should be acknowledged."""
        return (
            not self._completion_shown
            and has_installed_release
            and not restart_required
            and supported_count > 0
        )

    async def async_mark_completion_shown(self) -> None:
        """Persist acknowledgement without storing local device details."""
        self._completion_shown = True
        await self._store.async_save({"completion_shown": True})
