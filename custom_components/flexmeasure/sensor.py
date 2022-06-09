"""Sensor platform for FlexMeasure"""
from __future__ import annotations

import logging
from datetime import datetime
from datetime import timedelta
from typing import List

import homeassistant.util.dt as dt_util
from custom_components.flexmeasure.const import CONF_SENSOR_TYPE
from custom_components.flexmeasure.const import PREDEFINED_TIME_BOXES
from homeassistant.components.sensor import (
    RestoreSensor,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_template_result
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.event import TrackTemplate
from homeassistant.helpers.template import Template

from .const import ATTR_LAST_RESET
from .const import ATTR_PREV
from .const import ATTR_STATUS
from .const import CONF_TARGET
from .const import CONF_TEMPLATE
from .const import CONF_TIMEBOXES
from .const import ICON
from .const import NAME
from .const import PATTERN
from .const import SENSOR_TYPE_TIME
from .const import SERVICE_START
from .const import SERVICE_STOP
from .const import STATUS_INACTIVE
from .const import STATUS_MEASURING
from .timebox import Timebox
from .util import NumberType

# from homeassistant.helpers import entity_registry as er

UPDATE_INTERVAL = timedelta(minutes=1)
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

    sensors: List[FlexMeasureSensor] = []

    if sensor_type == SENSOR_TYPE_TIME:
        for box in config_entry.options[CONF_TIMEBOXES]:
            sensors.append(
                FlexMeasureTimeSensor(
                    entry_id,
                    target_sensor_name,
                    activation_template,
                    PREDEFINED_TIME_BOXES[box],
                )
            )

    # elif sensor_type == SENSOR_TYPE_SOURCE:
    #     registry = er.async_get(hass)
    #     # Validate + resolve entity registry id to entity_id
    #     source_entity_id = er.async_validate_entity_id(
    #         registry, config_entry.options[CONF_SOURCE]
    #     )

    #     sensor = FlexMeasureSourceSensor(
    #         entry_id, target_sensor_name, activation_template, source_entity_id
    #     )

    async_add_entities(sensors)

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
    def __init__(self, entry_id, sensor_name, template, reset_pattern):
        self._template = template
        self._timebox = Timebox(reset_pattern[PATTERN], dt_util.utcnow())

        self._attr_name = f"{sensor_name}_{reset_pattern[NAME]}"
        self._attr_unique_id = f"{sensor_name}_{reset_pattern[NAME]}"
        self._status = STATUS_INACTIVE
        self._attr_icon = ICON
        self._attr_extra_state_attributes = {}

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

            self.async_on_remove(
                async_track_time_interval(
                    self.hass, self.update_measurements, UPDATE_INTERVAL
                )
            )

            self.async_on_remove(result.async_remove)

    def get_value(self):
        raise NotImplementedError

    def _set_state(self) -> None:
        self._attr_native_value = self._timebox.state
        self._attr_extra_state_attributes[ATTR_STATUS] = self._status
        self._attr_extra_state_attributes[ATTR_PREV] = self._timebox.prev_state
        self._attr_extra_state_attributes[ATTR_LAST_RESET] = self._timebox.last_reset
        self._attr_extra_state_attributes["next_reset"] = self._timebox._next_reset

    def start_measuring(self):
        if self._status == STATUS_INACTIVE:
            self._status = STATUS_MEASURING
            value = self.get_value()
            self._timebox.start(value)
            self._set_state()

    def stop_measuring(self):
        if self._status == STATUS_MEASURING:
            self._status = STATUS_INACTIVE
            value = self.get_value()
            self._timebox.stop(value)
            self._set_state()

    @callback
    def update_measurements(self, now: datetime | None = None):
        _LOGGER.debug("Interval update triggered  at: %s.", now)

        value = self.get_value()
        if self._status == STATUS_MEASURING:
            self._timebox.update(value, now)
        else:
            self._timebox.check_reset(value, now)
        self._set_state()


class FlexMeasureTimeSensor(FlexMeasureSensor):
    def get_value(self) -> NumberType:
        return dt_util.utcnow().timestamp()

    def _set_state(self) -> None:
        self._attr_native_value = round(self._timebox.state)
        self._attr_extra_state_attributes[ATTR_STATUS] = self._status
        self._attr_extra_state_attributes[ATTR_PREV] = round(self._timebox.prev_state)
        self._attr_extra_state_attributes[ATTR_LAST_RESET] = self._timebox.last_reset
        self._attr_extra_state_attributes["next_reset"] = self._timebox._next_reset


# class FlexMeasureSourceSensor(FlexMeasureSensor):
#     def get_value(self) -> NumberType:
#         return

#     def __init__(self, entry_id, sensor_name, template, source_entity_id):
#         super().__init__(entry_id, sensor_name, template, [])
#         self._source_sensor_id = source_entity_id

#     def determine_start_value(self) -> Decimal:
#         return Decimal(self.hass.states.get(self._source_sensor_id).state)

#     def determine_session_diff(self):
#         try:
#             current_value = Decimal(self.hass.states.get(self._source_sensor_id).state)
#             return current_value - self._session_start_value

#         except DecimalException as err:
#             _LOGGER.error("Could not convert sensor value to decimal: %s", err)
#             # raise DetermineDiffError(err)
