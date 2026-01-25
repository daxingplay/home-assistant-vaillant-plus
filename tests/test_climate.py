"""Test vaillant-plus climate."""
from unittest.mock import patch

from homeassistant.components.climate.const import PRESET_COMFORT, PRESET_ECO, HVACMode

from custom_components.vaillant_plus.climate import VaillantClimate


async def test_climate_actions(hass, device_api_client):
    """Test binary sensor."""
    climate = VaillantClimate(
        device_api_client,
    )

    assert climate.unique_id == "1_climate"
    assert climate.should_poll is False
    assert climate.name is None

    with patch(
        "custom_components.vaillant_plus.VaillantClient.control_device"
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
        send_command_func.assert_awaited_with({
            "Room_Temperature_Setpoint_Comfort": 30,
        })

        await climate.async_set_hvac_mode(HVACMode.OFF)
        send_command_func.assert_awaited_with({
            "Heating_Enable": False
        })

        await climate.async_set_hvac_mode(HVACMode.HEAT)
        send_command_func.assert_awaited_with({
            "Heating_Enable": True,
            "Mode_Setting_CH": "Cruising",
        })
