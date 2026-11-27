"""Serialized state management for unsigned test Release installation."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.storage import Store

from .managed_quirks import ManagedQuirk
from .release_client import ReleaseClientError, UnsignedReleaseClient
from .release_deployer import ReleaseDeploymentError, UnsignedReleaseDeployer
from .release_models import (
    ReleaseStatus,
    UnsignedReleaseCandidate,
    UnsignedReleaseState,
)

_STORE_KEY = "ezaiot.unsigned_release_state"
_STORE_VERSION = 1


class UnsignedReleaseService:
    """Coordinate manual test Release lifecycle behind a single async lock."""

    def __init__(
        self,
        hass: Any,
        client: UnsignedReleaseClient | None = None,
        deployer: UnsignedReleaseDeployer | None = None,
        store: Store[dict[str, object]] | None = None,
    ) -> None:
        """Build the service using HA's shared client session and configuration."""
        self._hass = hass
        self._client = client or UnsignedReleaseClient(
            aiohttp_client.async_get_clientsession(hass)
        )
        self._deployer = deployer or UnsignedReleaseDeployer(
            Path(hass.config.config_dir)
        )
        self._store = store or Store(
            hass,
            _STORE_VERSION,
            _STORE_KEY,
            private=True,
            atomic_writes=True,
        )
        self._lock = asyncio.Lock()
        self._candidate: UnsignedReleaseCandidate | None = None
        self._managed_quirks: tuple[ManagedQuirk, ...] = ()
        self._state = UnsignedReleaseState(
            status=ReleaseStatus.NO_RELEASE,
            installed_version=None,
            backup_version=None,
            available_version=None,
            release_notes="",
            restart_required=False,
            message="No test Release has been checked.",
        )

    @property
    def state(self) -> UnsignedReleaseState:
        """Return state without exposing local paths or remote asset metadata."""
        return self._state

    @property
    def managed_quirks(self) -> tuple[ManagedQuirk, ...]:
        """Return only active Release signatures, never local file paths."""
        return self._managed_quirks

    async def async_initialize(self) -> UnsignedReleaseState:
        """Load the minimal persisted installation record."""
        stored = await self._store.async_load() or {}
        self._managed_quirks = await self._hass.async_add_executor_job(
            self._deployer.managed_quirks
        )
        installed_version = self._stored_version(stored, "installed_version")
        backup_version = self._stored_version(stored, "backup_version")
        if not self._managed_quirks:
            installed_version = None
            backup_version = None
        self._state = UnsignedReleaseState(
            status=ReleaseStatus.UP_TO_DATE if installed_version else ReleaseStatus.NO_RELEASE,
            installed_version=installed_version,
            backup_version=backup_version,
            available_version=None,
            release_notes="",
            restart_required=False,
            message=(
                "Installed test Release is active."
                if installed_version
                else "No test Release has been checked."
            ),
        )
        return self._state

    async def async_check(self) -> UnsignedReleaseState:
        """Read fixed-origin test Release metadata without installing it."""
        async with self._lock:
            self._state = self._replace(status=ReleaseStatus.CHECKING, message="Checking test Release.")
            try:
                candidate = await self._client.async_fetch_latest()
            except ReleaseClientError:
                self._candidate = None
                self._state = self._replace(
                    status=ReleaseStatus.VERIFICATION_FAILED,
                    available_version=None,
                    release_notes="",
                    restart_required=False,
                    message="Unable to check the test Release.",
                )
                return self._state
            self._candidate = candidate
            if self._is_newer(candidate.version, self._state.installed_version):
                self._state = self._replace(
                    status=ReleaseStatus.UPDATE_AVAILABLE,
                    available_version=candidate.version,
                    release_notes=candidate.release_notes[:255],
                    restart_required=True,
                    message="A test Release is ready to install.",
                )
            else:
                self._state = self._replace(
                    status=ReleaseStatus.UP_TO_DATE,
                    available_version=candidate.version,
                    release_notes=candidate.release_notes[:255],
                    restart_required=False,
                    message="The installed test Release is current.",
                )
            return self._state

    async def async_install(self) -> UnsignedReleaseState:
        """Download and deploy the candidate produced by an explicit check."""
        async with self._lock:
            candidate = self._candidate
            if candidate is None or not self._is_newer(
                candidate.version, self._state.installed_version
            ):
                raise ValueError("A newer checked test Release is required")
            self._state = self._replace(status=ReleaseStatus.INSTALLING, message="Installing test Release.")
            try:
                package = await self._client.async_download_package(candidate)
                deployed = await self._hass.async_add_executor_job(
                    self._deployer.deploy, candidate.version, package
                )
            except (ReleaseClientError, ReleaseDeploymentError, OSError):
                self._state = self._replace(
                    status=ReleaseStatus.VERIFICATION_FAILED,
                    message="Unable to install the test Release.",
                )
                return self._state
            await self._persist(deployed)
            self._managed_quirks = await self._hass.async_add_executor_job(
                self._deployer.managed_quirks
            )
            self._candidate = None
            self._state = UnsignedReleaseState(
                status=ReleaseStatus.UP_TO_DATE,
                installed_version=deployed.installed_version,
                backup_version=deployed.backup_version,
                available_version=deployed.installed_version,
                release_notes="",
                restart_required=True,
                message="Test Release installed. Restart Home Assistant to load it.",
            )
            return self._state

    async def async_rollback(self) -> UnsignedReleaseState:
        """Restore the one ezAIoT-managed previous test Release."""
        async with self._lock:
            if self._state.backup_version is None:
                raise ValueError("No test Release backup is available")
            self._state = self._replace(status=ReleaseStatus.ROLLING_BACK, message="Restoring test Release backup.")
            try:
                deployed = await self._hass.async_add_executor_job(self._deployer.rollback)
            except (ReleaseDeploymentError, OSError):
                self._state = self._replace(
                    status=ReleaseStatus.VERIFICATION_FAILED,
                    message="Unable to restore the test Release backup.",
                )
                return self._state
            await self._persist(deployed)
            self._managed_quirks = await self._hass.async_add_executor_job(
                self._deployer.managed_quirks
            )
            self._state = UnsignedReleaseState(
                status=ReleaseStatus.UP_TO_DATE,
                installed_version=deployed.installed_version,
                backup_version=deployed.backup_version,
                available_version=deployed.installed_version,
                release_notes="",
                restart_required=True,
                message="Test Release backup restored. Restart Home Assistant to load it.",
            )
            return self._state

    async def _persist(self, deployed: Any) -> None:
        """Persist only installation metadata useful across Home Assistant restarts."""
        await self._store.async_save(
            {
                "installed_version": deployed.installed_version,
                "backup_version": deployed.backup_version,
                "deployed_at": datetime.now(UTC).isoformat(),
            }
        )

    def _replace(self, **changes: object) -> UnsignedReleaseState:
        return UnsignedReleaseState(
            status=changes.get("status", self._state.status),
            installed_version=changes.get("installed_version", self._state.installed_version),
            backup_version=changes.get("backup_version", self._state.backup_version),
            available_version=changes.get("available_version", self._state.available_version),
            release_notes=changes.get("release_notes", self._state.release_notes),
            restart_required=changes.get("restart_required", self._state.restart_required),
            message=changes.get("message", self._state.message),
        )

    @staticmethod
    def _stored_version(stored: dict[str, object], field: str) -> str | None:
        value = stored.get(field)
        return value if isinstance(value, str) else None

    @staticmethod
    def _is_newer(candidate: str, installed: str | None) -> bool:
        if installed is None:
            return True
        return tuple(map(int, candidate.split("."))) > tuple(map(int, installed.split(".")))
