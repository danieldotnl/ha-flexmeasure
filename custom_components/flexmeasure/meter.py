from __future__ import annotations

from datetime import datetime
from enum import Enum

from homeassistant.util import dt as dt_util

from .period import Period

# import logging
# _LOGGER: logging.Logger = logging.getLogger(__package__)


class MeterState(Enum):
    MEASURING = "measuring"
    WAITING_FOR_TEMPLATE = "waiting for template"
    WAITING_FOR_PERIOD = "waiting for period start"


class Meter:
    def __init__(self, name: str, period: Period):
        self.name = name
        self._period = period
        self.state: MeterState | None = None

        self.measured_value = 0
        self.prev_measured_value = 0
        self._session_start_input_value: float | None = None
        self._start_measured_value: float | None = None

        self._template_active: bool = False

    @property
    def last_reset(self):
        return self._period.last_reset

    @property
    def next_reset(self):
        return self._period.end

    def disable_template(self):
        self._template_active = True  # bit hacky but more explicit than setting _template_active from coordinator

    def on_heartbeat(self, tznow: datetime, input_value: float):
        if self.state == MeterState.MEASURING:
            self._update(input_value)
        self._period.update(tznow, self._reset, input_value)
        self._update_state(input_value)

    def on_template_change(self, tznow: datetime, input_value: float, result: bool):
        if self.state == MeterState.MEASURING:
            self._update(input_value)
        self._period.update(tznow, self._reset, input_value)
        self._template_active = result
        self._update_state(input_value)

    def _update_state(self, input_value: float) -> MeterState:
        if self._period.active is True and self._template_active is True:
            new_state = MeterState.MEASURING
        elif self._period.active is True:
            new_state = MeterState.WAITING_FOR_TEMPLATE
        elif self._template_active is True:
            new_state = MeterState.WAITING_FOR_PERIOD
        else:
            raise ValueError("Invalid state determined.")

        if new_state == self.state:
            return
        if new_state == MeterState.MEASURING:
            self._start(input_value)
        self.state = new_state

    def _start(self, input_value):
        self._session_start_input_value = input_value
        self._start_measured_value = self.measured_value

    def _update(self, input_value: float):
        session_value = input_value - self._session_start_input_value
        self.measured_value = self._start_measured_value + session_value

    def _reset(self, input_value):
        self.prev_measured_value, self.measured_value = self.measured_value, 0
        self._session_start_input_value = input_value
        self._start_measured_value = self.measured_value

    @classmethod
    def to_dict(cls, meter: Meter) -> dict[str, str]:
        data = {
            "measured_value": meter.measured_value,
            "start_measured_value": meter._start_measured_value,
            "prev_measured_value": meter.prev_measured_value,
            "session_start_input_value": meter._session_start_input_value,
            "last_reset": dt_util.as_timestamp(meter._period.last_reset),
            "state": meter.state,
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, str], meter: Meter) -> Meter:
        meter.measured_value = data["measured_value"]
        meter._start_measured_value = data["start_measured_value"]
        meter.prev_measured_value = data["prev_measured_value"]
        meter._session_start_input_value = data["session_start_input_value"]
        last_reset = data.get("last_reset")
        if last_reset:
            meter._period.last_reset = dt_util.utc_from_timestamp(last_reset)
        meter.state = MeterState(data["state"])

        return meter
