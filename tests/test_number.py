"""Test the vaillant-plus number platform."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vaillant_plus import PLATFORMS
from custom_components.vaillant_plus.const import API_CLIENT, DOMAIN
from custom_components.vaillant_plus.number import (
    NUMBER_DESCRIPTIONS,
    VaillantNumberEntity,
)

from .const import MOCK_CONFIG_ENTRY_DATA, MOCK_DEVICE_ATTRS_WHEN_CONNECT, MOCK_DID

INDOOR_TEMPERATURE = NUMBER_DESCRIPTIONS[0]


def test_number_platform_is_set_up():
    """A platform missing from PLATFORMS is never imported, silently (#66)."""
    assert Platform.NUMBER in PLATFORMS


async def _setup(hass: HomeAssistant, device_attrs: dict):
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID
    )
    config_entry.add_to_hass(hass)

    with patch("vaillant_plus_cn_api.VaillantWebsocketClient.connect"):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    client = hass.data[DOMAIN][API_CLIENT][config_entry.entry_id]
    client._websocket_client._on_subscribe_handler(device_attrs)
    await hass.async_block_till_done()
    return config_entry, client


async def test_indoor_temperature_is_writable(
    hass: HomeAssistant, bypass_login, bypass_get_device
):
    """The weather compensation indoor temperature is exposed and writable."""
    config_entry, client = await _setup(
        hass, {**MOCK_DEVICE_ATTRS_WHEN_CONNECT, "indoor_temperature": 20.0}
    )

    entity_id = er.async_get(hass).async_get_entity_id(
        NUMBER_DOMAIN, DOMAIN, "1_indoor_temperature"
    )
    assert entity_id is not None

    state = hass.states.get(entity_id)
    assert float(state.state) == 20.0
    assert state.attributes["min"] == 5.0
    assert state.attributes["max"] == 30.0
    assert state.attributes["step"] == 0.5
    assert state.attributes["unit_of_measurement"] == "°C"

    with patch.object(
        client, "control_device", AsyncMock(return_value=True)
    ) as control_device:
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: 21.5},
            blocking=True,
        )

    control_device.assert_awaited_once_with({"indoor_temperature": 21.5})
    assert float(hass.states.get(entity_id).state) == 21.5

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_no_entity_without_the_attribute(
    hass: HomeAssistant, bypass_login, bypass_get_device
):
    """Devices that do not report the field get no number entity."""
    config_entry, _ = await _setup(hass, MOCK_DEVICE_ATTRS_WHEN_CONNECT)

    assert (
        er.async_get(hass).async_get_entity_id(
            NUMBER_DOMAIN, DOMAIN, "1_indoor_temperature"
        )
        is None
    )

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_failed_command_raises_and_keeps_the_value(hass, device_api_client):
    """An undelivered command must not look like it succeeded."""
    number = VaillantNumberEntity(device_api_client, INDOOR_TEMPERATURE)
    number.update_from_latest_data({"indoor_temperature": 20.0})

    with patch(
        "custom_components.vaillant_plus.VaillantClient.control_device",
        AsyncMock(return_value=False),
    ):
        with pytest.raises(HomeAssistantError):
            await number.async_set_native_value(22.0)

    assert number.native_value == 20.0


async def test_missing_value_marks_unavailable(hass, device_api_client):
    """A null value from the gateway leaves the entity unavailable."""
    number = VaillantNumberEntity(device_api_client, INDOOR_TEMPERATURE)

    number.update_from_latest_data({"indoor_temperature": None})
    assert number._attr_available is False

    number.update_from_latest_data({"Room_Temperature": 18.0})
    assert number._attr_available is False

    number.update_from_latest_data({"indoor_temperature": 19.5})
    assert number._attr_available is True
    assert number.native_value == 19.5
