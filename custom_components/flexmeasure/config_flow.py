"""Adds config flow for FlexMeasure."""
from __future__ import annotations

import logging

import voluptuous as vol
from croniter import croniter
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
from homeassistant.const import CONF_VALUE_TEMPLATE
from homeassistant.helpers import selector
from homeassistant.helpers.template import Template
from homeassistant.helpers.template import TemplateError

from .const import CONF_CONDITION
from .const import CONF_CRON
from .const import CONF_DURATION
from .const import CONF_METER_TYPE
from .const import CONF_PERIODS
from .const import CONF_SENSORS
from .const import CONF_SOURCE
from .const import CONF_TW_DAYS
from .const import CONF_TW_FROM
from .const import CONF_TW_TILL
from .const import DOMAIN
from .const import METER_TYPE_SOURCE
from .const import METER_TYPE_TIME
from .const import PREDEFINED_PERIODS


_LOGGER: logging.Logger = logging.getLogger(__name__)
METER_TYPES_MENU = ["time", "source"]
PERIOD_MENU = ["predefined", "custom"]
PERIOD_MENU_DONE = ["predefined", "custom", "done"]

PERIOD_OPTIONS = [
    # selector.SelectOptionDict(value="none", label="none (no reset)"),
    selector.SelectOptionDict(value="5m", label="5m"),
    selector.SelectOptionDict(value="hour", label="hour"),
    selector.SelectOptionDict(value="day", label="day"),
    selector.SelectOptionDict(value="week", label="week"),
    selector.SelectOptionDict(value="month", label="month"),
    selector.SelectOptionDict(value="year", label="year"),
]

DAY_OPTIONS = [
    selector.SelectOptionDict(value="0", label="monday"),
    selector.SelectOptionDict(value="1", label="tuesday"),
    selector.SelectOptionDict(value="2", label="wednesday"),
    selector.SelectOptionDict(value="3", label="thursday"),
    selector.SelectOptionDict(value="4", label="friday"),
    selector.SelectOptionDict(value="5", label="saturday"),
    selector.SelectOptionDict(value="6", label="sunday"),
]
DEFAULT_DAYS = ["0", "1", "2", "3", "4", "5", "6"]


class FlexMeasureConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    def __init__(self) -> None:
        super().__init__()
        self._sensor_config = {}
        self._data = {}
        self._data[CONF_SENSORS] = []

    def is_valid_cron(self, value: str) -> bool:
        return croniter.is_valid(value)

    def is_valid_template(self, value: str) -> bool:
        if not value:
            return True
        template = Template(value)
        try:
            template.ensure_valid()
            return True
        except TemplateError:
            return False

    async def async_step_user(self, user_input=None):
        return self.async_show_menu(step_id="user", menu_options=METER_TYPES_MENU)

    async def async_step_time(self, user_input=None):
        errors = {}
        if user_input is not None:
            if not self.is_valid_template(user_input.get(CONF_VALUE_TEMPLATE)):
                errors[CONF_VALUE_TEMPLATE] = "invalid template"

            if not errors:
                self._data[CONF_METER_TYPE] = METER_TYPE_TIME
                self._data[CONF_NAME] = user_input[CONF_NAME]
                self._sensor_config[CONF_UNIT_OF_MEASUREMENT] = user_input.get(
                    CONF_UNIT_OF_MEASUREMENT
                )
                self._sensor_config[CONF_VALUE_TEMPLATE] = user_input.get(
                    CONF_VALUE_TEMPLATE
                )
                return await self.async_step_when()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(),
                vol.Optional(CONF_UNIT_OF_MEASUREMENT): selector.TextSelector(),
                vol.Optional(CONF_VALUE_TEMPLATE): selector.TemplateSelector(),
            }
        )
        return self.async_show_form(step_id="time", data_schema=schema, errors=errors)

    async def async_step_source(self, user_input=None):
        errors = {}
        if user_input is not None:
            if not self.is_valid_template(user_input.get(CONF_VALUE_TEMPLATE)):
                errors[CONF_VALUE_TEMPLATE] = "invalid template"

            if not errors:
                self._data[CONF_METER_TYPE] = METER_TYPE_SOURCE
                self._data[CONF_NAME] = user_input[CONF_NAME]
                self._data[CONF_SOURCE] = user_input[CONF_SOURCE]
                self._sensor_config[CONF_UNIT_OF_MEASUREMENT] = user_input.get(
                    CONF_UNIT_OF_MEASUREMENT
                )
                self._sensor_config[CONF_VALUE_TEMPLATE] = user_input.get(
                    CONF_VALUE_TEMPLATE
                )
                return await self.async_step_when()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(),
                vol.Required(CONF_SOURCE): selector.EntitySelector(),
                vol.Optional(CONF_UNIT_OF_MEASUREMENT): selector.TextSelector(),
                vol.Optional(CONF_VALUE_TEMPLATE): selector.TemplateSelector(),
            }
        )
        return self.async_show_form(step_id="source", data_schema=schema, errors=errors)

    async def async_step_when(self, user_input=None):
        errors = {}
        _LOGGER.debug("User input: %s", user_input)

        if user_input is not None:
            if not self.is_valid_template(user_input.get(CONF_CONDITION)):
                errors[CONF_CONDITION] = "invalid_template"
            if not len(user_input.get(CONF_TW_DAYS)) > 0:
                errors[CONF_TW_DAYS] = "at_least_one_day"

            if not errors:
                self._data.update(user_input)
                return await self.async_step_periods()

        schema = vol.Schema(
            {
                vol.Optional(CONF_CONDITION): selector.TemplateSelector(),
                vol.Optional(
                    CONF_TW_DAYS, default=DEFAULT_DAYS
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=DAY_OPTIONS,
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    ),
                ),
                vol.Required(CONF_TW_FROM): selector.TimeSelector(),
                vol.Required(CONF_TW_TILL): selector.TimeSelector(),
            }
        )
        return self.async_show_form(step_id="when", data_schema=schema, errors=errors)

    async def async_step_periods(self, user_input=None):
        if len(self._data.get(CONF_SENSORS, 0)) > 0:
            return self.async_show_menu(
                step_id="periods", menu_options=PERIOD_MENU_DONE
            )
        return self.async_show_menu(step_id="periods", menu_options=PERIOD_MENU)

    async def async_step_predefined(self, user_input=None):
        errors = {}
        if user_input is not None:

            if not errors:
                _LOGGER.debug("Selected periods: %s.", user_input[CONF_PERIODS])
                for period in user_input[CONF_PERIODS]:
                    sensor = dict(self._sensor_config)
                    sensor[CONF_NAME] = period
                    sensor[CONF_CRON] = PREDEFINED_PERIODS[period]
                    self._data[CONF_SENSORS].append(sensor)
                _LOGGER.debug("Sensors: %s.", self._data)
                return await self.async_step_periods()

        schema = vol.Schema(
            {
                vol.Optional(CONF_PERIODS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=PERIOD_OPTIONS,
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(
            step_id="predefined", data_schema=schema, errors=errors
        )

    async def async_step_custom(self, user_input=None):

        errors = {}
        if user_input is not None:

            if not self.is_valid_cron(user_input[CONF_CRON]):
                errors[CONF_CRON] = "invalid cron pattern"
            if not self.is_valid_template(user_input.get(CONF_VALUE_TEMPLATE)):
                errors[CONF_VALUE_TEMPLATE] = "invalid template"

            if not errors:
                self._data[CONF_SENSORS].append(user_input)
                return await self.async_step_periods()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(),
                vol.Required(CONF_CRON): selector.TextSelector(),
                vol.Optional(CONF_DURATION): selector.DurationSelector(
                    selector.DurationSelectorConfig(enable_day=True)
                ),
                vol.Optional(CONF_UNIT_OF_MEASUREMENT): selector.TextSelector(),
                vol.Optional(CONF_VALUE_TEMPLATE): selector.TemplateSelector(),
            }
        )
        return self.async_show_form(step_id="custom", data_schema=schema, errors=errors)

    async def async_step_done(self, user_input=None):
        _LOGGER.debug("All stored data: %s", self._data)

        return self.async_create_entry(
            title=self._data[CONF_NAME], data={}, options=self._data
        )
