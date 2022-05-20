"""Sensor platform for integration_blueprint."""
from homeassistant.components.sensor import SensorEntity

from .const import DEFAULT_NAME
from .const import ICON
from .const import SENSOR
from .entity import FlexMeasureEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    async_add_devices([FlexMeasureSensor(entry)])


class FlexMeasureSensor(FlexMeasureEntity, SensorEntity):
    """integration_blueprint Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{SENSOR}"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return "test_native_value"

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON
