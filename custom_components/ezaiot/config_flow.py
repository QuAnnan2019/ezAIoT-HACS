"""Config and Options flows for ezAIoT."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN
from .support import support_placeholders


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the local-only integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, object] | None = None):
        """Create the singleton entry without collecting user data."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="ezAIoT", data={})

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EzaiotOptionsFlow:
        """Return the no-input Options flow."""
        return EzaiotOptionsFlow()


class EzaiotOptionsFlow(config_entries.OptionsFlow):
    """Show local operation and support guidance without collecting data."""

    async def async_step_init(self, user_input: dict[str, object] | None = None):
        """Show a no-input Options page."""
        if user_input is not None:
            return self.async_create_entry(title="", data={})
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description_placeholders=support_placeholders(),
        )
