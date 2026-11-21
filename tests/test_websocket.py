import asyncio
from types import SimpleNamespace

from custom_components.ezaiot.const import DATA_COORDINATOR, DOMAIN
from custom_components.ezaiot.models import (
    CompatibilityState,
    DiscoveryResult,
    SupportRecord,
)
from custom_components.ezaiot.websocket import websocket_get_status


class Connection:
    def __init__(self) -> None:
        self.result: tuple[int, dict[str, object]] | None = None

    def send_result(self, message_id: int, result: dict[str, object]) -> None:
        self.result = (message_id, result)


def test_websocket_returns_redacted_panel_status() -> None:
    result = DiscoveryResult(
        state=CompatibilityState.SUPPORTED,
        records=(
            SupportRecord(
                ordinal=1,
                manufacturer="Rti-Tek",
                model="eTRV-ZB01",
                entity_count=3,
            ),
        ),
    )
    hass = SimpleNamespace(
        data={DOMAIN: {"entry-1": {DATA_COORDINATOR: SimpleNamespace(data=result)}}}
    )
    connection = Connection()

    asyncio.run(
        websocket_get_status.__wrapped__(
            hass,
            connection,
            {"id": 7, "type": "ezaiot/status"},
        )
    )

    assert connection.result == (
        7,
        {
            "integration_version": "0.1.0",
            "supported_count": 1,
            "records": [
                {
                    "ordinal": 1,
                    "manufacturer": "Rti-Tek",
                    "model": "eTRV-ZB01",
                    "entity_count": 3,
                }
            ],
            "update_source": {
                "state": "not_configured",
                "message": "GitHub release source is not configured.",
            },
        },
    )
