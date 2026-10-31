"""Changes made outside Home Assistant (the Vaillant app) must reach its states.

A change made in the app arrives as a partial websocket frame carrying only
the attributes that changed. Each entity has to pick it up from there,
including after Home Assistant itself has just changed the same value.
"""
from dataclasses import replace
from unittest.mock import patch

from homeassistant.const import ATTR_TEMPERATURE, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from vaillant_plus_cn_api import EVT_DEVICE_ATTR_UPDATE, Device

from custom_components.vaillant_plus import async_setup
from custom_components.vaillant_plus.const import API_CLIENT, DOMAIN

from .const import MOCK_CONFIG_ENTRY_DATA, MOCK_DID

GATEWAY = Device(
    id=MOCK_DID,
    mac="mac2",
    product_key="pk",
    product_id=81,
    product_name="智能网关",
    product_verbose_name="WiFiGateway",
    is_online=True,
    is_manager=True,
    group_id=2,
    sno="sno",
    create_time="2000-01-01 00:00:00",
    platform=1,
)

# A gateway with a boiler bound, as sent once when the subscription starts.
GATEWAY_ATTRS = {
    "Heating_Enable": 1,
    "Flow_Temperature_Setpoint": 45,
    "Flow_temperature": 40,
    "indoor_temperature": 21,
    "Mode_Setting_CH": "Cruising",
    "WarmStar_Tank_Loading_Enable": 1,
    "DHW_setpoint": 45,
    "ebus_status": 1,
}


async def _set_up_gateway(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID
    )
    entry.add_to_hass(hass)

    with patch("vaillant_plus_cn_api.VaillantWebsocketClient.connect"), patch(
        "vaillant_plus_cn_api.VaillantApiClient.get_device_list",
        return_value=[replace(GATEWAY)],
    ):
        assert await async_setup(hass, {})
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    client = hass.data[DOMAIN][API_CLIENT][entry.entry_id]
    websocket = client._websocket_client
    websocket._on_subscribe_handler(dict(GATEWAY_ATTRS))
    websocket._on_update_handler(EVT_DEVICE_ATTR_UPDATE, {"data": dict(GATEWAY_ATTRS)})
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    ids = {
        "climate": registry.async_get_entity_id("climate", DOMAIN, f"{MOCK_DID}_climate"),
        "water_heater": registry.async_get_entity_id(
            "water_heater", DOMAIN, f"{MOCK_DID}_water_heater"
        ),
        "setpoint": registry.async_get_entity_id(
            "sensor", DOMAIN, f"{MOCK_DID}_Flow_Temperature_Setpoint"
        ),
        "heating": registry.async_get_entity_id(
            "binary_sensor", DOMAIN, f"{MOCK_DID}_Heating_Enable"
        ),
    }
    assert all(ids.values()), ids

    async def push(frame):
        """Deliver a partial frame the way the cloud does after an app change."""
        websocket._on_update_handler(EVT_DEVICE_ATTR_UPDATE, {"data": frame})
        await hass.async_block_till_done()

    return ids, push


async def test_app_changes_reach_the_gateway_entities(hass: HomeAssistant):
    """Setpoint, heating and hot water changed in the app show up in HA."""
    ids, push = await _set_up_gateway(hass)

    climate = hass.states.get(ids["climate"])
    assert climate.state == "heat"
    assert climate.attributes[ATTR_TEMPERATURE] == 45

    await push({"Flow_Temperature_Setpoint": 55})
    assert hass.states.get(ids["climate"]).attributes[ATTR_TEMPERATURE] == 55
    assert hass.states.get(ids["setpoint"]).state == "55"
    # A partial frame must not wipe what it does not carry.
    assert hass.states.get(ids["climate"]).attributes["current_temperature"] == 40

    await push({"Heating_Enable": 0})
    assert hass.states.get(ids["climate"]).state == "off"
    assert hass.states.get(ids["heating"]).state == STATE_OFF

    await push({"DHW_setpoint": 50, "WarmStar_Tank_Loading_Enable": 0})
    water_heater = hass.states.get(ids["water_heater"])
    assert water_heater.attributes[ATTR_TEMPERATURE] == 50
    assert water_heater.state == STATE_OFF


async def test_app_change_after_an_ha_change_still_wins(hass: HomeAssistant):
    """An optimistic value set by HA does not stick once the app changes it."""
    ids, push = await _set_up_gateway(hass)

    with patch("vaillant_plus_cn_api.VaillantApiClient.control_device"):
        await hass.services.async_call(
            "climate",
            "set_temperature",
            {"entity_id": ids["climate"], ATTR_TEMPERATURE: 60},
            blocking=True,
        )
        await hass.services.async_call(
            "water_heater",
            "turn_off",
            {"entity_id": ids["water_heater"]},
            blocking=True,
        )
    assert hass.states.get(ids["climate"]).attributes[ATTR_TEMPERATURE] == 60
    assert hass.states.get(ids["water_heater"]).state == STATE_OFF

    await push({"Flow_Temperature_Setpoint": 50})
    await push({"WarmStar_Tank_Loading_Enable": 1})
    assert hass.states.get(ids["climate"]).attributes[ATTR_TEMPERATURE] == 50
    assert hass.states.get(ids["setpoint"]).state == "50"
    assert hass.states.get(ids["water_heater"]).state == STATE_ON
