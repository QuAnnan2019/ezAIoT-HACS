from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_USER

from custom_components.ezaiot.const import DOMAIN


async def test_user_flow_creates_single_config_entry(
    hass, enable_custom_integrations
):
    with patch(
        "homeassistant.components.http.HomeAssistantHTTP.start",
        new=AsyncMock(),
    ), patch(
        "homeassistant.components.http.async_get_source_ip",
        new=AsyncMock(return_value="127.0.0.1"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == "ezAIoT"
    assert result["data"] == {}


async def test_second_user_flow_aborts(
    hass, enable_custom_integrations
):
    with patch(
        "homeassistant.components.http.HomeAssistantHTTP.start",
        new=AsyncMock(),
    ), patch(
        "homeassistant.components.http.async_get_source_ip",
        new=AsyncMock(return_value="127.0.0.1"),
    ):
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        await hass.async_block_till_done()

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
