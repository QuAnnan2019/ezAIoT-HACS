"""Read-only WebSocket data for the ezAIoT sidebar panel."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import (
    DATA_COORDINATOR,
    DATA_WEBSOCKET_REGISTERED,
    DOMAIN,
    INTEGRATION_VERSION,
)
from .coordinator import EzaiotCoordinator


@websocket_api.websocket_command(
    {
        vol.Required("type"): "ezaiot/status",
    }
)
@websocket_api.async_response
async def websocket_get_status(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, object],
) -> None:
    """Return only redacted compatibility and update-source state."""
    records: list[dict[str, object]] = []
    for entry_data in hass.data.get(DOMAIN, {}).values():
        coordinator: EzaiotCoordinator = entry_data[DATA_COORDINATOR]
        records.extend(
            {
                "ordinal": record.ordinal,
                "manufacturer": record.manufacturer,
                "model": record.model,
                "entity_count": record.entity_count,
            }
            for record in coordinator.data.records
        )

    connection.send_result(
        msg["id"],
        {
            "integration_version": INTEGRATION_VERSION,
            "supported_count": len(records),
            "records": records,
            "update_source": {
                "state": "not_configured",
                "message": "GitHub release source is not configured.",
            },
        },
    )


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register panel commands once while the integration is loaded."""
    if hass.data.get(DATA_WEBSOCKET_REGISTERED):
        return
    websocket_api.async_register_command(hass, websocket_get_status)
    hass.data[DATA_WEBSOCKET_REGISTERED] = True
