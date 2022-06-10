"""Constants for FlexMeasure."""
# Base component constants
NAME = "FlexMeasure"
DOMAIN = "flexmeasure"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/custom-components/ha-flexmeasure/issues"

# Icons
ICON = "mdi:measure"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
PLATFORMS = [SENSOR]


# Services
SERVICE_START = "start"
SERVICE_STOP = "stop"

# Configuration and options
CONF_ENABLED = "enabled"
CONF_SENSOR_TYPE = "Sensor type"
CONF_SOURCE = "Source sensor"
CONF_TEMPLATE = "Activation template"
CONF_TARGET = "Target sensor name"
CONF_TIMEBOXES = "timeboxes"

SENSOR_TYPE_TIME = "time"
SENSOR_TYPE_SOURCE = "source"

# Time boxes
NAME = "name"
PATTERN = "pattern"

PREDEFINED_TIME_BOXES = {
    "5m": {NAME: "5m", PATTERN: "*/5 * * * *"},
    "hour": {NAME: "hour", PATTERN: "0 * * * *"},
    "day": {NAME: "day", PATTERN: "0 0 * * *"},
    "week": {NAME: "week", PATTERN: "0 0 * * 1"},
    "month": {NAME: "month", PATTERN: "0 0 1 * *"},
    "year": {NAME: "year", PATTERN: "0 0 1 1 *"},
    "custom": "custom",
}


# Defaults
DEFAULT_NAME = DOMAIN

# Attributes
ATTR_PREV = "prev_period"
ATTR_LAST_RESET = "last_reset"
ATTR_NEXT_RESET = "next_reset"

# Statuses
ATTR_STATUS = "status"
STATUS_MEASURING = "Measuring"
STATUS_INACTIVE = "Inactive"
STATUSES = [STATUS_MEASURING, STATUS_INACTIVE]


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
