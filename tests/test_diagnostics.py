"""Tests for config entry diagnostics."""
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vaillant_plus.const import API_CLIENT, DISPATCHERS, DOMAIN
from custom_components.vaillant_plus.diagnostics import (
    REDACTED,
    async_get_config_entry_diagnostics,
)

from .const import MOCK_CONFIG_ENTRY_DATA, MOCK_DID


async def test_diagnostics_redacts_credentials(hass, device_api_client):
    """Diagnostics expose device attributes but never the account token."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID
    )
    entry.add_to_hass(hass)

    device_api_client._device_attrs = {"Heating_Enable": 1, "Room_Temperature": 21}
    hass.data.setdefault(DOMAIN, {API_CLIENT: {}, DISPATCHERS: {}})
    hass.data[DOMAIN][API_CLIENT][entry.entry_id] = device_api_client

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["entry"]["data"]["token"] == REDACTED
    assert result["client"]["device_attrs"] == {
        "Heating_Enable": 1,
        "Room_Temperature": 21,
    }
    assert result["client"]["device"]["model"] == "model_name"
    assert "mac" not in str(result["client"]["device"])


async def test_diagnostics_without_a_running_client(hass):
    """Diagnostics must still work when the entry failed to set up."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {API_CLIENT: {}, DISPATCHERS: {}})

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["client"] is None
    assert result["entry"]["data"]["token"] == REDACTED
