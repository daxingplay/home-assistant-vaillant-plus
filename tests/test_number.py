"""The gateway's indoor temperature setting.

`indoor_temperature` is a paired room sensor's reading or, without one, the
indoor temperature weather compensation works with. The value cannot say
which, so every gateway with a boiler is offered the setting and the user
decides whether to use it.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNKNOWN
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry
from vaillant_plus_cn_api import Device

from custom_components.vaillant_plus.const import (
    API_CLIENT,
    DISPATCHERS,
    DOMAIN,
    EVT_DEVICE_CONNECTED,
)
from custom_components.vaillant_plus.number import (
    NUMBER_DESCRIPTIONS,
    VaillantNumberEntity,
    async_setup_entry,
)

from .const import MOCK_CONFIG_ENTRY_DATA, MOCK_DID

GATEWAY = 1
VSMART = 0


async def _setup(hass, device_api_client, platform=GATEWAY, data=None):
    entry = MockConfigEntry(domain=DOMAIN, data={"did": "1", **(data or {})}, entry_id="1")
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {API_CLIENT: {}, DISPATCHERS: {}})
    hass.data[DOMAIN][API_CLIENT][entry.entry_id] = device_api_client
    hass.data[DOMAIN][DISPATCHERS]["1"] = []
    device_api_client._device.platform = platform

    added = []
    await async_setup_entry(hass, entry, added.extend)
    return entry, added


async def _connect(hass, device_api_client, attrs):
    device_api_client._device_attrs = dict(attrs)
    async_dispatcher_send(hass, EVT_DEVICE_CONNECTED.format("1"), dict(attrs))
    await hass.async_block_till_done()


@pytest.mark.parametrize("indoor_temperature", [255, 21])
async def test_every_gateway_with_a_boiler_gets_the_setting(
    hass, device_api_client, indoor_temperature
):
    """With or without a room sensor: the user decides whether to set it."""
    _, added = await _setup(hass, device_api_client)

    await _connect(
        hass,
        device_api_client,
        {"indoor_temperature": indoor_temperature, "ebus_status": 1},
    )

    assert len(added) == 1
    number = added[0]
    number.update_from_latest_data(device_api_client.device_attrs)
    # 255 until it is set: unknown, but still settable.
    assert number.native_value == (None if indoor_temperature == 255 else 21)
    assert number.available is True


async def test_gateway_without_a_boiler_gets_no_setting_until_one_connects(
    hass, device_api_client
):
    _, added = await _setup(hass, device_api_client)

    await _connect(hass, device_api_client, {"indoor_temperature": 255, "ebus_status": 0})
    assert added == []

    await _connect(hass, device_api_client, {"indoor_temperature": 255, "ebus_status": 1})
    assert len(added) == 1


async def test_vsmart_gets_no_setting(hass, device_api_client):
    _, added = await _setup(hass, device_api_client, platform=VSMART)

    await _connect(hass, device_api_client, {"indoor_temperature": 255, "ebus_status": 1})

    assert added == []


async def test_setting_the_value_writes_indoor_temperature(hass, device_api_client):
    device_api_client._device_attrs = {"indoor_temperature": 255}
    number = VaillantNumberEntity(device_api_client, NUMBER_DESCRIPTIONS[0])

    with patch(
        "custom_components.vaillant_plus.VaillantClient.control_device",
        return_value=True,
    ) as control:
        await number.async_set_native_value(21.5)

    control.assert_awaited_once_with({"indoor_temperature": 21.5})
    assert number.native_value == 21.5


async def test_a_failed_write_raises_and_keeps_the_value(hass, device_api_client):
    device_api_client._device_attrs = {"indoor_temperature": 20}
    number = VaillantNumberEntity(device_api_client, NUMBER_DESCRIPTIONS[0])
    number.update_from_latest_data(device_api_client.device_attrs)

    with patch(
        "custom_components.vaillant_plus.VaillantClient.control_device",
        return_value=False,
    ), pytest.raises(HomeAssistantError):
        await number.async_set_native_value(22)

    assert number.native_value == 20
    assert device_api_client.device_attrs["indoor_temperature"] == 20


async def test_end_to_end_through_the_config_entry(hass, bypass_login):
    """Set it through the number service, as a user would."""
    from custom_components.vaillant_plus import async_setup

    gateway = Device(
        id=MOCK_DID, mac="m", product_key="pk", product_id="81", product_name="pn",
        product_verbose_name="WiFiGateway", is_online=True, is_manager=True,
        group_id=2, sno="sno", create_time="2000-01-01 00:00:00", model_alias="",
        model="model_name", serial_number="s1", services_count=0,
        last_offline_time="2000-12-31 00:00:00", platform=GATEWAY,
    )
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID)
    entry.add_to_hass(hass)

    with patch(
        "vaillant_plus_cn_api.VaillantApiClient.get_device_list",
        return_value=[gateway],
    ), patch("vaillant_plus_cn_api.VaillantWebsocketClient.connect"), patch(
        "vaillant_plus_cn_api.VaillantApiClient.control_device",
        AsyncMock(return_value=True),
    ) as control:
        assert await async_setup(hass, {})
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED

        client = hass.data[DOMAIN][API_CLIENT][entry.entry_id]._websocket_client
        client._on_subscribe_handler(
            {"indoor_temperature": 255, "ebus_status": 1, "Heating_Enable": 1}
        )
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        number_id = registry.async_get_entity_id("number", DOMAIN, "1_indoor_temperature")
        assert number_id is not None
        assert hass.states.get(number_id).state == STATE_UNKNOWN

        await hass.services.async_call(
            "number", "set_value", {"entity_id": number_id, "value": 21}, blocking=True
        )
        control.assert_awaited_once()
        assert control.await_args.args[-1] == {"indoor_temperature": 21}
        assert float(hass.states.get(number_id).state) == 21
