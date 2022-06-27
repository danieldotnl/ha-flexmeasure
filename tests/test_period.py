from datetime import datetime
from datetime import timedelta

import pytest
import pytz
from custom_components.flexmeasure.const import PATTERN
from custom_components.flexmeasure.const import PREDEFINED_PERIODS
from custom_components.flexmeasure.period import Period

TZ = pytz.timezone("Europe/Amsterdam")


def test_init():
    fake_now = datetime(2022, 1, 1, 10, 30)
    tznow = TZ.localize(fake_now)

    # full day period
    start_pattern = PREDEFINED_PERIODS["day"][PATTERN]
    period = Period(start_pattern, tznow)
    assert period.start == TZ.localize(datetime(2022, 1, 1, 0, 0))
    assert period.end == period.start + timedelta(days=1)
    assert period.active is True

    # period with 8 hour duration
    period = Period(start_pattern, tznow, timedelta(hours=8))
    assert period.start == TZ.localize(datetime(2022, 1, 1, 0, 0))
    assert period.end == period.start + timedelta(hours=8)
    assert period.active is False

    # exception should be raised when duration is longer than interval
    with pytest.raises(ValueError):
        period = Period(start_pattern, tznow, timedelta(days=7))


def test_update_period_without_duration():
    fake_now = datetime(2022, 1, 1, 10, 30)
    tznow1 = TZ.localize(fake_now)

    start_pattern = PREDEFINED_PERIODS["day"][PATTERN]
    period = Period(start_pattern, tznow1)
    assert period.active is True

    reset_called = False

    def fake_reset(input_value):
        nonlocal reset_called
        reset_called = True
        assert input_value == 123

    # period shouldn't be resetted when updated during period
    fake_now = datetime(2022, 1, 1, 11, 30)
    tznow2 = TZ.localize(fake_now)
    period.update(tznow2, fake_reset, 123)
    assert reset_called is False
    assert period.active is True

    # reset period when updated after end time
    reset_called = False
    fake_now = datetime(2022, 1, 2, 13, 30)
    tznow3 = TZ.localize(fake_now)
    period.update(tznow3, fake_reset, 123)
    assert reset_called is True
    assert period.last_reset == tznow3
    assert period.active is True

    # don't reset again when updated after end time
    reset_called = False
    fake_now = datetime(2022, 1, 2, 13, 35)
    tznow4 = TZ.localize(fake_now)
    period.update(tznow4, fake_reset, 123)
    assert period.last_reset == tznow3
    assert reset_called is False
    assert period.active is True


def test_update_period_with_duration():
    fake_now = datetime(2022, 1, 1, 10, 30)
    tznow1 = TZ.localize(fake_now)

    start_pattern = PREDEFINED_PERIODS["day"][PATTERN]
    period = Period(start_pattern, tznow1, timedelta(hours=12))
    assert period.active is True

    reset_called = False

    def fake_reset(input_value):
        nonlocal reset_called
        reset_called = True
        assert input_value == 123

    # period shouldn't be resetted when updated during period
    fake_now = datetime(2022, 1, 1, 11, 30)
    tznow2 = TZ.localize(fake_now)
    period.update(tznow2, fake_reset, 123)
    assert reset_called is False
    assert period.active is True

    # reset period when updated after end time
    reset_called = False
    fake_now = datetime(2022, 1, 1, 13, 30)
    tznow3 = TZ.localize(fake_now)
    period.update(tznow3, fake_reset, 123)
    assert reset_called is True
    assert period.last_reset == tznow3
    assert period.active is False

    # don't reset again when updated after end time
    reset_called = False
    fake_now = datetime(2022, 1, 2, 3, 30)
    tznow4 = TZ.localize(fake_now)
    period.update(tznow4, fake_reset, 123)
    assert period.last_reset == tznow3
    assert reset_called is False
    assert period.active is True
