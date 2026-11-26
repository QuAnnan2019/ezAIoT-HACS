import asyncio
from types import SimpleNamespace

from custom_components.ezaiot.const import (
    DATA_COORDINATOR,
    DATA_RELEASE_SERVICE,
    DATA_WEBSOCKET_REGISTERED,
    DOMAIN,
)
from custom_components.ezaiot.models import (
    CompatibilityState,
    DiscoveryResult,
    SupportRecord,
)
from custom_components.ezaiot.release_models import ReleaseStatus, UnsignedReleaseState
from custom_components.ezaiot.websocket import (
    async_register_websocket_commands,
    websocket_download_diagnostics,
    websocket_get_status,
)


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
    release_state = UnsignedReleaseState(
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
                DATA_RELEASE_SERVICE: SimpleNamespace(state=release_state),
            }
        }
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
                "integration_version": "0.1.1",
            "supported_count": 1,
            "records": [
                {
                    "ordinal": 1,
                    "manufacturer": "Rti-Tek",
                    "model": "eTRV-ZB01",
                    "entity_count": 3,
                }
            ],
            "guidance": {
                "code": "restart_home_assistant",
                "title": "Restart Home Assistant",
                "message": (
                    "Keep this in configuration.yaml:\n"
                    "zha:\n"
                    "  custom_quirks_path: /config/zha_quirks\n\n"
                    "Restart Home Assistant to load the installed Quirk, then use "
                    "Reconfigure or re-pair the device."
                ),
                "actionable": True,
            },
            "update_source": {
                "state": "update_available",
                "installed_version": "0.0.1",
                "backup_version": "0.0.0",
                "available_version": "0.0.2",
                "release_notes": "Test change.",
                "restart_required": True,
                "message": "A test Release is ready to install.",
                "test_mode": True,
            },
        },
    )


def test_diagnostics_websocket_returns_shared_redacted_payload(monkeypatch) -> None:
    """The panel command must reuse the native diagnostic contract."""
    payload = {"integration_version": "0.1.1", "zha_devices": []}
    hass = SimpleNamespace(
        data={DOMAIN: {"entry-1": {DATA_COORDINATOR: object()}}}
    )
    connection = Connection()

    async def build_diagnostics(received_hass, entry):
        assert received_hass is hass
        assert entry.entry_id == "entry-1"
        return payload

    monkeypatch.setattr(
        "custom_components.ezaiot.websocket.async_build_diagnostics",
        build_diagnostics,
    )

    asyncio.run(
        websocket_download_diagnostics.__wrapped__.__wrapped__(
            hass,
            connection,
            {"id": 8, "type": "ezaiot/download_diagnostics"},
        )
    )

    assert connection.result == (8, payload)


def test_registers_diagnostics_websocket_once(monkeypatch) -> None:
    """The extra panel command follows the existing one-time registration rule."""
    registered = []
    hass = SimpleNamespace(data={})

    monkeypatch.setattr(
        "custom_components.ezaiot.websocket.websocket_api.async_register_command",
        lambda _hass, command: registered.append(command),
    )

    async_register_websocket_commands(hass)
    async_register_websocket_commands(hass)

    assert websocket_download_diagnostics in registered
    assert registered.count(websocket_download_diagnostics) == 1
    assert hass.data[DATA_WEBSOCKET_REGISTERED] is True
