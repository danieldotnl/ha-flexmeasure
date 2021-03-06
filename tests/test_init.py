"""Test flexmeasure setup process."""
# import pytest
from custom_components.flexmeasure import async_reload_entry
from custom_components.flexmeasure import async_unload_entry
from custom_components.flexmeasure.const import DOMAIN
from custom_components.flexmeasure.const import DOMAIN_DATA
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_TIME_CONFIG_FINAL


async def test_reload_entry(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, options=MOCK_TIME_CONFIG_FINAL, entry_id="1234"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert DOMAIN_DATA in hass.data and entry.entry_id in hass.data[DOMAIN_DATA]

    assert await async_reload_entry(hass, entry) is None
    assert DOMAIN_DATA in hass.data and entry.entry_id in hass.data[DOMAIN_DATA]


async def test_remove_entry(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, options=MOCK_TIME_CONFIG_FINAL, entry_id="1234"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert DOMAIN_DATA in hass.data and entry.entry_id in hass.data[DOMAIN_DATA]

    await async_unload_entry(hass, entry)
    assert hass.data[DOMAIN_DATA].get(entry.entry_id) is None
