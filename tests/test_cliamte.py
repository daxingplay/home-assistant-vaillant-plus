"""Test vaillant-plus climate."""
from unittest.mock import call, patch

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.climate.const import (
    PRESET_COMFORT,
    PRESET_ECO,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.vaillant_plus.client import (
    VaillantDeviceApiClient,
    VaillantApiHub,
)
from custom_components.vaillant_plus.climate import (
    VaillantClimate,
)
from custom_components.vaillant_plus.const import DOMAIN
from vaillant_plus_cn_api import Token, Device

from .const import MOCK_CONFIG_ENTRY_DATA, MOCK_DID


async def test_climate_actions(hass, device_api_client):
    """Test binary sensor."""
    climate = VaillantClimate(
        device_api_client,
    )

    assert climate.unique_id == "1"
    assert climate.should_poll is False
    assert climate.name == "pn"

    with patch(
        "custom_components.vaillant_plus.VaillantDeviceApiClient.send_command"
    ) as send_command_func:
        await climate.async_set_temperature()
        send_command_func.assert_not_called()
        send_command_func.assert_not_awaited()

        await climate.async_set_preset_mode(PRESET_COMFORT)
        send_command_func.assert_not_called()
        send_command_func.assert_not_awaited()

        assert climate.preset_mode == PRESET_COMFORT

        await climate.async_set_preset_mode(PRESET_ECO)
        send_command_func.assert_not_called()
        send_command_func.assert_not_awaited()

        assert climate.preset_mode == PRESET_COMFORT

        await climate.async_set_temperature(temperature=30)
        send_command_func.assert_awaited_with(
            "Room_Temperature_Setpoint_Comfort",
            30,
        )

        await climate.async_set_hvac_mode(HVACMode.OFF)
        send_command_func.assert_awaited_with(
            "Heating_Enable",
            False,
        )

        await climate.async_set_hvac_mode(HVACMode.HEAT)
        send_command_func.assert_awaited_with(
            "Heating_Enable",
            True,
        )
