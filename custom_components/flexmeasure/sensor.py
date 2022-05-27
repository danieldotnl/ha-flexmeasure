"""Sensor platform for FlexMeasure. Code partially based on/inspired by the HA utility meter."""
from __future__ import annotations

import logging

from custom_components.flexmeasure.const import DOMAIN_DATA
from homeassistant.components.sensor import (
    RestoreSensor,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SOURCE
from .const import CONF_TARGET
from .const import ICON
from .const import SENSOR


_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup sensor platform."""
    entry_id = config_entry.entry_id
    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    source_entity_id = er.async_validate_entity_id(
        registry, config_entry.options[CONF_SOURCE]
    )
    target_sensor_name = config_entry.options[CONF_TARGET]

    sensor = FlexMeasureSensor(entry_id, source_entity_id, target_sensor_name)
    hass.data[DOMAIN_DATA][entry_id][SENSOR] = sensor
    async_add_entities([sensor])


class FlexMeasureSensor(RestoreSensor):
    """integration_blueprint Sensor class."""

    def __init__(self, entry_id, source_entity_id, sensor_name):
        self.source_sensor_id = source_entity_id
        self._attr_name = sensor_name
        self._unit_of_measurement = None
        self._attr_unique_id = entry_id

        self._collecting = None
        self._state = None
        self._attr_native_value = None
        self._attr_icon = ICON

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()

    def start_measuring(self, event):
        _LOGGER.debug("(Re)START measuring %s. Event: %s", self.source_sensor_id, event)

    def stop_measuring(self, event):
        _LOGGER.debug("(Re)STOP measuring %s. Event: %s", self.source_sensor_id, event)
