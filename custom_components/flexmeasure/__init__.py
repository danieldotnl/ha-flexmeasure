"""
Custom integration to enable flexible measuring.

For more details about this integration, please refer to
https://github.com/custom-components/ha-flexmeasure
"""
import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.const import Platform
from homeassistant.core import callback
from homeassistant.core import Config
from homeassistant.core import CoreState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util

from .const import CONF_CONDITION
from .const import CONF_CRON
from .const import CONF_DURATION
from .const import CONF_METER_TYPE
from .const import CONF_SENSORS
from .const import CONF_SOURCE
from .const import DOMAIN
from .const import DOMAIN_DATA
from .const import METER_TYPE_SOURCE
from .const import METER_TYPE_TIME
from .coordinator import FlexMeasureCoordinator
from .meter import Meter
from .period import Period

STORAGE_VERSION = 1
STORAGE_KEY_TEMPLATE = "{domain}_{entry_id}"

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""

    config_name: str = entry.options[CONF_NAME]
    meter_type: str = entry.options[CONF_METER_TYPE]
    condition: str | None = entry.options.get(CONF_CONDITION)

    def get_time_value():
        return dt_util.utcnow().timestamp()

    def get_source_value():
        return hass.states.get(source_entity).state

    if meter_type == METER_TYPE_TIME:
        value_callback = get_time_value
    elif meter_type == METER_TYPE_SOURCE:

        registry = er.async_get(hass)

        try:
            source_entity = er.async_validate_entity_id(
                registry, entry.options[CONF_SOURCE]
            )
        except vol.Invalid:
            # The entity is identified by an unknown entity registry ID
            _LOGGER.error(
                "%s # Failed to setup FlexMeasure for unknown entity %s",
                config_name,
                entry.options[CONF_SOURCE],
            )
            return False

        value_callback = get_source_value

    if condition:
        condition = Template(condition)
        condition.ensure_valid()

    store = Store(
        hass,
        STORAGE_VERSION,
        STORAGE_KEY_TEMPLATE.format(domain=DOMAIN, entry_id=entry.entry_id),
    )

    meters = {}
    now = dt_util.now()

    for sensor in entry.options[CONF_SENSORS]:
        duration = None
        if sensor.get(CONF_DURATION):
            duration = cv.time_period_dict(sensor.get(CONF_DURATION))
        period = Period(sensor[CONF_CRON], now, duration)
        meters[sensor[CONF_NAME]] = Meter(f"{config_name}_{sensor[CONF_NAME]}", period)

    coordinator = FlexMeasureCoordinator(
        hass, config_name, store, meters, condition, value_callback
    )
    await coordinator.async_init()

    @callback
    async def run_start(event):
        await coordinator.async_start()

    if not hass.state == CoreState.running:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, run_start)
    else:
        await run_start(None)

    hass.data.setdefault(DOMAIN_DATA, {})[entry.entry_id] = coordinator
    hass.config_entries.async_setup_platforms(entry, ([Platform.SENSOR]))

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
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
