"""Contracts for the temporary, unsigned GitHub Release client."""

import asyncio
from dataclasses import dataclass
from typing import Self

import pytest

from custom_components.ezaiot.const import RELEASE_API_URL
from custom_components.ezaiot.release_client import (
    ReleaseClientError,
    UnsignedReleaseClient,
)


@dataclass
class FakeResponse:
    """Small aiohttp response substitute for client contracts."""

    status: int
    payload: object
    url: str

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def json(self) -> object:
        return self.payload

    async def read(self) -> bytes:
        assert isinstance(self.payload, bytes)
        return self.payload


class FakeSession:
    """Record each request and serve known API/asset responses."""

    def __init__(self, responses: dict[str, FakeResponse]) -> None:
        self.responses = responses
        self.requests: list[tuple[str, dict[str, object]]] = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.requests.append((url, kwargs))
        return self.responses[url]


def _release_payload() -> dict[str, object]:
    return {
        "tag_name": "v0.0.1",
        "body": "Test quirk release.",
        "html_url": "https://github.com/QuAnnan2019/zigbee-quircks/releases/tag/v0.0.1",
        "assets": [
            {
                "id": 1,
                "name": "ezaiot-zha-etrv-zb01-v0.0.1.zip",
                "size": 12,
                "browser_download_url": "https://github.com/QuAnnan2019/zigbee-quircks/releases/download/v0.0.1/ezaiot-zha-etrv-zb01-v0.0.1.zip",
            }
        ],
    }


def test_client_selects_only_the_expected_test_package() -> None:
    session = FakeSession(
        {
            RELEASE_API_URL: FakeResponse(200, _release_payload(), RELEASE_API_URL),
        }
    )

    candidate = asyncio.run(UnsignedReleaseClient(session).async_fetch_latest())

    assert candidate.version == "0.0.1"
    assert candidate.package.name == "ezaiot-zha-etrv-zb01-v0.0.1.zip"
    assert session.requests == [(RELEASE_API_URL, {"headers": {"Accept": "application/vnd.github+json"}})]


def test_client_rejects_missing_or_wrongly_named_package() -> None:
    payload = _release_payload()
    payload["assets"] = []
    session = FakeSession({RELEASE_API_URL: FakeResponse(200, payload, RELEASE_API_URL)})

    with pytest.raises(ReleaseClientError, match="(?i)expected.*package"):
        asyncio.run(UnsignedReleaseClient(session).async_fetch_latest())


def test_client_downloads_only_selected_package_and_enforces_size() -> None:
    candidate_payload = _release_payload()
    package_url = candidate_payload["assets"][0]["browser_download_url"]
    assert isinstance(package_url, str)
    session = FakeSession(
        {
            RELEASE_API_URL: FakeResponse(200, candidate_payload, RELEASE_API_URL),
            package_url: FakeResponse(200, b"test package", package_url),
        }
    )
    client = UnsignedReleaseClient(session)
    candidate = asyncio.run(client.async_fetch_latest())

    package = asyncio.run(client.async_download_package(candidate))

    assert package == b"test package"
    assert session.requests[-1] == (package_url, {"headers": {"Accept": "application/octet-stream"}})
