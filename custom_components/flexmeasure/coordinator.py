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
from homeassistant.helpers.event import async_track_template_result
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.event import TrackTemplate
from homeassistant.helpers.storage import Store
from homeassistant.helpers.template import Template

from .const import ATTR_STATUS
from .const import DOMAIN_DATA
from .const import STATUS_INACTIVE
from .const import STATUS_MEASURING
from .timebox import Timebox
from .util import NumberType

UPDATE_INTERVAL = timedelta(minutes=1)
_LOGGER: logging.Logger = logging.getLogger(__package__)


class FlexMeasureCoordinator:
    def __init__(
        self,
        hass: HomeAssistant,
        config_name: str,
        store: Store,
        timeboxes: List[Timebox],
        template: Template | None,
        value_callback: Callable[[str], NumberType],
    ) -> None:
        self._hass: HomeAssistant = hass
        self._name: str = config_name
        self._store: Store = store
        self._timeboxes: dict[str, Timebox] = timeboxes
        self._template: Template | None = template
        self._get_value: Callable[[str], NumberType] = value_callback
        self._listeners: dict[CALLBACK_TYPE, tuple[CALLBACK_TYPE, object | None]] = {}
        self._context = None
        self.last_update_value = None

        self.status: str = STATUS_INACTIVE

    async def async_init(self):
        await self._from_storage()

        if self._template:
            result = async_track_template_result(
                self._hass,
                [TrackTemplate(self._template, None)],
                self._async_on_template_update,
            )
            result.async_refresh()
        else:
            await self.start_measuring()

        async_track_time_interval(self._hass, self.update_measurements, UPDATE_INTERVAL)
        await self.update_measurements()  # initial update to reset timeboxes when needed

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

    def get_timebox(self, name: str) -> Timebox:
        return self._timeboxes[name]

    @property
    def timeboxes(self) -> List[Timebox]:
        return self._timeboxes.values()

    @callback
    async def _async_on_template_update(self, event, updates):
        """Update ha state when dependencies update."""
        result = updates.pop().result

        if isinstance(result, TemplateError):
            _LOGGER.error(
                "%s # Encountered a template error: %s. If we were measuring, we will now stop doing so.",
                self._name,
                result,
            )
            await self.stop_measuring()
        else:
            _LOGGER.debug("%s # Template value changed into: %s", self._name, result)
            if result is True:
                await self.start_measuring()
            else:
                await self.stop_measuring()

        if event:
            self._context = event.context

    async def start_measuring(self):
        _LOGGER.debug("%s # Start measuring!", self._name)
        if self.status == STATUS_INACTIVE:
            try:
                value = self._parse_value(self._get_value())
            except ValueError as ex:
                _LOGGER.error(
                    "%s # Could not start measuring because the input value is invalid. Error: %s",
                    self._name,
                    ex,
                )
                return

            for timebox in self.timeboxes:
                timebox.start(value)
            self.status = STATUS_MEASURING
            self.last_update_value = value
            self._update_listeners()
            await self._to_storage()

    async def stop_measuring(self):
        if self.status == STATUS_MEASURING:
            try:
                value = self._parse_value(self._get_value())
            except ValueError as ex:
                _LOGGER.error(
                    "%s # Could not stop measuring because the input value is invalid. Instead the latest update value will be used. Error: %s",
                    self._name,
                    ex,
                )
                value = self.last_update_value
                if not value:
                    _LOGGER.error(
                        "%s # Latest update value is empty. Zero will be used instead, resulting in an incorrect state.",
                        self._name,
                        value=0,
                    )

            for timebox in self.timeboxes:
                timebox.stop(value)
            self.status = STATUS_INACTIVE
            self.last_update_value = value
            self._update_listeners()
            await self._to_storage()

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

    @callback
    async def update_measurements(self, now: datetime | None = None):
        now = dt_util.now()
        _LOGGER.debug(
            "%s # Interval update triggered  at: %s.", self._name, now.isoformat()
        )
        reset: bool = False
        value = None
        try:
            value = self._parse_value(self._get_value())
        except ValueError as ex:
            _LOGGER.warning("%s # Could not update sensors: %s", self._name, ex)
            return

        if self.status == STATUS_MEASURING:
            for timebox in self.timeboxes:
                timebox.update(value, now)
        else:
            for timebox in self.timeboxes:
                if timebox.check_reset(value, now):
                    reset = True
        self.last_update_value = value
        self._update_listeners()
        if reset is True:
            await self._to_storage()

    async def _from_storage(self):
        try:
            stored_data = await self._store.async_load()
            if stored_data:
                self.status = stored_data.get(DOMAIN_DATA)
                for timebox in self.timeboxes:
                    Timebox.from_dict(stored_data[timebox.name], timebox)
        except Exception as ex:
            _LOGGER.error(
                "%s # Loading component state from disk failed with error: %s",
                self._name,
                ex,
            )

    async def _to_storage(self) -> None:
        try:
            data = {}
            for timebox in self.timeboxes:
                data[timebox.name] = Timebox.to_dict(timebox)
            data[ATTR_STATUS] = self.status
            await self._store.async_save(data)
        except Exception as ex:
            _LOGGER.error(
                "%s # Saving component state to disk failed with error: %s",
                self._name,
                ex,
            )
