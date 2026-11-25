"""Local registry discovery for exact signatures in the active Release."""

from collections import Counter
from collections.abc import Iterable
from typing import Protocol

from .managed_quirks import ManagedQuirk
from .models import CompatibilityState, DiscoveryResult, SupportRecord


class DeviceLike(Protocol):
    """Fields used from a Home Assistant device registry entry."""

    id: str
    manufacturer: str | None
    model: str | None


class EntityLike(Protocol):
    """Fields used from a Home Assistant entity registry entry."""

    device_id: str | None


def discover_managed_quirk_devices(
    devices: Iterable[DeviceLike],
    entities: Iterable[EntityLike],
    managed_quirks: Iterable[ManagedQuirk],
) -> DiscoveryResult:
    """Return redacted records for exact matches from the active catalog."""
    entity_counts = Counter(
        entity.device_id for entity in entities if entity.device_id is not None
    )
    supported_signatures = {
        (quirk.manufacturer, quirk.model) for quirk in managed_quirks
    }
    supported_devices = sorted(
        (device for device in devices if (device.manufacturer, device.model) in supported_signatures),
        key=lambda device: device.id,
    )
    records = tuple(
        SupportRecord(
            ordinal=index,
            manufacturer=device.manufacturer or "",
            model=device.model or "",
            entity_count=entity_counts[device.id],
        )
        for index, device in enumerate(supported_devices, start=1)
    )
    state = CompatibilityState.SUPPORTED if records else CompatibilityState.NOT_FOUND
    return DiscoveryResult(state=state, records=records)
