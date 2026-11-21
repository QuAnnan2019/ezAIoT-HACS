"""Local registry discovery for supported Rti-Tek thermostatic valves."""

from collections import Counter
from collections.abc import Iterable
from typing import Protocol

from .const import MANUFACTURER_RTI_TEK, MODEL_ETRV_ZB01
from .models import CompatibilityState, DiscoveryResult, SupportRecord


class DeviceLike(Protocol):
    """Fields used from a Home Assistant device registry entry."""

    id: str
    manufacturer: str | None
    model: str | None


class EntityLike(Protocol):
    """Fields used from a Home Assistant entity registry entry."""

    device_id: str | None


def discover_trvzb_devices(
    devices: Iterable[DeviceLike],
    entities: Iterable[EntityLike],
) -> DiscoveryResult:
    """Return redacted records for exact-match Rti-Tek eTRV-ZB01 devices."""
    entity_counts = Counter(
        entity.device_id for entity in entities if entity.device_id is not None
    )
    supported_devices = sorted(
        (
            device
            for device in devices
            if device.manufacturer == MANUFACTURER_RTI_TEK
            and device.model == MODEL_ETRV_ZB01
        ),
        key=lambda device: device.id,
    )
    records = tuple(
        SupportRecord(
            ordinal=index,
            manufacturer=MANUFACTURER_RTI_TEK,
            model=MODEL_ETRV_ZB01,
            entity_count=entity_counts[device.id],
        )
        for index, device in enumerate(supported_devices, start=1)
    )
    state = CompatibilityState.SUPPORTED if records else CompatibilityState.NOT_FOUND
    return DiscoveryResult(state=state, records=records)
