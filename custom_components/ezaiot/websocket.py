"""Read-only WebSocket data for the ezAIoT sidebar panel."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import (
    DATA_COORDINATOR,
    DATA_RELEASE_COORDINATOR,
    DATA_RELEASE_SERVICE,
    DATA_WEBSOCKET_REGISTERED,
    DOMAIN,
    INTEGRATION_VERSION,
)
from .coordinator import EzaiotCoordinator
from .guidance import Guidance, async_sync_guidance_notification, build_guidance
from .models import CompatibilityState, DiscoveryResult
from .release_models import UnsignedReleaseState
from .release_service import UnsignedReleaseService


def _release_state_payload(state: UnsignedReleaseState) -> dict[str, object]:
    """Return the redacted test-mode state shared by all panel commands."""
    return {
        "state": state.status.value,
        "installed_version": state.installed_version,
        "backup_version": state.backup_version,
        "available_version": state.available_version,
        "release_notes": state.release_notes,
        "restart_required": state.restart_required,
        "message": state.message,
        "test_mode": True,
    }


def _guidance_payload(guidance: Guidance) -> dict[str, object]:
    """Return display-ready setup guidance without local registry data."""
    return {
        "code": guidance.code.value,
        "title": guidance.title,
        "message": guidance.message,
        "actionable": guidance.actionable,
    }


def _release_service(hass: HomeAssistant) -> UnsignedReleaseService:
    """Return the singleton service after integration setup is complete."""
    return hass.data[DOMAIN][DATA_RELEASE_SERVICE]


def _set_release_state(hass: HomeAssistant, state: UnsignedReleaseState) -> None:
    """Keep the Update entity in sync with panel-initiated operations."""
    coordinator = hass.data[DOMAIN].get(DATA_RELEASE_COORDINATOR)
    if coordinator is not None:
        coordinator.async_set_updated_data(state)


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
        if not isinstance(entry_data, dict) or DATA_COORDINATOR not in entry_data:
            continue
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

    release_state = _release_service(hass).state
    discovery = DiscoveryResult(
        state=(
            CompatibilityState.SUPPORTED if records else CompatibilityState.NOT_FOUND
        ),
        records=(),
    )
    connection.send_result(
        msg["id"],
        {
            "integration_version": INTEGRATION_VERSION,
            "supported_count": len(records),
            "records": records,
            "guidance": _guidance_payload(build_guidance(discovery, release_state)),
            "update_source": _release_state_payload(release_state),
        },
    )


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "ezaiot/check_release"})
@websocket_api.async_response
async def websocket_check_release(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, object],
) -> None:
    """Check the fixed test Release source at an administrator's request."""
    state = await _release_service(hass).async_check()
    _set_release_state(hass, state)
    _sync_guidance(hass)
    connection.send_result(msg["id"], _release_state_payload(state))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "ezaiot/install_release"})
@websocket_api.async_response
async def websocket_install_release(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, object],
) -> None:
    """Install the candidate selected by the latest administrator check."""
    state = await _release_service(hass).async_install()
    _set_release_state(hass, state)
    _sync_guidance(hass)
    connection.send_result(msg["id"], _release_state_payload(state))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "ezaiot/rollback_release"})
@websocket_api.async_response
async def websocket_rollback_release(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, object],
) -> None:
    """Restore the single ezAIoT-managed test Release backup."""
    state = await _release_service(hass).async_rollback()
    _set_release_state(hass, state)
    _sync_guidance(hass)
    connection.send_result(msg["id"], _release_state_payload(state))


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register panel commands once while the integration is loaded."""
    if hass.data.get(DATA_WEBSOCKET_REGISTERED):
        return
    websocket_api.async_register_command(hass, websocket_get_status)
    websocket_api.async_register_command(hass, websocket_check_release)
    websocket_api.async_register_command(hass, websocket_install_release)
    websocket_api.async_register_command(hass, websocket_rollback_release)
    hass.data[DATA_WEBSOCKET_REGISTERED] = True


def _sync_guidance(hass: HomeAssistant) -> None:
    """Synchronize guidance using the singleton entry's discovery result."""
    for entry_data in hass.data[DOMAIN].values():
        if isinstance(entry_data, dict) and DATA_COORDINATOR in entry_data:
            async_sync_guidance_notification(hass, entry_data[DATA_COORDINATOR].data)
            return
