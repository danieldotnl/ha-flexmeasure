from datetime import datetime
from datetime import timedelta
from datetime import timezone

import homeassistant.util.dt as dt_util
import pytest
import pytz
from custom_components.flexmeasure.timebox import Timebox

RESET_PATTERN = "0 0 * * *"
NAME = "24h"


@pytest.fixture
def timebox():
    fake_now = datetime(2022, 1, 1, 10, 30)
    tz = pytz.timezone("Europe/Amsterdam")
    return Timebox(NAME, reset_pattern=RESET_PATTERN, tznow=tz.localize(fake_now))


def test_init(timebox):

    assert timebox._reset_pattern == RESET_PATTERN
    print(f"reset: {timebox.next_reset}")

    reset_now = datetime(2022, 1, 2, 0, 0)
    tz = pytz.timezone("Europe/Amsterdam")
    assert timebox.next_reset == tz.localize(reset_now)


def test_start(timebox):
    fake_now = datetime(2022, 1, 1, 11, 5).timestamp()
    timebox.start(fake_now)
    assert timebox._session_start_value == fake_now
    assert timebox._box_state_start_value == 0


def test_stop(timebox):
    fake_now = datetime(2022, 1, 1, 11, 5)
    timebox.start(fake_now.timestamp())

    fake_now += timedelta(minutes=5)  # 11:10
    timebox.stop(fake_now.timestamp())

    assert timebox._box_state == 300

    fake_now += timedelta(minutes=2)  # 11:12
    timebox.start(fake_now.timestamp())

    fake_now += timedelta(minutes=3)  # 11:15
    timebox.stop(fake_now.timestamp())

    assert timebox._box_state == 480


def test_update(timebox):
    fake_now = datetime(2022, 1, 1, 10, 35, tzinfo=timezone.utc)
    timebox.start(fake_now.timestamp())
    fake_now += timedelta(minutes=5)  # 10:40
    timebox.update(fake_now.timestamp(), fake_now)

    assert timebox._box_state == 300

    fake_now += timedelta(minutes=5)  # 10:45
    timebox.update(fake_now.timestamp(), fake_now)

    assert timebox._box_state == 600

    fake_now += timedelta(minutes=10)  # 10:55
    timebox.update(fake_now.timestamp(), fake_now)

    assert timebox._box_state == 1200


def test_daylight_savings(timebox):
    fake_now = datetime(2022, 3, 27, 1, 50, tzinfo=timezone.utc)  # start summer time
    timebox.start(fake_now.timestamp())

    fake_now += timedelta(minutes=20)  # 2:10
    timebox.stop(fake_now.timestamp())

    assert timebox._box_state == 1200

    fake_reset = datetime(2022, 10, 30, 2, 50, tzinfo=pytz.timezone("Europe/Amsterdam"))
    fake_now = datetime(2022, 10, 30, 2, 50, tzinfo=timezone.utc)  # start winter time
    timebox = Timebox(NAME, reset_pattern=RESET_PATTERN, tznow=fake_reset)
    timebox.start(fake_now.timestamp())

    fake_now = datetime(2022, 10, 30, 3, 10, tzinfo=timezone.utc)  # 2:10
    timebox.stop(fake_now.timestamp())

    assert timebox._box_state == 1200


def test_hass_dt(timebox):
    fake_now = dt_util.utcnow()
    timebox.start(fake_now.timestamp())

    fake_now += timedelta(days=2)
    timebox.stop(fake_now.timestamp())

    assert timebox._box_state == 172800


def test_update_with_reset(timebox: Timebox):
    reset_now = datetime(2022, 1, 1, 0, 0)
    tz = pytz.timezone("Europe/Amsterdam")
    reset_now = tz.localize(reset_now)
    assert timebox.next_reset == reset_now + timedelta(days=1)

    fake_now = datetime(2022, 1, 1, 10, 35, tzinfo=timezone.utc)
    timebox.start(fake_now.timestamp())

    fake_now = datetime(2022, 1, 2, 10, 35, tzinfo=timezone.utc)
    timebox.update(fake_now.timestamp(), fake_now)

    assert timebox._box_state == 0
    assert timebox._prev_box_state == 86400

    fake_now = datetime(2022, 1, 2, 10, 36, tzinfo=timezone.utc)
    timebox.update(fake_now.timestamp(), fake_now)

    assert timebox._box_state == 60
    assert timebox._prev_box_state == 86400
