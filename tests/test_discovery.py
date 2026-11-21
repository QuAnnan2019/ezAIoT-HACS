from types import SimpleNamespace

from custom_components.ezaiot.discovery import discover_trvzb_devices
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


def test_discovers_only_exact_rti_tek_etrv_zb01_devices() -> None:
    devices = (
        make_device("supported", "Rti-Tek", "eTRV-ZB01"),
        make_device("wrong-manufacturer", "Rti Tek", "eTRV-ZB01"),
        make_device("wrong-model", "Rti-Tek", "eTRV-ZB02"),
    )
    entities = (
        make_entity("supported"),
        make_entity("supported"),
        make_entity("wrong-model"),
    )

    result = discover_trvzb_devices(devices, entities)

    assert result.state is CompatibilityState.SUPPORTED
    assert result.supported_count == 1
    assert result.records[0].ordinal == 1
    assert result.records[0].manufacturer == "Rti-Tek"
    assert result.records[0].model == "eTRV-ZB01"
    assert result.records[0].entity_count == 2


def test_returns_not_found_for_empty_or_partial_matches() -> None:
    devices = (
        make_device("partial", "Rti-Tek", "eTRV-ZB01-Preview"),
        make_device("missing-model", "Rti-Tek", None),
    )

    result = discover_trvzb_devices(devices, ())

    assert result.state is CompatibilityState.NOT_FOUND
    assert result.supported_count == 0
    assert result.records == ()
