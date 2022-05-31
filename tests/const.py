"""Constants for flexmeasure tests."""
from custom_components.flexmeasure.const import CONF_EXPRESSION
from custom_components.flexmeasure.const import CONF_SOURCE
from custom_components.flexmeasure.const import CONF_TARGET

# Mock config data to be used across multiple tests
MOCK_CONFIG = {
    CONF_SOURCE: "sun.sun",
    CONF_EXPRESSION: "test_expression",
    CONF_TARGET: "test_target",
}
