"""Sensor platform for FlexMeasure"""
from __future__ import annotations

import logging
from typing import List

from custom_components.flexmeasure.const import CONF_SENSOR_TYPE
from custom_components.flexmeasure.const import PREDEFINED_TIME_BOXES
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_LAST_RESET
from .const import ATTR_NEXT_RESET
from .const import ATTR_PREV
from .const import ATTR_STATUS
from .const import CONF_TARGET
from .const import CONF_TIMEBOXES
from .const import DOMAIN_DATA
from .const import ICON
from .const import NAME
from .const import SENSOR_TYPE_TIME
from .coordinator import FlexMeasureCoordinator
from .timebox import Timebox

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

    coordinator = hass.data[DOMAIN_DATA][entry_id]

    sensors: List[FlexMeasureSensor] = []

    if sensor_type == SENSOR_TYPE_TIME:
        for box in config_entry.options[CONF_TIMEBOXES]:
            sensors.append(
                FlexMeasureSensor(
                    coordinator,
                    target_sensor_name,
                    sensor_type,
                    PREDEFINED_TIME_BOXES[box][NAME],
                )
            )

    async_add_entities(sensors)


class FlexMeasureSensor(SensorEntity):
    def __init__(self, coordinator, sensor_name, sensor_type, pattern_name):
        self._sensor_type = sensor_type
        self._coordinator: FlexMeasureCoordinator = coordinator
        self._pattern_name = pattern_name
        self._attr_name = f"{sensor_name}_{pattern_name}"
        self._attr_unique_id = f"{sensor_name}_{pattern_name}"
        self._attr_icon = ICON
        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self):
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        timebox: Timebox = self._coordinator.get_timebox(self._pattern_name)

        state = timebox.state
        prev_state = timebox.prev_state
        if self._sensor_type == SENSOR_TYPE_TIME:
            state = round(state)
            prev_state = round(prev_state)

        self._attr_native_value = state
        self._attr_extra_state_attributes[ATTR_STATUS] = self._coordinator.status
        self._attr_extra_state_attributes[ATTR_PREV] = prev_state
        self._attr_extra_state_attributes[ATTR_LAST_RESET] = timebox.last_reset
        self._attr_extra_state_attributes[ATTR_NEXT_RESET] = timebox._next_reset

        self.async_write_ha_state()
