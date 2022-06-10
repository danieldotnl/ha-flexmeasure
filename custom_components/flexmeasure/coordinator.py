import logging
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Callable
from typing import List

import homeassistant.util.dt as dt_util
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import callback
from homeassistant.core import CALLBACK_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.event import async_track_template_result
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.event import TrackTemplate
from homeassistant.helpers.storage import Store
from homeassistant.helpers.template import Template

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
        store: Store,
        timeboxes: List[Timebox],
        template: Template,
        value_callback: Callable[[str], NumberType],
    ) -> None:
        self._hass: HomeAssistant = hass
        self._store: Store = store
        self._timeboxes: dict[str, Timebox] = timeboxes
        self._template: Template = template
        self._get_value: Callable[[str], NumberType] = value_callback
        self._listeners: dict[CALLBACK_TYPE, tuple[CALLBACK_TYPE, object | None]] = {}

        self.status: str = STATUS_INACTIVE

        self._hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, self.async_init())

    async def async_init(self):
        await self.load_timeboxes()

        result = async_track_template_result(
            self._hass,
            [TrackTemplate(self._template, None)],
            self._async_on_template_update,
        )
        result.async_refresh()

        async_track_time_interval(self._hass, self.update_measurements, UPDATE_INTERVAL)
        await self.update_measurements()

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

    async def load_timeboxes(self):
        stored_data = await self._store.async_load()
        if stored_data:
            for timebox in self.timeboxes:
                Timebox.from_dict(stored_data[timebox.name], timebox)

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
                "Encountered a template error: %s. If we were measuring, we will now stop doing so.",
                result,
            )
            await self.stop_measuring()
        else:
            _LOGGER.debug("Template value changed into: %s", result)
            if result is True:
                await self.start_measuring()
            else:
                await self.stop_measuring()

        # if event:
        #     self.async_set_context(event.context)

    async def start_measuring(self):
        _LOGGER.debug("Start measuring!")
        if self.status == STATUS_INACTIVE:
            self.status = STATUS_MEASURING
            value = self._get_value()
            for timebox in self.timeboxes:
                timebox.start(value)
            self._update_listeners()
            await self._save_timeboxes()

    async def stop_measuring(self):
        if self.status == STATUS_MEASURING:
            self.status = STATUS_INACTIVE
            value = self._get_value()
            for timebox in self.timeboxes:
                timebox.stop(value)
            self._update_listeners()
            await self._save_timeboxes()

    def _update_listeners(self):
        for update_callback, _ in list(self._listeners.values()):
            update_callback()

    @callback
    async def update_measurements(self, now: datetime | None = None):
        _LOGGER.debug("Interval update triggered  at: %s.", now.isoformat())
        reset: bool = False
        value = self._get_value()
        now = dt_util.utcnow()

        if self.status == STATUS_MEASURING:
            for timebox in self.timeboxes:
                timebox.update(value, now)
        else:
            for timebox in self.timeboxes:
                if timebox.check_reset(value, now):
                    reset = True
        self._update_listeners()
        if reset is True:
            await self._save_timeboxes()

    async def _save_timeboxes(self) -> None:
        data = {}
        for timebox in self.timeboxes:
            data[timebox.name] = Timebox.to_dict(timebox)
        await self._store.async_save(data)
