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
