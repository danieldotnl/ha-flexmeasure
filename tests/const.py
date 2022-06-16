"""Constants for flexmeasure tests."""
from custom_components.flexmeasure.const import CONF_SENSOR_TYPE
from custom_components.flexmeasure.const import CONF_SOURCE
from custom_components.flexmeasure.const import CONF_TARGET
from custom_components.flexmeasure.const import CONF_TEMPLATE
from custom_components.flexmeasure.const import CONF_TIMEBOXES
from custom_components.flexmeasure.const import SENSOR_TYPE_TIME

# Mock config data to be used across multiple tests
MOCK_TIME_CONFIG_FORM = {
    CONF_TEMPLATE: "test_template",
    CONF_TARGET: "test_target",
}

MOCK_TIME_CONFIG_FINAL = {
    CONF_TEMPLATE: "test_template",
    CONF_TARGET: "test_target",
    CONF_SENSOR_TYPE: SENSOR_TYPE_TIME,
    CONF_TIMEBOXES: ["day", "5m"],
}

MOCK_SOURCE_CONFIG = {
    CONF_SOURCE: "sun.sun",
    CONF_TEMPLATE: "test_template",
    CONF_TARGET: "test_target",
    CONF_SENSOR_TYPE: SENSOR_TYPE_TIME,
}

MOCK_TIMEBOX_CONFIG = {CONF_TIMEBOXES: ["day", "5m"]}

MOCK_TIME_CONFIG_NOTEMPLATE = {
    CONF_TEMPLATE: None,
    CONF_TARGET: "test_notemplate",
    CONF_SENSOR_TYPE: SENSOR_TYPE_TIME,
    CONF_TIMEBOXES: ["day", "5m"],
}
