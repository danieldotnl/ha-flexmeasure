import json
from datetime import datetime

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


def test_init(meter: Meter):
    start = datetime(2022, 1, 1, 0, 0)
    assert meter._period.start == TZ.localize(start)


def test_heartbeat(meter: Meter):

    # should trigger start()
    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 5))
    meter._template_active = True
    meter.on_heartbeat(fake_now, 123, True)
    assert meter._session_start_reading == 123
    assert meter._start_measured_value == 0

    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 10))
    meter.on_heartbeat(fake_now, 130, True)
    assert meter.measured_value == 7

    fake_now = TZ.localize(datetime(2022, 1, 2, 11, 11))
    meter.on_heartbeat(fake_now, 132, True)
    assert meter.measured_value == 0
    assert meter.prev_measured_value == 9

    fake_now = TZ.localize(datetime(2022, 1, 2, 11, 20))
    meter.on_heartbeat(fake_now, 140, False)
    assert meter.measured_value == 8

    fake_now = TZ.localize(datetime(2022, 1, 2, 11, 20))
    meter.on_heartbeat(fake_now, 145, False)
    assert meter.measured_value == 8

    fake_now = TZ.localize(datetime(2022, 1, 2, 11, 20))
    meter.on_heartbeat(fake_now, 148, True)
    assert meter.measured_value == 8

    fake_now = TZ.localize(datetime(2022, 1, 2, 11, 21))
    meter.on_heartbeat(fake_now, 150, True)
    assert meter.measured_value == 10


def test_template_update(meter: Meter):
    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 5))
    meter.on_template_change(fake_now, 123, True, tw_active=True)
    assert meter.state == MeterState.MEASURING

    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 6))
    meter.on_template_change(fake_now, 125, False, tw_active=True)
    assert meter.state == MeterState.WAITING_FOR_CONDITION
    assert meter.measured_value == 2

    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 7))
    meter.on_template_change(fake_now, 127, True, tw_active=True)
    assert meter.state == MeterState.MEASURING
    assert meter.measured_value == 2

    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 8))
    meter.on_heartbeat(fake_now, 130, True)
    assert meter.state == MeterState.MEASURING
    assert meter.measured_value == 5


def test_serializing(meter: Meter):
    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 5))
    meter.on_template_change(fake_now, 123, True, tw_active=True)
    assert meter.state == MeterState.MEASURING

    fake_now = TZ.localize(datetime(2022, 1, 1, 11, 8))
    meter.on_heartbeat(fake_now, 130, True)
    assert meter.state == MeterState.MEASURING
    data = Meter.to_dict(meter)

    meter2 = Meter(meter.name, meter._period)
    meter2: Meter = Meter.from_dict(data, meter2)
    assert meter2.state == MeterState.MEASURING
    assert meter2.measured_value == 7

    meter2.on_template_change(fake_now, 150, False, tw_active=True)
    assert meter2.state == MeterState.WAITING_FOR_CONDITION
    assert meter2.measured_value == 27

    # serialize to json
    data = Meter.to_dict(meter2)
    json_data = json.dumps(data, indent=4)
    assert json_data

    json_data2 = json.loads(json_data)
    assert json_data2["measured_value"] == 27


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
