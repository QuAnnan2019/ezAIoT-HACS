"""Contracts for the manual unsigned test Release update entity."""

import asyncio
from types import SimpleNamespace

import pytest
from homeassistant.components.update import UpdateEntityFeature

from custom_components.ezaiot.release_models import ReleaseStatus, UnsignedReleaseState
from custom_components.ezaiot.update import EzaiotTestReleaseUpdate


def _state(status: ReleaseStatus = ReleaseStatus.UPDATE_AVAILABLE) -> UnsignedReleaseState:
    return UnsignedReleaseState(
        status=status,
        installed_version="0.0.1",
        backup_version=None,
        available_version="0.0.2",
        release_notes="Test change.",
        restart_required=True,
        message="A test Release is ready to install.",
    )


def test_update_entity_exposes_only_manual_install() -> None:
    coordinator = SimpleNamespace(data=_state(), service=SimpleNamespace())
    entry = SimpleNamespace(entry_id="entry-1")

    entity = EzaiotTestReleaseUpdate(coordinator, entry)

    assert entity.installed_version == "0.0.1"
    assert entity.latest_version == "0.0.2"
    assert entity.release_summary == "Test change."
    assert entity.auto_update is False
    assert entity.supported_features is UpdateEntityFeature.INSTALL


def test_update_entity_rejects_specific_versions_and_delegates_latest() -> None:
    installed = _state(ReleaseStatus.UP_TO_DATE)

    async def install() -> UnsignedReleaseState:
        return installed

    coordinator = SimpleNamespace(
        data=_state(),
        service=SimpleNamespace(async_install=install),
        async_set_updated_data=lambda data: setattr(coordinator, "data", data),
    )
    entity = EzaiotTestReleaseUpdate(coordinator, SimpleNamespace(entry_id="entry-1"))

    with pytest.raises(ValueError, match="latest"):
        asyncio.run(entity.async_install("0.0.2", False))
    asyncio.run(entity.async_install(None, False))

    assert coordinator.data.status is ReleaseStatus.UP_TO_DATE
