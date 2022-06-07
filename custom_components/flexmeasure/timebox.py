from __future__ import annotations

import logging
from datetime import datetime
from datetime import timedelta

from croniter import croniter

_LOGGER: logging.Logger = logging.getLogger(__package__)


class Timebox:
    def __init__(
        self,
        reset_pattern: str,
        utcnow: datetime,
        duration: timedelta | None = None,
    ):
        self._reset_pattern = reset_pattern
        self._duration = duration

        self._session_state = 0
        self._box_state = 0
        self._prev_box_state = 0
        self._session_start_value: float | None = None
        self._box_state_start_value: float | None = None
        self._set_next_reset(utcnow)

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

    def update(self, value, utcnow):
        """Updates the state during measuring. Will be triggered every UPDATE_INTERVAL"""
        self._session_state = value - self._session_start_value
        self._box_state = self._box_state_start_value + self._session_state
        self.check_reset(value, utcnow)

    def check_reset(self, value, utcnow):
        if utcnow >= self._next_reset:
            self._prev_box_state, self._box_state = self._box_state, 0
            self._session_state = 0
            self._session_start_value = value
            self._box_state_start_value = self._box_state
            self._set_next_reset(utcnow)

    def _set_next_reset(self, utcnow):
        self.last_reset = utcnow.isoformat()
        self._next_reset = croniter(self._reset_pattern, utcnow).get_next(datetime)
