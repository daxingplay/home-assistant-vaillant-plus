"""Test vaillant-plus switch."""
from unittest.mock import patch

from homeassistant.components.climate.const import HVACAction
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_TEMPERATURE,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from vaillant_plus_cn_api import EVT_DEVICE_ATTR_UPDATE

from custom_components.vaillant_plus import (
    VaillantClient,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.vaillant_plus.const import DISPATCHERS, DOMAIN, API_CLIENT

from .const import (
    MOCK_CONFIG_ENTRY_DATA,
    MOCK_DEVICE_ATTRS_WHEN_CONNECT,
    MOCK_DEVICE_ATTRS_WHEN_UPDATE,
    MOCK_DID,
)


async def test_init_setup_and_unload_entry(hass: HomeAssistant, bypass_login, bypass_get_device):
    """Test switch services."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID
    )
    config_entry.add_to_hass(hass)

    # Functions/objects can be patched directly in test code as well and can be used to test
    # additional things, like whether a function was called or what arguments it was called with
    with patch(
        "vaillant_plus_cn_api.VaillantWebsocketClient.connect"
    ) as connect_func:
        assert await async_setup(hass, {})
        assert await async_setup_entry(hass, config_entry)

        assert DOMAIN in hass.data
        assert MOCK_DID in hass.data[DOMAIN][DISPATCHERS]
        assert config_entry.entry_id in hass.data[DOMAIN][API_CLIENT]
        assert isinstance(
            hass.data[DOMAIN][API_CLIENT][config_entry.entry_id],
            VaillantClient,
        )

        # async_dispatcher_send(
        #     hass,
        #     EVT_DEVICE_UPDATED.format(MOCK_DID),
        #     MOCK_DEVICE_ATTRS_WHEN_CONNECT,
        # )

        await hass.async_block_till_done()

        assert connect_func.called
        assert len(hass.data[DOMAIN][DISPATCHERS][MOCK_DID]) >= 2

        client = hass.data[DOMAIN][API_CLIENT][config_entry.entry_id]._websocket_client
        client._on_subscribe_handler(MOCK_DEVICE_ATTRS_WHEN_CONNECT)

        await hass.async_block_till_done()

        # Test whether the states of those entities are correct
        state_binary_sensor_heating = hass.states.get("binary_sensor.heating")
        assert (
            state_binary_sensor_heating.attributes.get(ATTR_FRIENDLY_NAME) == "Heating"
        )
        assert state_binary_sensor_heating.state == STATE_OFF

        state_water_heater = hass.states.get(
            "water_heater.vaillant_plus_1_water_heater"
        )
        assert state_water_heater.state == STATE_ON
        assert state_water_heater.attributes.get(ATTR_TEMPERATURE) == 45
        assert state_water_heater.attributes.get("min_temp") == 35.0
        assert state_water_heater.attributes.get("max_temp") == 65.0
        assert state_water_heater.attributes.get("target_temp_low") == 35.0
        assert state_water_heater.attributes.get("target_temp_high") == 65.0

        state_climate = hass.states.get("climate.vaillant_plus_1_climate")
        assert state_climate.state == STATE_OFF
        assert state_climate.attributes.get("hvac_action") == STATE_OFF
        assert state_climate.attributes.get("current_temperature") == 18.5

        # Test whether entities handle correctly when connect event triggered again
        client._on_subscribe_handler(MOCK_DEVICE_ATTRS_WHEN_CONNECT)

        # Test update event
        client._on_update_handler(
            EVT_DEVICE_ATTR_UPDATE, {"data": MOCK_DEVICE_ATTRS_WHEN_UPDATE}
        )
        state_water_heater = hass.states.get(
            "water_heater.vaillant_plus_1_water_heater"
        )
        assert state_water_heater.attributes.get(ATTR_TEMPERATURE) == 60
        assert state_water_heater.attributes.get("min_temp") == 35.0
        assert state_water_heater.attributes.get("max_temp") == 65.0
        assert state_water_heater.attributes.get("target_temp_low") == 35.0
        assert state_water_heater.attributes.get("target_temp_high") == 65.0

        state_climate = hass.states.get("climate.vaillant_plus_1_climate")
        assert state_climate.state == "heat"
        assert state_climate.attributes.get("hvac_action") == HVACAction.HEATING
        assert state_climate.attributes.get("current_temperature") == 20.5

        with patch(
            "custom_components.vaillant_plus.VaillantClient.close"
        ) as close_func:
            assert await async_unload_entry(hass, config_entry)
            await hass.async_block_till_done()
            assert close_func.called
            assert config_entry.entry_id not in hass.data[DOMAIN][API_CLIENT]
