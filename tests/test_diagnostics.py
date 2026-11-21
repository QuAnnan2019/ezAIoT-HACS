import asyncio
import json
from types import SimpleNamespace

from custom_components.ezaiot.const import DATA_COORDINATOR, DOMAIN
from custom_components.ezaiot.diagnostics import async_get_config_entry_diagnostics
from custom_components.ezaiot.models import (
    CompatibilityState,
    DiscoveryResult,
    SupportRecord,
)


def test_diagnostics_contain_only_redacted_support_data() -> None:
    result = DiscoveryResult(
        state=CompatibilityState.SUPPORTED,
        records=(
            SupportRecord(
                ordinal=1,
                manufacturer="Rti-Tek",
                model="eTRV-ZB01",
                entity_count=4,
            ),
        ),
    )
    hass = SimpleNamespace(
        data={DOMAIN: {"entry-1": {DATA_COORDINATOR: SimpleNamespace(data=result)}}}
    )
    entry = SimpleNamespace(entry_id="entry-1")

    diagnostics = asyncio.run(async_get_config_entry_diagnostics(hass, entry))

    assert diagnostics["compatibility_state"] == "supported"
    assert diagnostics["supported_devices"] == [
        {
            "ordinal": 1,
            "manufacturer": "Rti-Tek",
            "model": "eTRV-ZB01",
            "entity_count": 4,
        },
    ]
    serialized = json.dumps(diagnostics).lower()
    for forbidden_key in (
        "device_id",
        "entity_id",
        "ieee",
        "ip",
        "token",
        "attributes",
        "name",
    ):
        assert forbidden_key not in serialized
