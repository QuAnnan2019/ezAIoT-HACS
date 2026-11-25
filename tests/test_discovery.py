from types import SimpleNamespace

from custom_components.ezaiot.discovery import discover_managed_quirk_devices
from custom_components.ezaiot.managed_quirks import ManagedQuirk
from custom_components.ezaiot.models import CompatibilityState


def make_device(
    device_id: str,
    manufacturer: str | None,
    model: str | None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=device_id,
        manufacturer=manufacturer,
        model=model,
    )


def make_entity(device_id: str) -> SimpleNamespace:
    return SimpleNamespace(device_id=device_id)


def _managed_quirks() -> tuple[ManagedQuirk, ...]:
    return (
        ManagedQuirk("rti_tek_etrv_zb01.py", "Rti-Tek", "eTRV-ZB01"),
        ManagedQuirk("rti_tek_sthzb.py", "Rti-Tek", "STHZB"),
    )


def test_discovers_only_exact_active_managed_quirk_devices() -> None:
    devices = (
        make_device("supported", "Rti-Tek", "eTRV-ZB01"),
        make_device("wrong-manufacturer", "Rti Tek", "eTRV-ZB01"),
        make_device("wrong-model", "Rti-Tek", "eTRV-ZB02"),
        make_device("sthzb", "Rti-Tek", "STHZB"),
    )
    entities = (
        make_entity("supported"),
        make_entity("supported"),
        make_entity("wrong-model"),
    )

    result = discover_managed_quirk_devices(devices, entities, _managed_quirks())

    assert result.state is CompatibilityState.SUPPORTED
    assert result.supported_count == 2
    assert {record.model for record in result.records} == {"eTRV-ZB01", "STHZB"}
    etrv = next(record for record in result.records if record.model == "eTRV-ZB01")
    assert etrv.ordinal == 2
    assert etrv.manufacturer == "Rti-Tek"
    assert etrv.entity_count == 2


def test_returns_not_found_for_empty_or_partial_matches() -> None:
    devices = (
        make_device("partial", "Rti-Tek", "eTRV-ZB01-Preview"),
        make_device("missing-model", "Rti-Tek", None),
    )

    result = discover_managed_quirk_devices(devices, (), _managed_quirks())

    assert result.state is CompatibilityState.NOT_FOUND
    assert result.supported_count == 0
    assert result.records == ()
