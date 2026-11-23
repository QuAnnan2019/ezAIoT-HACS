"""Contracts for unsigned test Release state and serialization."""

import asyncio
from types import SimpleNamespace

import pytest

from custom_components.ezaiot.release_models import (
    DeploymentState,
    ReleaseAsset,
    ReleaseStatus,
    UnsignedReleaseCandidate,
)
from custom_components.ezaiot.release_service import UnsignedReleaseService


class FakeStore:
    """In-memory replacement for the Home Assistant state store."""

    def __init__(self, data: dict[str, object] | None = None) -> None:
        self.data = data

    async def async_load(self) -> dict[str, object] | None:
        return self.data

    async def async_save(self, data: dict[str, object]) -> None:
        self.data = data


class FakeClient:
    """Return a fixed candidate and package, recording calls."""

    def __init__(self, candidate: UnsignedReleaseCandidate) -> None:
        self.candidate = candidate
        self.downloads = 0

    async def async_fetch_latest(self) -> UnsignedReleaseCandidate:
        return self.candidate

    async def async_download_package(self, _: UnsignedReleaseCandidate) -> bytes:
        self.downloads += 1
        return b"package"


class FakeDeployer:
    """Record synchronous deployment operations."""

    def __init__(self) -> None:
        self.deployments: list[tuple[str, bytes]] = []
        self.rollbacks = 0

    def deploy(self, version: str, package: bytes) -> DeploymentState:
        self.deployments.append((version, package))
        return DeploymentState(version, "0.0.1", None, None)

    def rollback(self) -> DeploymentState:
        self.rollbacks += 1
        return DeploymentState("0.0.1", "0.0.2", None, None)


async def _run_in_executor(func: object, *args: object) -> object:
    assert callable(func)
    return func(*args)


def _candidate(version: str = "0.0.2") -> UnsignedReleaseCandidate:
    return UnsignedReleaseCandidate(
        version=version,
        package=ReleaseAsset(1, f"ezaiot-zha-etrv-zb01-v{version}.zip", 7, "url"),
        release_notes="Test change.",
        release_url="",
    )


def _service(
    client: FakeClient | None = None,
    deployer: FakeDeployer | None = None,
    store: FakeStore | None = None,
) -> tuple[UnsignedReleaseService, FakeClient, FakeDeployer, FakeStore]:
    client = client or FakeClient(_candidate())
    deployer = deployer or FakeDeployer()
    store = store or FakeStore()
    hass = SimpleNamespace(async_add_executor_job=_run_in_executor)
    return UnsignedReleaseService(hass, client, deployer, store), client, deployer, store


def test_check_then_install_persists_only_redacted_release_state() -> None:
    service, client, deployer, store = _service()

    assert asyncio.run(service.async_initialize()).status is ReleaseStatus.NO_RELEASE
    checked = asyncio.run(service.async_check())
    installed = asyncio.run(service.async_install())

    assert checked.status is ReleaseStatus.UPDATE_AVAILABLE
    assert installed.status is ReleaseStatus.UP_TO_DATE
    assert installed.installed_version == "0.0.2"
    assert client.downloads == 1
    assert deployer.deployments == [("0.0.2", b"package")]
    assert store.data is not None
    assert set(store.data) == {"installed_version", "backup_version", "deployed_at"}
    assert store.data["installed_version"] == "0.0.2"


def test_install_requires_a_checked_candidate() -> None:
    service, _, deployer, _ = _service()

    asyncio.run(service.async_initialize())

    with pytest.raises(ValueError, match="checked"):
        asyncio.run(service.async_install())
    assert deployer.deployments == []


def test_rollback_requires_backup_and_swaps_persisted_versions() -> None:
    store = FakeStore(
        {
            "installed_version": "0.0.2",
            "backup_version": "0.0.1",
            "deployed_at": "2026-11-23T00:00:00+00:00",
        }
    )
    service, _, deployer, persisted = _service(store=store)

    asyncio.run(service.async_initialize())
    state = asyncio.run(service.async_rollback())

    assert state.installed_version == "0.0.1"
    assert state.backup_version == "0.0.2"
    assert deployer.rollbacks == 1
    assert persisted.data is not None
    assert persisted.data["installed_version"] == "0.0.1"
