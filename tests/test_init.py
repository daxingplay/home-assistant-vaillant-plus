"""Test vaillant-plus switch."""
from unittest.mock import call, patch

from homeassistant.const import ATTR_ENTITY_ID
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vaillant_plus import (
    async_setup,
    async_setup_entry,
    async_unload_entry,
    VaillantDeviceApiClient,
)
from custom_components.vaillant_plus.const import DOMAIN, DISPATCHERS, WEBSOCKET_CLIENT

from .const import MOCK_CONFIG_ENTRY_DATA, MOCK_DID


async def test_init_setup_and_unload_entry(hass, bypass_get_device_info):
    """Test switch services."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID
    )

    # Functions/objects can be patched directly in test code as well and can be used to test
    # additional things, like whether a function was called or what arguments it was called with
    with patch(
        "custom_components.vaillant_plus.VaillantDeviceApiClient.connect"
    ) as connect_func:
        assert await async_setup(hass, {})
        assert await async_setup_entry(hass, config_entry)
        await hass.async_block_till_done()
        assert connect_func.called
        assert DOMAIN in hass.data
        assert MOCK_DID in hass.data[DOMAIN][DISPATCHERS]
        assert config_entry.entry_id in hass.data[DOMAIN][WEBSOCKET_CLIENT]
        assert isinstance(
            hass.data[DOMAIN][WEBSOCKET_CLIENT][config_entry.entry_id],
            VaillantDeviceApiClient,
        )
        assert len(hass.data[DOMAIN][DISPATCHERS][MOCK_DID]) >= 2

        with patch(
            "custom_components.vaillant_plus.VaillantDeviceApiClient.close"
        ) as close_func:
            assert await async_unload_entry(hass, config_entry)
            await hass.async_block_till_done()
            assert close_func.called
            assert config_entry.entry_id not in hass.data[DOMAIN][WEBSOCKET_CLIENT]
