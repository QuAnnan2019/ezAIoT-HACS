from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_USER

from custom_components.ezaiot.const import DOMAIN


async def test_user_flow_creates_single_config_entry(
    hass, enable_custom_integrations
):
    with patch("custom_components.ezaiot.async_register_panel", new=AsyncMock()):
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
    with patch("custom_components.ezaiot.async_register_panel", new=AsyncMock()):
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
