from custom_components.flexmeasure.const import DOMAIN
from custom_components.flexmeasure.const import DOMAIN_DATA
from custom_components.flexmeasure.const import STATUS_INACTIVE
from custom_components.flexmeasure.const import STATUS_MEASURING
from custom_components.flexmeasure.coordinator import FlexMeasureCoordinator
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
    coordinator: FlexMeasureCoordinator = hass.data[DOMAIN_DATA][entry.entry_id]

    assert len(coordinator._timeboxes.keys()) == 2
    assert coordinator._timeboxes["day"].state == 0
    await coordinator.start_measuring()
    assert coordinator.status == STATUS_MEASURING
    await coordinator.stop_measuring()
    assert coordinator.status == STATUS_INACTIVE
    assert coordinator._timeboxes["day"].state > 0
