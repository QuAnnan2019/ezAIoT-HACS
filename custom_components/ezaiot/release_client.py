"""Temporary client for manually installing unsigned test Releases."""

from __future__ import annotations

import re
from typing import Any

from .const import (
    RELEASE_API_URL,
    RELEASE_MAX_PACKAGE_BYTES,
    RELEASE_PACKAGE_PREFIX,
)
from .release_models import ReleaseAsset, UnsignedReleaseCandidate

_VERSION_RE = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_RELEASE_DOWNLOAD_ROOT = (
    "https://github.com/QuAnnan2019/zigbee-quircks/releases/download/"
)


class ReleaseClientError(ValueError):
    """Raised when the fixed test Release source is unusable."""


class UnsignedReleaseClient:
    """Read the one exact unsigned package from the fixed GitHub repository."""

    def __init__(self, session: Any) -> None:
        """Initialize with Home Assistant's shared aiohttp session."""
        self._session = session

    async def async_fetch_latest(self) -> UnsignedReleaseCandidate:
        """Fetch metadata for the latest eligible test Release."""
        async with self._session.get(
            RELEASE_API_URL,
            headers={"Accept": "application/vnd.github+json"},
        ) as response:
            if response.status == 404:
                raise ReleaseClientError("No test Release is published")
            if response.status != 200:
                raise ReleaseClientError("Unable to read the test Release")
            payload = await response.json()

        if not isinstance(payload, dict):
            raise ReleaseClientError("Invalid test Release metadata")
        tag = payload.get("tag_name")
        if not isinstance(tag, str) or _VERSION_RE.fullmatch(tag) is None:
            raise ReleaseClientError("Invalid test Release version")
        version = tag.removeprefix("v")
        package_name = f"{RELEASE_PACKAGE_PREFIX}{version}.zip"
        package_url = f"{_RELEASE_DOWNLOAD_ROOT}{tag}/{package_name}"
        assets = payload.get("assets")
        if not isinstance(assets, list):
            raise ReleaseClientError("Invalid test Release assets")

        selected: ReleaseAsset | None = None
        for raw_asset in assets:
            if not isinstance(raw_asset, dict) or raw_asset.get("name") != package_name:
                continue
            asset_id = raw_asset.get("id")
            size = raw_asset.get("size")
            download_url = raw_asset.get("browser_download_url")
            if (
                isinstance(asset_id, bool)
                or not isinstance(asset_id, int)
                or isinstance(size, bool)
                or not isinstance(size, int)
                or not 0 < size <= RELEASE_MAX_PACKAGE_BYTES
                or download_url != package_url
            ):
                raise ReleaseClientError("Invalid test Release package")
            selected = ReleaseAsset(
                asset_id=asset_id,
                name=package_name,
                size=size,
                api_url=package_url,
            )
            break

        if selected is None:
            raise ReleaseClientError("Missing expected test Release package")
        release_url = payload.get("html_url")
        if not isinstance(release_url, str):
            release_url = ""
        release_notes = payload.get("body")
        if not isinstance(release_notes, str):
            release_notes = ""
        return UnsignedReleaseCandidate(
            version=version,
            package=selected,
            release_notes=release_notes,
            release_url=release_url,
        )

    async def async_download_package(self, candidate: UnsignedReleaseCandidate) -> bytes:
        """Download the already selected package with a final size check."""
        async with self._session.get(
            candidate.package.api_url,
            headers={"Accept": "application/octet-stream"},
        ) as response:
            if response.status != 200:
                raise ReleaseClientError("Unable to download the test Release package")
            package = await response.read()
        if len(package) != candidate.package.size:
            raise ReleaseClientError("Test Release package size does not match metadata")
        if len(package) > RELEASE_MAX_PACKAGE_BYTES:
            raise ReleaseClientError("Test Release package is too large")
        return package
