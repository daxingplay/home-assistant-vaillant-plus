"""The Vaillant Plus integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.typing import ConfigType
from vaillant_plus_cn_api import Token

from .client import VaillantClient
from .const import (
    API_CLIENT,
    CONF_DID,
    CONF_TOKEN,
    DISPATCHERS,
    DOMAIN,
    EVT_TOKEN_UPDATED,
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
        {API_CLIENT: {}, DISPATCHERS: {}},
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Vaillant Plus from a config entry."""

    token = Token.deserialize(entry.data.get(CONF_TOKEN))
    device_id = entry.data.get(CONF_DID)
    client = VaillantClient(hass, token, device_id)

    async def close_client(_):
        await client.close()

    hass.data[DOMAIN][API_CLIENT][entry.entry_id] = client

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

    unsub_stop = hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, close_client)
    hass.data[DOMAIN][DISPATCHERS][device_id].append(unsub_stop)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    hass.loop.create_task(client.start())

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        if (
            entry.entry_id in hass.data[DOMAIN][API_CLIENT]
            and hass.data[DOMAIN][API_CLIENT][entry.entry_id] is not None
        ):
            try:
                await hass.data[DOMAIN][API_CLIENT][entry.entry_id].close()
            except:
                pass
        hass.data[DOMAIN][API_CLIENT].pop(entry.entry_id)

    device_id = entry.data.get(CONF_DID)
    dispatchers = hass.data[DOMAIN][DISPATCHERS].pop(device_id)
    for unsub in dispatchers:
        unsub()

    return unload_ok
