"""Sensor platform for FlexMeasure. Code partially based on/inspired by the HA utility meter."""
from __future__ import annotations

import logging
from decimal import Decimal
from decimal import DecimalException

import homeassistant.util.dt as dt_util
from custom_components.flexmeasure.const import CONF_SENSOR_TYPE
from custom_components.flexmeasure.const import DOMAIN_DATA
from homeassistant.components.sensor import (
    RestoreSensor,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_SOURCE
from .const import CONF_TARGET
from .const import CONF_TEMPLATE
from .const import ICON
from .const import SENSOR
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

    if sensor_type == SENSOR_TYPE_TIME:
        sensor = FlexMeasureTimeSensor(entry_id, target_sensor_name, template)

    elif sensor_type == SENSOR_TYPE_SOURCE:
        registry = er.async_get(hass)
        # Validate + resolve entity registry id to entity_id
        source_entity_id = er.async_validate_entity_id(
            registry, config_entry.options[CONF_SOURCE]
        )

        sensor = FlexMeasureSourceSensor(
            entry_id, target_sensor_name, template, source_entity_id
        )

    hass.data[DOMAIN_DATA][entry_id][SENSOR] = sensor
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


class FlexMeasureSourceSensor(RestoreSensor):
    """FlexMeasure Source Sensor class."""

    def __init__(self, entry_id, sensor_name, template, source_entity_id):
        self._source_sensor_id = source_entity_id
        self._template = template
        self._attr_name = sensor_name
        self._unit_of_measurement = None
        self._attr_unique_id = entry_id

        self._tracking = None
        self._start_source_value = None
        self._current_source_value = None
        self._attr_native_value = 0
        self._attr_icon = ICON

    def start_measuring(self, **kwargs):
        self._start_source_value = self.hass.states.get(self._source_sensor_id).state
        _LOGGER.debug(
            "(Re)START measuring %s at value: %s",
            self._source_sensor_id,
            self._start_source_value,
        )

        self._tracking = async_track_state_change_event(
            self.hass, [self._source_sensor_id], self.async_reading
        )

    async def stop_measuring(self, **kwargs):
        self._current_source_value = self.hass.states.get(self._source_sensor_id).state
        _LOGGER.debug(
            "(Re)STOPPED measuring %s at value: %s",
            self._source_sensor_id,
            self._current_source_value,
        )
        self._tracking()

    @callback
    def async_reading(self, event):
        """Handle the sensor state changes."""

        try:

            old_state = Decimal(event.data.get("old_state").state)
            new_state = Decimal(event.data.get("new_state").state)

            diff = new_state - old_state
            self._attr_native_value = self._attr_native_value + diff

            _LOGGER.debug("Old state: %s, new state: %s", old_state, new_state)

            self.async_write_ha_state()
        except DecimalException as err:
            _LOGGER.error("Invalid adjustment of %s: %s", new_state.state, err)


class FlexMeasureTimeSensor(RestoreSensor):
    """FlexMeasure Time Sensor class."""

    def __init__(self, entry_id, sensor_name, template):
        self._template = template
        self._attr_name = sensor_name
        self._unit_of_measurement = None
        self._attr_unique_id = entry_id

        self._tracking = None
        self._start_source_value = None
        self._current_source_value = None
        self._attr_native_value = 0
        self._attr_icon = ICON

    async def start_measuring(self):
        self._tracking = STATUS_MEASURING
        self._start_source_value = dt_util.as_timestamp(dt_util.now())
        _LOGGER.debug(
            "(Re)START measuring time at value: %s",
            self._start_source_value,
        )

    async def stop_measuring(self):
        if self._tracking == STATUS_MEASURING:
            diff = dt_util.as_timestamp(dt_util.now()) - self._start_source_value
            self._attr_native_value = self._attr_native_value + diff
            self._tracking = STATUS_INACTIVE

            _LOGGER.debug(
                "(Re)STOPPED measuring time at value: %s",
                self._attr_native_value,
            )
