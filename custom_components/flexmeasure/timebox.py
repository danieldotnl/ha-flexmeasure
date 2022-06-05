from __future__ import annotations

from datetime import datetime
from datetime import timedelta

from croniter import croniter


class Timebox:
    def __init__(
        self,
        name: str,
        reset_pattern: str,
        utcnow: datetime,
        duration: timedelta | None = None,
    ):
        self._name = name
        self._reset_pattern = reset_pattern
        self._duration = duration

        self._session_state = 0
        self._box_state = 0
        self._prev_box_state = 0
        self._session_start_value: float | None = None
        self._box_state_start_value: float | None = None
        self._set_next_reset(utcnow)

    def start(self, value):
        self._session_start_value = value
        self._box_state_start_value = self._box_state

    def stop(self, value):
        self._box_state = (
            self._box_state_start_value + value - self._session_start_value
        )
        self._session_start_value = None

    def update(self, value, utcnow):
        """Updates the state during measuring. Will be """
        self._session_state = value - self._session_start_value
        self._box_state = self._box_state_start_value + self._session_state
        if utcnow > self._next_reset:
            self.reset(value, utcnow)

    def reset(self, value, utcnow):
        self._prev_box_state, self._box_state = self._box_state, 0
        self._session_start_value = value
        self._box_state_start_value = self._box_state
        self._set_next_reset(utcnow)

    def to_attributes(self):
        return {
            f"current_{self._name}": self._box_state,
            f"prev_{self._name}": round(self._prev_box_state),
        }

    def _set_next_reset(self, utcnow):
        self._next_reset = croniter(self._reset_pattern, utcnow).get_next(datetime)
