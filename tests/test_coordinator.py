from unittest.mock import Mock

from custom_components.flexmeasure.const import COORDINATOR
from custom_components.flexmeasure.const import DOMAIN
from custom_components.flexmeasure.const import DOMAIN_DATA
from custom_components.flexmeasure.coordinator import FlexMeasureCoordinator
from custom_components.flexmeasure.meter import MeterState
from custom_components.flexmeasure.time_window import TimeWindow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_TIME_CONFIG_FINAL


async def test_coordinator_happy_flow(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, options=MOCK_TIME_CONFIG_FINAL, entry_id="1234"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator: FlexMeasureCoordinator = hass.data[DOMAIN_DATA][entry.entry_id][
        COORDINATOR
    ]

    assert len(coordinator._meters.keys()) == 2
    assert coordinator._meters["day"].measured_value == 0
    assert coordinator._meters["day"].state == MeterState.MEASURING


# coordinator should use lastest reading in case the value is rubbish
async def test_value_error(hass: HomeAssistant):

    meter = Mock()
    meter.disable_template.return_value = None
    meter.on_heartbeat.return_value = None
    meter.disable_template()
    meter.disable_template.assert_any_call()

    value_func = Mock()
    value_func.side_effect = [234, "rubbish"]
    time_window = TimeWindow(["0"], "00:00:00", "00:00:00")

    store = Mock
    coordinator = FlexMeasureCoordinator(
        hass, "test_config", store, {"name": meter}, None, time_window, value_func
    )
    assert coordinator._name == "test_config"

    await coordinator._async_update_meters()
    assert meter.on_heartbeat.called

    meter.reset_mock()
    await coordinator._async_update_meters()
    assert meter.on_heartbeat.called
