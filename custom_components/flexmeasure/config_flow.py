"""Adds config flow for FlexMeasure."""
from __future__ import annotations

from collections.abc import Callable
from collections.abc import Mapping
from typing import Any
from typing import cast

import voluptuous as vol
from homeassistant.const import CONF_VALUE_TEMPLATE
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import SchemaConfigFlowHandler
from homeassistant.helpers.schema_config_entry_flow import SchemaFlowFormStep
from homeassistant.helpers.schema_config_entry_flow import SchemaFlowMenuStep

from .const import CONF_SENSOR_TYPE
from .const import CONF_SOURCE
from .const import CONF_TARGET
from .const import CONF_TEMPLATE
from .const import DOMAIN
from .const import PREDEFINED_TIME_BOXES
from .const import SENSOR_TYPE_SOURCE
from .const import SENSOR_TYPE_TIME

SENSOR_TYPES_MENU = [SENSOR_TYPE_TIME, SENSOR_TYPE_SOURCE]


def set_sensor_type(sensor_type: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Set group type."""

    @callback
    def _set_sensor_type(user_input: dict[str, Any]) -> dict[str, Any]:
        """Add group type to user input."""
        return {CONF_SENSOR_TYPE: sensor_type, **user_input}

    return _set_sensor_type


GENERAL_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TARGET): selector.TextSelector(),
        vol.Optional(CONF_TEMPLATE): selector.TemplateSelector(),
        vol.Optional(CONF_VALUE_TEMPLATE): selector.TemplateSelector(),
    }
)

SOURCE_CONFIG_SCHEMA = GENERAL_CONFIG_SCHEMA.extend(
    {
        vol.Required(CONF_SOURCE): selector.EntitySelector(),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SOURCE): selector.EntitySelector(),
        vol.Required(CONF_TARGET): selector.TextSelector(),
    }
)

timebox_options = [
    selector.SelectOptionDict(value=x, label=x) for x in PREDEFINED_TIME_BOXES
]

TIMEBOXES_SCHEMA = vol.Schema(
    {
        vol.Optional("timeboxes"): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=timebox_options,
                mode=selector.SelectSelectorMode.LIST,
                multiple=True,
            )
        ),
    }
)

GENERAL_CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "user": SchemaFlowMenuStep(SENSOR_TYPES_MENU),
    SENSOR_TYPE_SOURCE: SchemaFlowFormStep(
        SOURCE_CONFIG_SCHEMA,
        set_sensor_type(SENSOR_TYPE_SOURCE),
        next_step=lambda x: "timeboxes",
    ),
    SENSOR_TYPE_TIME: SchemaFlowFormStep(
        GENERAL_CONFIG_SCHEMA,
        set_sensor_type(SENSOR_TYPE_TIME),
        next_step=lambda x: "timeboxes",
    ),
    "timeboxes": SchemaFlowFormStep(TIMEBOXES_SCHEMA),
}


OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA)
}


class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    config_flow = GENERAL_CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""

        return cast(str, options[CONF_TARGET])
