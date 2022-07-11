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
CONF_METER_TYPE = "meter_type"
CONF_SOURCE = "source_entity"
CONF_CONDITION = "condition"
CONF_TARGET = "target_sensor"
CONF_METERS = "meters"
CONF_PERIODS = "periods"
CONF_DURATION = "duration"
CONF_CRON = "cron"
CONF_PERIOD = "period"
CONF_SENSORS = "sensors"
CONF_STATE_CLASS = "state_class"
CONF_TW_DAYS = "when_days"
CONF_TW_FROM = "when_from"
CONF_TW_TILL = "when_till"

METER_TYPE_TIME = "time"
METER_TYPE_SOURCE = "source"

# Time boxes
NAME = "name"
PATTERN = "pattern"

PREDEFINED_PERIODS = {
    "5m": "*/5 * * * *",
    "hour": "0 * * * *",
    "day": "0 0 * * *",
    "week": "0 0 * * 1",
    "month": "0 0 1 * *",
    "year": "0 0 1 1 *",
    "none": "59 59 23 31 12 ? 2099",
}


# Defaults
DEFAULT_NAME = DOMAIN

# Attributes
ATTR_PREV = "prev_period"
ATTR_NEXT_RESET = "next_reset"

# Statuses
ATTR_STATUS = "status"
STATUS_MEASURING = "measuring"
STATUS_INACTIVE = "inactive"
STATUS_WAIT_SCHEDULE = "wait for schedule"
STATUS_WAIT_TEMPLATE = "wait for template"
STATUS_ERROR = "error"
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
