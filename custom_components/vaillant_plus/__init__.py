"""The Vaillant Plus integration."""
from __future__ import annotations

from typing import Any
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.typing import ConfigType

from vaillant_plus_cn_api import (
    VaillantApiClient,
    VaillantWebsocketClient,
    Token,
    Device,
    InvalidAuthError,
    EVT_DEVICE_ATTR_UPDATE,
)

from .client import VaillantApiHub, VaillantDeviceApiClient
from .const import (
    API_HUB,
    CONF_DID,
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_TOKEN,
    CONF_UID,
    CONF_USERNAME,
    DISPATCHERS,
    DOMAIN,
    EVT_DEVICE_CONNECTED,
    EVT_DEVICE_UPDATED,
    EVT_TOKEN_UPDATED,
    WEBSOCKET_CLIENT,
)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.WATER_HEATER,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(
        DOMAIN,
        {API_HUB: VaillantApiHub(hass), DISPATCHERS: {}, WEBSOCKET_CLIENT: {}},
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Vaillant Plus from a config entry."""

    hub: VaillantApiHub = hass.data[DOMAIN][API_HUB]
    token = Token.deserialize(entry.data.get(CONF_TOKEN))
    device_id = entry.data.get(CONF_DID)

    @callback
    def on_token_update(token_new: Token) -> None:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_TOKEN: token_new.serialize()}
        )

    unsub = async_dispatcher_connect(
        hass,
        EVT_TOKEN_UPDATED.format(token.username),
        on_token_update,
    )

    hass.data[DOMAIN][DISPATCHERS].setdefault(device_id, [])
    hass.data[DOMAIN][DISPATCHERS][device_id].append(unsub)

    device = await hub.get_device(token, device_id)
    client = VaillantDeviceApiClient(hass, hub, token, device)

    hass.data[DOMAIN][WEBSOCKET_CLIENT][entry.entry_id] = client

    def close_client(_):
        return client.close()

    unsub_stop = hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, close_client)
    hass.data[DOMAIN][DISPATCHERS][device_id].append(unsub_stop)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    hass.loop.create_task(client.connect())

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        if (
            entry.entry_id in hass.data[DOMAIN]
            and hass.data[DOMAIN][entry.entry_id] is not None
        ):
            await hass.data[DOMAIN][entry.entry_id].close()
        hass.data[DOMAIN].pop(entry.entry_id)

    device_id = entry.data.get(CONF_DID)
    dispatchers = hass.data[DOMAIN][DISPATCHERS].pop(device_id)
    for unsub in dispatchers:
        unsub()

    return unload_ok
