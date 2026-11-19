"""Register the ezAIoT sidebar panel and its local static module."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import (
    DATA_PANEL_REGISTERED,
    DATA_PANEL_STATIC_REGISTERED,
    PANEL_COMPONENT_NAME,
    PANEL_MODULE_URL,
    PANEL_URL_PATH,
)

_STATIC_URL_PATH = "/ezaiot-panel"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the local panel module and the ezAIoT sidebar entry."""
    if not hass.data.get(DATA_PANEL_STATIC_REGISTERED):
        frontend_path = Path(__file__).parent / "frontend"
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_STATIC_URL_PATH, str(frontend_path), cache_headers=False)]
        )
        hass.data[DATA_PANEL_STATIC_REGISTERED] = True

    if hass.data.get(DATA_PANEL_REGISTERED):
        return

    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_COMPONENT_NAME,
        sidebar_title="ezAIoT",
        sidebar_icon="mdi:zigbee",
        module_url=PANEL_MODULE_URL,
        embed_iframe=False,
        require_admin=False,
    )
    hass.data[DATA_PANEL_REGISTERED] = True


def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the sidebar entry after the last config entry unloads."""
    if hass.data.pop(DATA_PANEL_REGISTERED, None):
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
