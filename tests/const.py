"""Constants for flexmeasure tests."""
from custom_components.flexmeasure.const import CONF_SOURCE
from custom_components.flexmeasure.const import CONF_TARGET
from custom_components.flexmeasure.const import CONF_TEMPLATE

# Mock config data to be used across multiple tests
MOCK_CONFIG = {
    CONF_SOURCE: "sun.sun",
    CONF_TEMPLATE: "test_template",
    CONF_TARGET: "test_target",
}
