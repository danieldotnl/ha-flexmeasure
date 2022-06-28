"""Sensor platform for FlexMeasure"""
from __future__ import annotations

import logging
from typing import List

from custom_components.flexmeasure.const import CONF_SENSOR_TYPE
from custom_components.flexmeasure.const import PREDEFINED_PERIODS
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_VALUE_TEMPLATE
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_NEXT_RESET
from .const import ATTR_PREV
from .const import ATTR_STATUS
from .const import CONF_PERIODS
from .const import CONF_TARGET
from .const import DOMAIN_DATA
from .const import ICON
from .const import NAME
from .const import SENSOR_TYPE_TIME
from .coordinator import FlexMeasureCoordinator
from .meter import Meter
from .util import create_renderer

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup sensor platform."""
    entry_id: str = config_entry.entry_id
    sensor_type: str = config_entry.options[CONF_SENSOR_TYPE]
    target_sensor_name: str = config_entry.options[CONF_TARGET]
    value_template_renderer = create_renderer(
        hass, config_entry.options.get(CONF_VALUE_TEMPLATE)
    )

    coordinator = hass.data[DOMAIN_DATA][entry_id]

    sensors: List[FlexMeasureSensor] = []

    for box in config_entry.options[CONF_PERIODS]:
        sensors.append(
            FlexMeasureSensor(
                coordinator,
                target_sensor_name,
                sensor_type,
                PREDEFINED_PERIODS[box][NAME],
                value_template_renderer,
            )
        )

    async_add_entities(sensors)


class FlexMeasureSensor(SensorEntity):
    def __init__(
        self,
        coordinator,
        sensor_name,
        sensor_type,
        pattern_name,
        value_template_renderer,
    ):
        self._sensor_type = sensor_type
        self._coordinator: FlexMeasureCoordinator = coordinator
        self._pattern_name = pattern_name
        self._attr_name = f"{sensor_name}_{pattern_name}"
        self._attr_unique_id = f"{sensor_name}_{pattern_name}"
        self._attr_icon = ICON
        self._attr_extra_state_attributes = {}
        self._value_template_renderer = value_template_renderer
        self._attr_state_class = SensorStateClass.TOTAL

        if self._sensor_type == SENSOR_TYPE_TIME:
            self._attr_device_class = SensorDeviceClass.DURATION

    async def async_added_to_hass(self):
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        meter: Meter = self._coordinator.get_meter(self._pattern_name)

        measured_value = meter.measured_value
        prev_measured_value = meter.prev_measured_value
        if self._sensor_type == SENSOR_TYPE_TIME:
            measured_value = round(measured_value)
            prev_measured_value = round(prev_measured_value)
        else:
            measured_value = round(measured_value, 2)
            prev_measured_value = round(prev_measured_value, 2)

        self._attr_native_value = self._value_template_renderer(measured_value)
        self._attr_extra_state_attributes[ATTR_STATUS] = meter.state
        self._attr_extra_state_attributes[ATTR_PREV] = self._value_template_renderer(
            prev_measured_value
        )
        self._attr_last_reset = meter.last_reset
        self._attr_extra_state_attributes[ATTR_NEXT_RESET] = meter.next_reset
        self.async_set_context(self._coordinator._context)

        self.async_write_ha_state()
