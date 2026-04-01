"""Config flow for Edesur."""

from __future__ import annotations

import logging

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .api import EdesurApi, EdesurAuthError
from .const import CONF_NIC, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_NIC): str,
    }
)


class EdesurConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Edesur."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            api = EdesurApi(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_NIC],
            )

            try:
                async with aiohttp.ClientSession() as session:
                    await api.authenticate(session)
            except EdesurAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(user_input[CONF_NIC])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Edesur ({user_input[CONF_NIC]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
