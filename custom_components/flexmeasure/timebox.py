from __future__ import annotations

from datetime import datetime
from datetime import timedelta

from croniter import croniter
from homeassistant.util import dt as dt_util

# import logging

# _LOGGER: logging.Logger = logging.getLogger(__package__)


class Timebox:
    def __init__(
        self,
        name: str,
        reset_pattern: str,
        tznow: datetime,
        duration: timedelta | None = None,
    ):
        self.name = name
        self._reset_pattern = reset_pattern
        self._duration = duration

        self._box_state = 0
        self._prev_box_state = 0
        self._session_start_value: float | None = None
        self._box_state_start_value: float | None = None
        self.last_reset = None
        self.next_reset = None
        self._set_next_reset(tznow)

    @property
    def state(self):
        return self._box_state

    @property
    def prev_state(self):
        return self._prev_box_state

    def start(self, value):
        self._session_start_value = value
        self._box_state_start_value = self._box_state

    def stop(self, value):
        self._box_state = (
            self._box_state_start_value + value - self._session_start_value
        )
        self._session_start_value = None

    def update(self, value, tznow):
        """Updates the state during measuring. Will be triggered every UPDATE_INTERVAL"""
        session_state = value - self._session_start_value
        self._box_state = self._box_state_start_value + session_state
        self.check_reset(value, tznow)

    def check_reset(self, value, tznow) -> bool:
        if tznow >= self.next_reset:
            self._prev_box_state, self._box_state = self._box_state, 0
            self._session_start_value = value
            self._box_state_start_value = self._box_state
            self._set_next_reset(tznow)
            return True
        return False

    def _set_next_reset(self, tznow: datetime):
        self.last_reset = tznow
        self.next_reset = croniter(self._reset_pattern, tznow).get_next(datetime)

    @classmethod
    def to_dict(cls, timebox: Timebox) -> dict[str, str]:
        data = {
            "box_state": timebox._box_state,
            "box_state_start_value": timebox._box_state_start_value,
            "prev_box_state": timebox._prev_box_state,
            "session_start_value": timebox._session_start_value,
            "next_reset": dt_util.as_timestamp(timebox.next_reset),
            "last_reset": dt_util.as_timestamp(timebox.last_reset),
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, str], timebox: Timebox) -> Timebox:
        timebox._box_state = data["box_state"]
        timebox._box_state_start_value = data["box_state_start_value"]
        timebox._prev_box_state = data["prev_box_state"]
        timebox._session_start_value = data["session_start_value"]
        timebox.next_reset = dt_util.utc_from_timestamp(data["next_reset"])
        timebox.last_reset = dt_util.utc_from_timestamp(data.get("last_reset"))

        return timebox
