import asyncio
import json
from types import SimpleNamespace

from custom_components.ezaiot.const import (
    DATA_COORDINATOR,
    DATA_RELEASE_SERVICE,
    DOMAIN,
)
from custom_components.ezaiot.diagnostics import async_get_config_entry_diagnostics
from custom_components.ezaiot.models import (
    CompatibilityState,
    DiscoveryResult,
    SupportRecord,
)
from custom_components.ezaiot.release_models import ReleaseStatus, UnsignedReleaseState


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
    release = UnsignedReleaseState(
        status=ReleaseStatus.UPDATE_AVAILABLE,
        installed_version="0.0.1",
        backup_version="0.0.0",
        available_version="0.0.2",
        release_notes="Test change.",
        restart_required=True,
        message="A test Release is ready to install.",
    )
    hass = SimpleNamespace(
        data={
            DOMAIN: {
                "entry-1": {DATA_COORDINATOR: SimpleNamespace(data=result)},
                DATA_RELEASE_SERVICE: SimpleNamespace(state=release),
            }
        }
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
    assert diagnostics["test_release"] == {
        "status": "update_available",
        "installed_version": "0.0.1",
        "backup_version": "0.0.0",
        "available_version": "0.0.2",
        "restart_required": True,
    }
    serialized = json.dumps(diagnostics).lower()
    for forbidden_key in (
        "device_id",
        "entity_id",
        "ieee",
        "ip",
        "token",
        "attributes",
        "name",
        "release_url",
        "asset",
        "sha256",
        "path",
        "exception",
    ):
        assert forbidden_key not in serialized
