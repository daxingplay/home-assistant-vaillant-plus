"""Test vaillant-plus climate."""
from unittest.mock import patch

from custom_components.vaillant_plus.const import WATER_HEATER_OFF, WATER_HEATER_ON
from custom_components.vaillant_plus.water_heater import VaillantWaterHeater


async def test_water_heater_actions(hass, device_api_client):
    """Test binary sensor."""
    water_heater = VaillantWaterHeater(
        device_api_client,
    )

    assert water_heater.unique_id == "1_water_heater"
    assert water_heater.should_poll is False
    assert water_heater.name is None

    with patch(
        "custom_components.vaillant_plus.VaillantClient.control_device"
    ) as send_command_func:
        await water_heater.async_set_temperature()
        send_command_func.assert_not_called()
        send_command_func.assert_not_awaited()

        await water_heater.async_set_operation_mode(WATER_HEATER_OFF)
        send_command_func.assert_awaited_with({
            "WarmStar_Tank_Loading_Enable": 0,
        })

        await water_heater.async_set_operation_mode(WATER_HEATER_ON)
        send_command_func.assert_awaited_with({
            "WarmStar_Tank_Loading_Enable": 1,
        })

        await water_heater.async_set_temperature(temperature=30)
        send_command_func.assert_awaited_with({
            "DHW_setpoint": 30,
        })

        # Device actions and scripts call turn_on/turn_off, see issue #34.
        await water_heater.async_turn_on()
        send_command_func.assert_awaited_with({
            "WarmStar_Tank_Loading_Enable": 1,
        })

        await water_heater.async_turn_off()
        send_command_func.assert_awaited_with({
            "WarmStar_Tank_Loading_Enable": 0,
        })


async def test_water_heater_supports_turn_on_off(hass, device_api_client):
    """The on/off feature must be advertised, or the services are rejected."""
    from homeassistant.components.water_heater import WaterHeaterEntityFeature

    water_heater = VaillantWaterHeater(device_api_client)

    assert water_heater.supported_features & WaterHeaterEntityFeature.ON_OFF
    assert water_heater.supported_features & WaterHeaterEntityFeature.OPERATION_MODE


async def test_water_heater_temperature_limits_have_fallbacks(hass, device_api_client):
    """Gateways that omit the DHW limits must not break the state write."""
    water_heater = VaillantWaterHeater(device_api_client)

    device_api_client._device_attrs = {}
    assert water_heater.min_temp == 35.0
    assert water_heater.max_temp == 65.0

    device_api_client._device_attrs = {
        "Lower_Limitation_of_DHW_Setpoint": 40,
        "Upper_Limitation_of_DHW_Setpoint": 60,
    }
    assert water_heater.min_temp == 40
    assert water_heater.max_temp == 60
