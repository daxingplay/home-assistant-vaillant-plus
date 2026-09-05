"""Test vaillant-plus climate."""
from unittest.mock import patch

import pytest

from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    PRESET_COMFORT,
    PRESET_ECO,
    HVACAction,
    HVACMode,
)

from custom_components.vaillant_plus.climate import (
    VaillantGatewayClimate,
    VaillantVSmartClimate,
)


async def test_climate_actions(hass, device_api_client):
    """Test binary sensor."""
    climate = VaillantVSmartClimate(
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
    climate = VaillantVSmartClimate(device_api_client)

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
    climate = VaillantVSmartClimate(device_api_client)

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


async def test_climate_failed_command_raises_and_does_not_change_state(
    hass, device_api_client
):
    """A command that never reached the cloud must not look successful.

    `control_device` returns False once it has exhausted its retries, and
    nothing re-sends the command, so the device keeps its old state.
    """
    from homeassistant.exceptions import HomeAssistantError

    device_api_client._device_attrs = {
        "Heating_Enable": 1,
        "Room_Temperature_Setpoint_Comfort": 22,
    }
    climate = VaillantVSmartClimate(device_api_client)

    with patch(
        "custom_components.vaillant_plus.VaillantClient.control_device",
        return_value=False,
    ):
        with pytest.raises(HomeAssistantError):
            await climate.async_set_temperature(temperature=24)

        with pytest.raises(HomeAssistantError):
            await climate.async_turn_off()

    assert climate.target_temperature == 22
    assert climate.hvac_mode == HVACMode.HEAT


async def test_water_heater_failed_command_raises(hass, device_api_client):
    """The same for the water heater."""
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.vaillant_plus.const import WATER_HEATER_OFF
    from custom_components.vaillant_plus.water_heater import VaillantWaterHeater

    device_api_client._device_attrs = {
        "DHW_setpoint": 45,
        "WarmStar_Tank_Loading_Enable": 0,
    }
    water_heater = VaillantWaterHeater(device_api_client)

    with patch(
        "custom_components.vaillant_plus.VaillantClient.control_device",
        return_value=False,
    ):
        with pytest.raises(HomeAssistantError):
            await water_heater.async_turn_on()

    assert water_heater.current_operation == WATER_HEATER_OFF
    assert water_heater.target_temperature == 45


# Key set captured from a real gateway (productId 81, verboseName
# "WiFiGateway"). Note what is absent: no `Flow_temperature`, and none of the
# `Lower/Upper_Limitation_of_CH_Setpoint` pair the vSMART sends. It names its
# room reading `indoor_temperature`.
GATEWAY_ATTRS = {
    "Heating_Enable": 1,
    "Flow_Temperature_Setpoint": 45,
    "indoor_temperature": 21,
    "Mode_Setting_CH": "Cruising",
    "ebus_status": 1,
}

# The same gateway before a boiler is bound to it (`ebus_status: 0`): every
# reading is the raw eBUS "no data" sentinel rather than an absent key.
GATEWAY_UNPAIRED_ATTRS = {
    "Heating_Enable": 0,
    "Flow_Temperature_Setpoint": 127.5,
    "DHW_setpoint": 127.5,
    "indoor_temperature": 255,
    "Mode_Setting_CH": "Cruising",
    "ebus_status": 0,
}


async def test_gateway_controls_the_flow_temperature(hass, device_api_client):
    """A gateway targets the central heating flow setpoint."""
    device_api_client._device_attrs = dict(GATEWAY_ATTRS)
    climate = VaillantGatewayClimate(device_api_client)

    assert climate.current_temperature == 21
    assert climate.target_temperature == 45
    # A gateway reports no CH setpoint limits, so this range is all it gets.
    assert climate.min_temp == 30.0
    assert climate.max_temp == 75.0
    assert climate.hvac_action == HVACAction.HEATING

    with patch(
        "custom_components.vaillant_plus.VaillantClient.control_device"
    ) as send_command_func:
        await climate.async_set_temperature(temperature=50)
        send_command_func.assert_awaited_with({"Flow_Temperature_Setpoint": 50})


async def test_gateway_advertises_no_comfort_preset(hass, device_api_client):
    """PRESET_MODE must not be advertised without a room setpoint.

    Home Assistant rejects an entity that offers the feature and then returns
    None for the mode.
    """
    device_api_client._device_attrs = dict(GATEWAY_ATTRS)
    gateway = VaillantGatewayClimate(device_api_client)
    vsmart = VaillantVSmartClimate(device_api_client)

    assert not gateway.supported_features & ClimateEntityFeature.PRESET_MODE
    assert vsmart.supported_features & ClimateEntityFeature.PRESET_MODE
    assert vsmart.preset_mode == PRESET_COMFORT


async def test_gateway_ignores_no_data_sentinels(hass, device_api_client):
    """A gateway with no boiler must report nothing, not 127.5 / 255."""
    device_api_client._device_attrs = dict(GATEWAY_UNPAIRED_ATTRS)
    climate = VaillantGatewayClimate(device_api_client)

    assert climate.current_temperature is None
    assert climate.target_temperature is None
    # Neither temperature is known, so no claim about heating can be made.
    assert climate.hvac_action == HVACAction.OFF


async def test_gateway_sends_cruising_like_a_vsmart(hass, device_api_client):
    """Both families report Mode_Setting_CH, so both are sent it."""
    device_api_client._device_attrs = dict(GATEWAY_ATTRS)
    climate = VaillantGatewayClimate(device_api_client)

    with patch(
        "custom_components.vaillant_plus.VaillantClient.control_device"
    ) as send_command_func:
        await climate.async_turn_on()
        send_command_func.assert_awaited_with({
            "Heating_Enable": True,
            "Mode_Setting_CH": "Cruising",
        })


async def test_setup_creates_the_entity_for_the_resolved_family(
    hass, device_api_client
):
    """The class is chosen from the device list, not from the attributes.

    The gateway payload here carries no `Flow_Temperature_Setpoint`, so an
    attribute-sniffing implementation would classify it as a vSMART. Only the
    device list says what it is.
    """
    from homeassistant.helpers.dispatcher import async_dispatcher_send
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.vaillant_plus.climate import async_setup_entry
    from custom_components.vaillant_plus.const import (
        API_CLIENT,
        DISPATCHERS,
        DOMAIN,
        EVT_DEVICE_CONNECTED,
    )

    entry = MockConfigEntry(domain=DOMAIN, data={"did": "1"}, entry_id="1")
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {API_CLIENT: {}, DISPATCHERS: {}})
    hass.data[DOMAIN][API_CLIENT][entry.entry_id] = device_api_client
    hass.data[DOMAIN][DISPATCHERS]["1"] = []

    device_api_client._device.platform = 1
    device_api_client._device.product_verbose_name = "WiFiGateway"

    added = []
    await async_setup_entry(hass, entry, added.extend)

    device_api_client._device_attrs = {"Heating_Enable": 1}
    async_dispatcher_send(hass, EVT_DEVICE_CONNECTED.format("1"), {"Heating_Enable": 1})
    await hass.async_block_till_done()

    assert len(added) == 1
    assert isinstance(added[0], VaillantGatewayClimate)
