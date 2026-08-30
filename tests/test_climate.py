"""Test vaillant-plus climate."""
from unittest.mock import patch

from homeassistant.components.climate.const import (
    PRESET_COMFORT,
    PRESET_ECO,
    HVACAction,
    HVACMode,
)

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


async def test_climate_turn_on_off(hass, device_api_client):
    """climate.turn_on / turn_off map onto the heating enable attribute."""
    device_api_client._device_attrs = {
        "Heating_Enable": 1,
        "Room_Temperature": 20.5,
        "Room_Temperature_Setpoint_Comfort": 22,
    }
    climate = VaillantClimate(device_api_client)

    with patch(
        "custom_components.vaillant_plus.VaillantClient.control_device"
    ) as send_command_func:
        await climate.async_turn_off()
        send_command_func.assert_awaited_with({"Heating_Enable": False})
        # Optimistically applied, so the UI does not snap back while the
        # cloud takes its time to echo the change.
        assert climate.hvac_mode == HVACMode.OFF
        assert climate.hvac_action == HVACAction.OFF

        await climate.async_turn_on()
        send_command_func.assert_awaited_with(
            {"Heating_Enable": True, "Mode_Setting_CH": "Cruising"}
        )
        assert climate.hvac_mode == HVACMode.HEAT


async def test_climate_target_temperature_is_applied_optimistically(
    hass, device_api_client
):
    """A new setpoint shows immediately instead of after the websocket echo."""
    device_api_client._device_attrs = {
        "Heating_Enable": 1,
        "Room_Temperature_Setpoint_Comfort": 22,
    }
    climate = VaillantClimate(device_api_client)

    with patch("custom_components.vaillant_plus.VaillantClient.control_device"):
        await climate.async_set_temperature(temperature=24)

    assert climate.target_temperature == 24


async def test_water_heater_operation_is_applied_optimistically(
    hass, device_api_client
):
    """Switching DHW on shows immediately in the entity state."""
    from custom_components.vaillant_plus.const import WATER_HEATER_ON
    from custom_components.vaillant_plus.water_heater import VaillantWaterHeater

    device_api_client._device_attrs = {
        "DHW_setpoint": 45,
        "WarmStar_Tank_Loading_Enable": 0,
    }
    water_heater = VaillantWaterHeater(device_api_client)

    with patch("custom_components.vaillant_plus.VaillantClient.control_device"):
        await water_heater.async_turn_on()

    assert water_heater.current_operation == WATER_HEATER_ON
