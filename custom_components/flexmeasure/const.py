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
SERVICE_START = "Start"
SERVICE_STOP = "Stop"

# Configuration and options
CONF_ENABLED = "enabled"
CONF_SOURCE = "Source sensor"
CONF_EXPRESSION = "Activator expression"
CONF_TARGET = "Target sensor name"

# Defaults
DEFAULT_NAME = DOMAIN

# Statuses
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
