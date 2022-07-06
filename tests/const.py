"""Constants for flexmeasure tests."""
from custom_components.flexmeasure.const import CONF_CRON
from custom_components.flexmeasure.const import CONF_METER_TYPE
from custom_components.flexmeasure.const import CONF_PERIODS
from custom_components.flexmeasure.const import CONF_SENSORS
from custom_components.flexmeasure.const import CONF_SOURCE
from custom_components.flexmeasure.const import CONF_TARGET
from custom_components.flexmeasure.const import CONF_TEMPLATE
from custom_components.flexmeasure.const import METER_TYPE_SOURCE
from custom_components.flexmeasure.const import METER_TYPE_TIME
from custom_components.flexmeasure.const import PREDEFINED_PERIODS
from homeassistant.const import CONF_NAME
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
from homeassistant.const import CONF_VALUE_TEMPLATE

# Mock config data to be used across multiple tests
MOCK_TIME_CONFIG_FORM = {
    CONF_TEMPLATE: "test_template",
    CONF_TARGET: "test_target",
}

MOCK_TIME_CONFIG_FINAL = {
    CONF_NAME: "test_configname",
    CONF_TEMPLATE: None,
    CONF_METER_TYPE: METER_TYPE_TIME,
    CONF_SENSORS: [
        {
            CONF_NAME: "day",
            CONF_CRON: PREDEFINED_PERIODS["day"],
            CONF_UNIT_OF_MEASUREMENT: None,
            CONF_VALUE_TEMPLATE: None,
        },
        {
            CONF_NAME: "year",
            CONF_CRON: PREDEFINED_PERIODS["year"],
            CONF_UNIT_OF_MEASUREMENT: None,
            CONF_VALUE_TEMPLATE: None,
        },
    ],
}

MOCK_SOURCE_CONFIG = {
    CONF_SOURCE: "sun.sun",
    CONF_TEMPLATE: "test_template",
    CONF_TARGET: "test_target",
    CONF_METER_TYPE: METER_TYPE_SOURCE,
}

MOCK_TIMEBOX_CONFIG = {CONF_PERIODS: ["day", "5m"]}

MOCK_TIME_CONFIG_NOTEMPLATE = {
    CONF_TEMPLATE: None,
    CONF_NAME: "test_notemplate",
    CONF_METER_TYPE: METER_TYPE_TIME,
    CONF_SENSORS: [
        {CONF_NAME: "day", CONF_CRON: PREDEFINED_PERIODS["day"]},
        {CONF_NAME: "5m", CONF_CRON: PREDEFINED_PERIODS["5m"]},
    ],
}

# MOCK_TIME_CONFIG_NOTEMPLATE = {
#     "sensors": [{"name": "tz", "cron": "50 15 * * *"}],
#     "meter_type": "time",
#     "name": "now",
#     "trigger_template": None,
# }

# MOCK_TIME_CONFIG_NOTEMPLATE = {
#     "sensors": [
#         {
#             "name": "tz",
#             "cron": "50 15 * * *",
#             "duration": {"hours": 0, "minutes": 2, "seconds": 0},
#             "unit_of_measurement": "sec",
#         }
#     ],
#     "meter_type": "time",
#     "name": "now",
#     "trigger_template": None,
# }
