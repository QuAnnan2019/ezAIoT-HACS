"""Minimal, redacted ZHA data for ezAIoT diagnostics."""

from __future__ import annotations

import hashlib
import platform
from collections.abc import Iterable, Mapping
from importlib import metadata
from typing import Any

from homeassistant.helpers import device_registry as dr

from .managed_quirks import ManagedQuirk


def ieee_hash(value: object) -> str | None:
    """Return a stable short identifier without exposing an IEEE address."""
    if value is None:
        return None
    return hashlib.sha256(str(value).encode()).hexdigest()[:12]


def summarize_zha_device(device: object | None) -> dict[str, object] | None:
    """Return only the endpoint and cluster IDs needed for support diagnosis."""
    if device is None:
        return None

    endpoints = getattr(device, "endpoints", {})
    endpoint_items = endpoints.items() if isinstance(endpoints, Mapping) else ()
    return {
        "ieee_hash": ieee_hash(getattr(device, "ieee", None)),
        "endpoints": [
            {
                "id": endpoint_id,
                "in_clusters": _cluster_ids(getattr(endpoint, "in_clusters", {})),
                "out_clusters": _cluster_ids(getattr(endpoint, "out_clusters", {})),
            }
            for endpoint_id, endpoint in sorted(endpoint_items)
            if endpoint_id != 0
        ],
    }


def environment_versions() -> dict[str, str | None]:
    """Return the runtime versions relevant to a ZHA Quirk issue."""
    try:
        zigpy_version = metadata.version("zigpy")
    except metadata.PackageNotFoundError:
        zigpy_version = None
    return {"python": platform.python_version(), "zigpy": zigpy_version}


def collect_zha_summaries(
    hass: Any, managed_quirks: Iterable[ManagedQuirk]
) -> list[dict[str, object]]:
    """Summarize only registry devices matching the active Quirk catalog."""
    signatures = {
        (quirk.manufacturer, quirk.model)
        for quirk in managed_quirks
    }
    if not signatures:
        return []

    device_registry = dr.async_get(hass)
    matching_devices = sorted(
        (
            device
            for device in device_registry.devices.values()
            if (device.manufacturer, device.model) in signatures
        ),
        key=lambda device: device.id,
    )

    try:
        from homeassistant.components.zha.helpers import async_get_zha_device_proxy
    except ImportError:
        return []

    summaries: list[dict[str, object]] = []
    for device in matching_devices:
        try:
            summary = summarize_zha_device(
                async_get_zha_device_proxy(hass, device.id).device
            )
        except (AttributeError, KeyError, StopIteration, ValueError):
            continue
        if summary is not None:
            summaries.append(summary)
    return summaries


def _cluster_ids(clusters: object) -> list[int]:
    """Return sorted cluster identifiers from a ZHA endpoint mapping."""
    if not isinstance(clusters, Mapping):
        return []
    return sorted(int(cluster_id) for cluster_id in clusters)
