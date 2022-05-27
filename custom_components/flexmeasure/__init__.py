"""
Custom integration to enable flexible measuring.

For more details about this integration, please refer to
https://github.com/custom-components/ha-flexmeasure
"""
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Config
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import CONF_SOURCE
from .const import DOMAIN_DATA

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""

    entity_registry = er.async_get(hass)
    hass.data[DOMAIN_DATA] = {}
    hass.data[DOMAIN_DATA][entry.entry_id] = {}

    try:
        er.async_validate_entity_id(entity_registry, entry.options[CONF_SOURCE])
    except vol.Invalid:
        # The entity is identified by an unknown entity registry ID
        _LOGGER.error(
            "Failed to setup FlexMeasure for unknown entity %s",
            entry.options[CONF_SOURCE],
        )
        return False

    hass.config_entries.async_setup_platforms(entry, ([Platform.SENSOR]))

    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))
    return True


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry,
        (Platform.SENSOR,),
    ):
        hass.data[DOMAIN_DATA].pop(entry.entry_id)

    return unload_ok
