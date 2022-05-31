"""Sensor platform for FlexMeasure. Code partially based on/inspired by the HA utility meter."""
from __future__ import annotations

import logging
from decimal import Decimal
from decimal import DecimalException

import homeassistant.util.dt as dt_util
from custom_components.flexmeasure.const import CONF_SENSOR_TYPE
from homeassistant.components.sensor import (
    RestoreSensor,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import entity_platform
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_template_result
from homeassistant.helpers.event import TrackTemplate
from homeassistant.helpers.template import Template

from .const import CONF_SOURCE
from .const import CONF_TARGET
from .const import CONF_TEMPLATE
from .const import ICON
from .const import SENSOR_TYPE_SOURCE
from .const import SENSOR_TYPE_TIME
from .const import SERVICE_START
from .const import SERVICE_STOP
from .const import STATUS_INACTIVE
from .const import STATUS_MEASURING


_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup sensor platform."""
    entry_id: str = config_entry.entry_id
    sensor_type: str = config_entry.options[CONF_SENSOR_TYPE]
    target_sensor_name: str = config_entry.options[CONF_TARGET]
    template: str | None = config_entry.options.get(CONF_TEMPLATE)
    activation_template: Template | None = None

    if template:
        activation_template = Template(template)

    if sensor_type == SENSOR_TYPE_TIME:
        sensor = FlexMeasureTimeSensor(
            entry_id, target_sensor_name, activation_template
        )

    elif sensor_type == SENSOR_TYPE_SOURCE:
        registry = er.async_get(hass)
        # Validate + resolve entity registry id to entity_id
        source_entity_id = er.async_validate_entity_id(
            registry, config_entry.options[CONF_SOURCE]
        )

        sensor = FlexMeasureSourceSensor(
            entry_id, target_sensor_name, activation_template, source_entity_id
        )

    async_add_entities([sensor])

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_START,
        {},
        "start_measuring",
    )

    platform.async_register_entity_service(
        SERVICE_STOP,
        {},
        "stop_measuring",
    )


class FlexMeasureSensor(RestoreSensor):
    def __init__(self, entry_id, sensor_name, template):
        self._template = template
        self._attr_name = sensor_name
        self._attr_unique_id = entry_id

        self._tracking = None
        self._start_source_value = None
        self._current_source_value = None
        self._attr_native_value = 0
        self._attr_icon = ICON

    async def async_added_to_hass(self):
        @callback
        def _async_on_template_update(event, updates):
            """Update ha state when dependencies update."""
            result = updates.pop().result

            if isinstance(result, TemplateError):
                _LOGGER.error(
                    "Encountered a template error: %s. If we were measuring, we will now stop doing so.",
                    result,
                )
                self.stop_measuring()
            else:
                _LOGGER.debug("Template value changed into: %s", result)
                if result is True:
                    self.start_measuring()
                else:
                    self.stop_measuring()

            if event:
                self.async_set_context(event.context)

            self.async_schedule_update_ha_state(True)

        if self._template is not None:
            result = async_track_template_result(
                self.hass,
                [TrackTemplate(self._template, None)],
                _async_on_template_update,
            )
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_START, callback(lambda _: result.async_refresh())
            )
            result.async_refresh()

            self.async_on_remove(result.async_remove)


class FlexMeasureSourceSensor(FlexMeasureSensor):
    """FlexMeasure Source Sensor class."""

    def __init__(self, entry_id, sensor_name, template, source_entity_id):
        super().__init__(entry_id, sensor_name, template)
        self._source_sensor_id = source_entity_id

        self._start_source_value = None
        self._current_source_value = None

    def start_measuring(self, **kwargs):
        self._start_source_value = self.hass.states.get(self._source_sensor_id).state
        _LOGGER.debug(
            "(Re)START measuring %s at value: %s",
            self._source_sensor_id,
            self._start_source_value,
        )

    def stop_measuring(self, **kwargs):
        try:

            self._current_source_value = Decimal(
                self.hass.states.get(self._source_sensor_id).state
            )
            diff = self._current_source_value - self._attr_native_value
            self._attr_native_value = self._attr_native_value + diff

            self.async_write_ha_state()
        except DecimalException as err:
            _LOGGER.error("Could not convert sensor value to decimal: %s", err)

        _LOGGER.debug(
            "(Re)STOPPED measuring %s at value: %s",
            self._source_sensor_id,
            self._current_source_value,
        )


class FlexMeasureTimeSensor(FlexMeasureSensor):
    """FlexMeasure Time Sensor class."""

    def start_measuring(self):
        self._tracking = STATUS_MEASURING
        self._start_source_value = dt_util.as_timestamp(dt_util.now())
        _LOGGER.debug(
            "(Re)START measuring time at value: %s",
            self._start_source_value,
        )

    def stop_measuring(self):
        if self._tracking == STATUS_MEASURING:
            diff = round(dt_util.as_timestamp(dt_util.now()) - self._start_source_value)
            self._attr_native_value = self._attr_native_value + diff
            self._tracking = STATUS_INACTIVE

            _LOGGER.debug(
                "(Re)STOPPED measuring time at value: %s",
                self._attr_native_value,
            )
        else:
            _LOGGER.warning("Stop measuring triggered, but sensor wasn't measuring.")
