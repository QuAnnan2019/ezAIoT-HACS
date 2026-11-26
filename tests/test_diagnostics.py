import asyncio
import json
from types import SimpleNamespace

from custom_components.ezaiot.const import (
    DATA_COORDINATOR,
    DATA_RELEASE_SERVICE,
    DOMAIN,
)
from custom_components.ezaiot.diagnostics import (
    async_build_diagnostics,
    async_get_config_entry_diagnostics,
)
from custom_components.ezaiot.models import (
    CompatibilityState,
    DiscoveryResult,
    SupportRecord,
)
from custom_components.ezaiot.release_models import ReleaseStatus, UnsignedReleaseState


def test_diagnostics_contain_only_redacted_support_data(monkeypatch) -> None:
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

    monkeypatch.setattr(
        "custom_components.ezaiot.diagnostics.environment_versions",
        lambda: {"python": "3.12.0", "zigpy": "1.0.0"},
    )
    monkeypatch.setattr(
        "custom_components.ezaiot.diagnostics.collect_zha_summaries",
        lambda *_: [
            {
                "ieee_hash": "74e831a01ddb",
                "endpoints": [
                    {"id": 1, "in_clusters": [6, 64546], "out_clusters": [25]}
                ],
            }
        ],
    )

    diagnostics = asyncio.run(async_get_config_entry_diagnostics(hass, entry))
    shared_diagnostics = asyncio.run(async_build_diagnostics(hass, entry))

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
    assert diagnostics["environment"] == {"python": "3.12.0", "zigpy": "1.0.0"}
    assert diagnostics["managed_quirk_files"] == []
    assert diagnostics["zha_devices"] == [
        {
            "ieee_hash": "74e831a01ddb",
            "endpoints": [
                {"id": 1, "in_clusters": [6, 64546], "out_clusters": [25]}
            ],
        }
    ]
    assert shared_diagnostics == diagnostics
    serialized = json.dumps(diagnostics).lower()
    for forbidden_key in (
        "device_id",
        "entity_id",
        "ip",
        "token",
        "attributes",
        "name",
        "release_url",
        "asset",
        "sha256",
        "path",
        "exception",
        "00:11:22:33:44:55:66:77",
    ):
        assert forbidden_key not in serialized
