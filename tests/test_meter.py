from datetime import datetime
from datetime import timedelta

import pytest
import pytz
from custom_components.flexmeasure.meter import Meter
from custom_components.flexmeasure.meter import MeterState
from custom_components.flexmeasure.period import Period

START_PATTERN = "0 0 * * *"
NAME = "24h"
TZ = pytz.timezone("Europe/Amsterdam")


@pytest.fixture
def meter():
    fake_now = datetime(2022, 1, 1, 10, 30)
    period = Period(START_PATTERN, tznow=TZ.localize(fake_now))
    return Meter(NAME, period)


@pytest.fixture
def duration_meter():
    fake_now = datetime(2022, 1, 1, 10, 30)
    period = Period(
        START_PATTERN, tznow=TZ.localize(fake_now), duration=timedelta(hours=12)
    )
    return Meter(NAME, period)


def test_init(meter: Meter):
    start = datetime(2022, 1, 1, 0, 0)
    assert meter._period.start == TZ.localize(start)


def test_heartbeat(meter: Meter):

    # should trigger start()
    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 5))
    meter._template_active = True
    meter.on_heartbeat(fake_now, 123)
    assert meter._session_start_input_value == 123
    assert meter._start_measured_value == 0

    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 10))
    meter.on_heartbeat(fake_now, 130)
    assert meter.measured_value == 7

    fake_now = TZ.localize(datetime(2022, 1, 2, 11, 10))
    meter.on_heartbeat(fake_now, 132)
    assert meter.measured_value == 0
    assert meter.prev_measured_value == 9


def test_template_update(meter: Meter):
    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 5))
    meter.on_template_change(fake_now, 123, True)
    assert meter.state == MeterState.MEASURING

    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 6))
    meter.on_template_change(fake_now, 125, False)
    assert meter.state == MeterState.WAITING_FOR_TEMPLATE
    assert meter.measured_value == 2

    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 7))
    meter.on_template_change(fake_now, 127, True)
    assert meter.state == MeterState.MEASURING
    assert meter.measured_value == 2

    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 8))
    meter.on_heartbeat(fake_now, 130)
    assert meter.state == MeterState.MEASURING
    assert meter.measured_value == 5


def test_serializing(meter: Meter):
    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 5))
    meter.on_template_change(fake_now, 123, True)
    assert meter.state == MeterState.MEASURING

    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 8))
    meter.on_heartbeat(fake_now, 130)
    assert meter.state == MeterState.MEASURING
    data = Meter.to_dict(meter)

    meter2 = Meter(meter.name, meter._period)
    meter2: Meter = Meter.from_dict(data, meter2)
    assert meter2.state == MeterState.MEASURING
    assert meter2.measured_value == 7

    meter2.on_template_change(fake_now, 150, False)
    assert meter2.state == MeterState.WAITING_FOR_TEMPLATE
    assert meter2.measured_value == 27


def test_meter_with_duration(duration_meter: Meter):
    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 8))
    duration_meter.on_template_change(fake_now, 1000, True)

    fake_now = TZ.localize(datetime(2022, 1, 2, 12, 8))
    duration_meter.on_heartbeat(fake_now, 2000)
    assert duration_meter.state == MeterState.WAITING_FOR_PERIOD
    assert duration_meter.measured_value == 0
    assert duration_meter.prev_measured_value == 1000

    fake_now = TZ.localize(datetime(2022, 1, 3, 2, 8))
    duration_meter.on_heartbeat(fake_now, 100)
    assert duration_meter.state == MeterState.MEASURING
    duration_meter.on_heartbeat(fake_now, 101)
    assert duration_meter.measured_value == 1


# def test_daylight_savings(meter):
#     fake_now = datetime(2022, 3, 27, 1, 50, tzinfo=timezone.utc)  # start summer time
#     meter.start(fake_now.timestamp())

#     fake_now += timedelta(minutes=20)  # 2:10
#     meter.stop(fake_now.timestamp())

#     assert meter._box_state == 1200

#     fake_reset = datetime(2022, 10, 30, 2, 50, tzinfo=pytz.timezone("Europe/Amsterdam"))
#     fake_now = datetime(2022, 10, 30, 2, 50, tzinfo=timezone.utc)  # start winter time
#     meter = Meter(NAME, reset_pattern=RESET_PATTERN, tznow=fake_reset)
#     meter.start(fake_now.timestamp())

#     fake_now = datetime(2022, 10, 30, 3, 10, tzinfo=timezone.utc)  # 2:10
#     meter.stop(fake_now.timestamp())

#     assert meter._box_state == 1200


# def test_hass_dt(meter):
#     fake_now = dt_util.utcnow()
#     meter.start(fake_now.timestamp())

#     fake_now += timedelta(days=2)
#     meter.stop(fake_now.timestamp())

#     assert meter._box_state == 172800


# def test_update_with_reset(meter: Meter):
#     reset_now = datetime(2022, 1, 1, 0, 0)
#     tz = pytz.timezone("Europe/Amsterdam")
#     reset_now = tz.localize(reset_now)
#     assert meter.next_reset == reset_now + timedelta(days=1)

#     fake_now = datetime(2022, 1, 1, 10, 35, tzinfo=timezone.utc)
#     meter.start(fake_now.timestamp())

#     fake_now = datetime(2022, 1, 2, 10, 35, tzinfo=timezone.utc)
#     meter.update(fake_now.timestamp(), fake_now)

#     assert meter._box_state == 0
#     assert meter._prev_box_state == 86400

#     fake_now = datetime(2022, 1, 2, 10, 36, tzinfo=timezone.utc)
#     meter.update(fake_now.timestamp(), fake_now)

#     assert meter._box_state == 60
#     assert meter._prev_box_state == 86400
