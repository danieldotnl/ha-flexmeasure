"""Adds config flow for FlexMeasure."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from typing import cast

import voluptuous as vol
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import SchemaConfigFlowHandler
from homeassistant.helpers.schema_config_entry_flow import SchemaFlowFormStep
from homeassistant.helpers.schema_config_entry_flow import SchemaFlowMenuStep

from .const import CONF_SOURCE
from .const import CONF_TARGET
from .const import DOMAIN

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
        vol.Required(CONF_SOURCE): selector.EntitySelector(),
        vol.Required(CONF_TARGET): selector.TextSelector(),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SOURCE): selector.EntitySelector(),
        vol.Required(CONF_TARGET): selector.TextSelector(),
    }
)

CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "user": SchemaFlowFormStep(CONFIG_SCHEMA)
}

OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA)
}


class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""

        return cast(str, options[CONF_NAME])


# class FlexMeasureFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
#     """Config flow for Blueprint."""

#     VERSION = 1
#     CONNECTION_CLASS = config_entries.CONN_CLASS_ASSUMED

#     def __init__(self):
#         """Initialize."""
#         self._errors = {}

#     async def async_step_user(self, user_input=None):
#         """Handle a flow initialized by the user."""
#         self._errors = {}

#         # Uncomment the next 2 lines if only a single instance of the integration is allowed:
#         # if self._async_current_entries():
#         #     return self.async_abort(reason="single_instance_allowed")

#         if user_input is not None:
#             valid = True
#             # valid = await self._test_credentials(
#             #     user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
#             # )
#             if valid:
#                 return self.async_create_entry(
#                     title=user_input[CONF_TARGET], data=user_input
#                 )
#             else:
#                 self._errors["base"] = "auth"

#             return await self._show_config_form(user_input)

#         user_input = {}

#         return await self._show_config_form(user_input)

#     # @staticmethod
#     # @callback
#     # def async_get_options_flow(config_entry):
#     #     return FlexMeasureOptionsFlowHandler(config_entry)

#     async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
#         """Show the configuration form to edit location data."""
#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema(
#                 {
#                     vol.Required(CONF_SOURCE): selector.EntitySelector(),
#                     vol.Optional(
#                         CONF_EXPRESSION, default=None
#                     ): selector.TemplateSelector(),
#                     vol.Required(CONF_TARGET): selector.TextSelector(),
#                 }
#             ),
#             errors=self._errors,
#         )


# class FlexMeasureFlowHandler(config_entries.OptionsFlow):
#     """Blueprint config flow options handler."""

#     def __init__(self, config_entry):
#         """Initialize HACS options flow."""
#         self.config_entry = config_entry
#         self.options = dict(config_entry.options)

#     async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
#         """Manage the options."""
#         return await self.async_step_user()

#     async def async_step_user(self, user_input=None):
#         """Handle a flow initialized by the user."""
#         if user_input is not None:
#             self.options.update(user_input)
#             return await self._update_options()

#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema(
#                 {
#                     vol.Required(x, default=self.options.get(x, True)): bool
#                     for x in sorted(PLATFORMS)
#                 }
#             ),
#         )

#     async def _update_options(self):
#         """Update config entry options."""
#         return self.async_create_entry(
#             title=self.config_entry.data.get(CONF_USERNAME), data=self.options
#         )