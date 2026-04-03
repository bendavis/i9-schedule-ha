"""Config flow for i9 Schedule integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_PRE_EVENT_MINUTES,
    CONF_PRE_EVENT_UPDATE,
    CONF_SCAN_INTERVAL,
    DEFAULT_PRE_EVENT_MINUTES,
    DEFAULT_PRE_EVENT_UPDATE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .i9_client import I9API, InvalidAuth

_LOGGER = logging.getLogger(__name__)


class I9ScheduleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for i9 Schedule."""

    VERSION = 1
    MINOR_VERSION = 0

    async def async_step_reconfigure(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle reconfiguration step to update credentials."""
        config_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        errors: Dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = I9API(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                session=session,
            )

            try:
                await api.authenticate()
                teams = await api.get_teams()

                if not teams:
                    errors["base"] = "no_teams"
                else:
                    self.hass.config_entries.async_update_entry(config_entry, data=user_input)
                    await self.hass.config_entries.async_reload(config_entry.entry_id)
                    return self.async_abort(reason="reconfigure_successful")

            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.error("Unexpected error during reconfigure: %s", err)
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_USERNAME,
                    default=config_entry.data.get(CONF_USERNAME),
                ): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "username": config_entry.data.get(CONF_USERNAME),
            },
        )

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Check for duplicate entry
            await self.async_set_unique_id(user_input[CONF_USERNAME])
            self._abort_if_unique_id_configured()

            # Validate credentials
            session = async_get_clientsession(self.hass)
            api = I9API(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                session=session,
            )

            try:
                await api.authenticate()
                teams = await api.get_teams()

                if not teams:
                    errors["base"] = "no_teams"
                else:
                    # Store data for next step
                    self._data = user_input
                    return self.async_create_entry(
                        title=user_input[CONF_USERNAME],
                        data=user_input,
                        options={
                            CONF_SCAN_INTERVAL: int(DEFAULT_SCAN_INTERVAL.total_seconds()),
                            CONF_PRE_EVENT_UPDATE: DEFAULT_PRE_EVENT_UPDATE,
                            CONF_PRE_EVENT_MINUTES: DEFAULT_PRE_EVENT_MINUTES,
                        },
                    )

            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.error("Unexpected error during auth: %s", err)
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={},
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return I9ScheduleOptionsFlow(config_entry)


class I9ScheduleOptionsFlow(config_entries.OptionsFlow):
    """Handle options for i9 Schedule."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle options step."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            int(DEFAULT_SCAN_INTERVAL.total_seconds()),
        )
        pre_event_update = self.config_entry.options.get(CONF_PRE_EVENT_UPDATE, DEFAULT_PRE_EVENT_UPDATE)
        pre_event_minutes = self.config_entry.options.get(CONF_PRE_EVENT_MINUTES, DEFAULT_PRE_EVENT_MINUTES)

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=scan_interval,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=300, max=86400),
                ),
                vol.Required(
                    CONF_PRE_EVENT_UPDATE,
                    default=pre_event_update,
                ): bool,
                vol.Required(
                    CONF_PRE_EVENT_MINUTES,
                    default=pre_event_minutes,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=5, max=1440),
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            description_placeholders={},
        )
