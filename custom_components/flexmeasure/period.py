from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from typing import Callable

from croniter import croniter


class Period:
    def __init__(
        self, start_pattern: str, tznow: datetime, duration: timedelta | None = None
    ) -> None:
        self._start_pattern: str = start_pattern
        self._duration: timedelta = duration
        self.start: datetime = croniter(self._start_pattern, tznow).get_prev(datetime)
        self.end = self._determine_end()
        self.active = self._is_within_period(tznow)
        self.last_reset: datetime = tznow

    def update(self, tznow: datetime, reset_func: Callable, input_value: float):
        if self.end < tznow:
            self.last_reset = tznow
            if self._duration:
                self.start = croniter(self._start_pattern, tznow).get_next(datetime)
            else:
                self.start = self.end
            self.end = self._determine_end()
            reset_func(input_value)
        self.active = self._is_within_period(tznow)

    def _determine_end(self) -> datetime:
        if self._duration:
            end = self.start + self._duration
            if end > croniter(self._start_pattern, self.start).get_next(datetime):
                raise ValueError("Duration cannot be longer than pattern interval.")
            return end
        else:
            return croniter(self._start_pattern, self.start).get_next(datetime)

    def _is_within_period(self, tznow: datetime):
        return self.start <= tznow <= self.end
