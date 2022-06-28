from __future__ import annotations

import logging
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Callable
from typing import get_args
from typing import List

import homeassistant.util.dt as dt_util
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.core import CALLBACK_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.event import async_track_template_result
from homeassistant.helpers.event import TrackTemplate
from homeassistant.helpers.storage import Store
from homeassistant.helpers.template import Template

from .meter import Meter
from .util import NumberType

UPDATE_INTERVAL = timedelta(minutes=1)
_LOGGER: logging.Logger = logging.getLogger(__name__)


class FlexMeasureCoordinator:
    def __init__(
        self,
        hass: HomeAssistant,
        config_name: str,
        store: Store,
        meters: List[Meter],
        template: Template | None,
        value_callback: Callable[[str], NumberType],
    ) -> None:
        self._hass: HomeAssistant = hass
        self._name: str = config_name
        self._store: Store = store
        self._meters: dict[str, Meter] = meters
        self._template: Template | None = template
        self._get_value: Callable[[str], NumberType] = value_callback
        self._listeners: dict[CALLBACK_TYPE, tuple[CALLBACK_TYPE, object | None]] = {}
        self._context = None
        self.last_update_value = None

    async def async_init(self):
        await self._async_from_storage()
        if not self._template:
            for meter in self.meters:
                meter.disable_template()

    async def async_start(self):
        if self._template:
            result = async_track_template_result(
                self._hass,
                [TrackTemplate(self._template, None)],
                self._async_on_template_update,
            )
            result.async_refresh()

        await self.async_on_heartbeat()

    @callback
    def async_add_listener(
        self, update_callback: CALLBACK_TYPE, context: Any = None
    ) -> Callable[[], None]:
        @callback
        def remove_listener() -> None:
            """Remove update listener."""
            self._listeners.pop(remove_listener)

        self._listeners[remove_listener] = (update_callback, context)

        update_callback()
        return remove_listener

    def get_meter(self, name: str) -> Meter:
        return self._meters[name]

    @property
    def meters(self) -> List[Meter]:
        return self._meters.values()

    async def _async_update_meters(self, template_result: bool | None = None):
        tznow = dt_util.now()
        trigger = (
            f"template changed to {template_result}"
            if template_result is not None
            else "update interval"
        )
        _LOGGER.debug(
            "%s # Update triggered at: %s by %s.",
            self._name,
            tznow.isoformat(),
            trigger,
        )

        try:
            input_value = self._parse_value(self._get_value())
        except ValueError as ex:
            _LOGGER.error(
                "%s # Could not update meters because the input value is invalid. Error: %s",
                self._name,
                ex,
            )
            # set the input value to the last updated value, so the meters are at least reset when required
            if self.last_update_value:
                input_value = self.last_update_value
            else:
                return  # nothing we can do... we'll try again next time

        if template_result is not None:
            for meter in self.meters:
                meter.on_template_change(tznow, input_value, template_result)
        else:
            for meter in self.meters:
                meter.on_heartbeat(tznow, input_value)

        self._update_listeners()
        await self._async_to_storage()

    @callback
    async def async_on_heartbeat(self, now: datetime | None = None):
        await self._async_update_meters()

        # We _floor_ utcnow to create a schedule on a rounded minute,
        # minimizing the time between the point and the real activation.
        # That way we obtain a constant update frequency,
        # as long as the update process takes less than a minute
        async_track_point_in_utc_time(
            self._hass,
            self.async_on_heartbeat,
            dt_util.utcnow().replace(second=0, microsecond=0) + UPDATE_INTERVAL,
        )

    @callback
    async def _async_on_template_update(self, event, updates):
        result = updates.pop().result

        if isinstance(result, TemplateError):
            _LOGGER.error(
                "%s # Encountered a template error: %s. Could not start or stop measuring!",
                self._name,
                result,
            )
        else:
            await self._async_update_meters(result)

        if event:
            self._context = event.context

    def _update_listeners(self):
        for update_callback, _ in list(self._listeners.values()):
            update_callback()

    def _parse_value(self, value: Any) -> NumberType | None:
        if isinstance(value, get_args(NumberType)):
            return value
        elif value in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            _LOGGER.debug(
                "%s # Error converting value %s to a number.", self._name, value
            )
            raise ValueError("Could not process value as it's unknown or unavailable.")
        else:
            return float(value)

    async def _async_from_storage(self):
        try:
            stored_data = await self._store.async_load()
            if stored_data:
                for meter in self.meters:
                    Meter.from_dict(stored_data[meter.name], meter)
        except Exception as ex:
            _LOGGER.error(
                "%s # Loading component state from disk failed with error: %s",
                self._name,
                ex,
            )

    async def _async_to_storage(self) -> None:
        try:
            data = {}
            for meter in self.meters:
                data[meter.name] = Meter.to_dict(meter)
            await self._store.async_save(data)
        except Exception as ex:
            _LOGGER.error(
                "%s # Saving component state to disk failed with error: %s",
                self._name,
                ex,
            )
