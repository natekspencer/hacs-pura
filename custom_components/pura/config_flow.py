"""Pura config flow."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from pypura import Pura, PuraAuthenticationError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)


class PuraConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pura."""

    VERSION = 1

    async def _async_create_entry(self, user_input: dict[str, Any]) -> FlowResult:
        """Create the config entry."""
        existing_entry = await self.async_set_unique_id(DOMAIN)

        config_data = {k: v for k, v in user_input.items() if k != CONF_PASSWORD}

        if existing_entry:
            self.hass.config_entries.async_update_entry(
                existing_entry, data=config_data
            )
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        return self.async_create_entry(
            title=config_data[CONF_USERNAME], data=config_data
        )

    async def async_pura_login(
        self, step_id, user_input: dict[str, Any] | None, schema: vol.Schema
    ) -> FlowResult:
        """Attempt a login with Pura."""
        errors = {}

        pura = Pura(username=user_input[CONF_USERNAME])
        try:
            await self.hass.async_add_executor_job(
                pura.authenticate, user_input[CONF_PASSWORD]
            )
        except PuraAuthenticationError:
            errors["base"] = "invalid_auth"
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.exception(ex)
            errors["base"] = "unknown"

        if not errors:
            return await self._async_create_entry(user_input | pura.get_tokens())

        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            for entry in self._async_current_entries():
                if entry.data[CONF_USERNAME] == user_input[CONF_USERNAME]:
                    return self.async_abort(reason="already_configured")

            return await self.async_pura_login(
                step_id="user", user_input=user_input, schema=STEP_USER_DATA_SCHEMA
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm(user_input)

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            user_input = {}

        reauth_schema = vol.Schema(
            {
                vol.Required(
                    CONF_USERNAME,
                    default=user_input.get(
                        CONF_USERNAME, self.init_data.get(CONF_USERNAME)
                    ),
                ): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        if user_input.get(CONF_PASSWORD) is None:
            return self.async_show_form(
                step_id="reauth_confirm", data_schema=reauth_schema
            )

        return await self.async_pura_login(
            step_id="reauth_confirm", user_input=user_input, schema=reauth_schema
        )
