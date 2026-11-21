from homeassistant.config_entries import SOURCE_USER

from custom_components.ezaiot.const import DOMAIN


async def test_user_flow_creates_single_config_entry(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "ezAIoT"
    assert result["data"] == {}


async def test_second_user_flow_aborts(hass):
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "single_instance_allowed"
