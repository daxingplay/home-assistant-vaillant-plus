"""Vaillant Plus client."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.dispatcher import async_dispatcher_send
from vaillant_plus_cn_api import (
    EVT_DEVICE_ATTR_UPDATE,
    Device,
    InvalidAuthError,
    Token,
    VaillantApiClient,
    VaillantWebsocketClient,
)

from .const import EVT_DEVICE_CONNECTED, EVT_DEVICE_UPDATED, EVT_TOKEN_UPDATED

_LOGGER = logging.getLogger(__name__)


class VaillantApiHub:
    """API hub for authentication to the cloud."""

    def __init__(self, hass: HomeAssistant, *, retry_interval: int = 3) -> None:
        """Initialize."""
        self._hass = hass
        self._api_client = VaillantApiClient(
            session=aiohttp_client.async_get_clientsession(self._hass)
        )
        self._retry_interval = retry_interval

    async def login(self, username: str, password: str) -> Token:
        """Login to get uid and token."""
        return await self._api_client.login(username=username, password=password)

    async def get_device_list(self, token: str) -> list[Device]:
        """Get device list."""
        return await self._api_client.get_device_list(token)

    async def get_device_info(self, token: str, mac_addr: str) -> dict[str, str]:
        """Get device info"""
        upper_mac = str.upper(mac_addr)
        return await self._api_client.get_device_info(token, upper_mac)

    async def get_device(self, token: Token, device_id: str) -> Device:
        device_list: list[Device] = []
        device: Device | None = None
        succeed = False
        retry_times = 0

        while not succeed:
            if retry_times > 3:
                raise ShouldUpdateConfigEntry

            try:
                device_list = await self.get_device_list(token.token)
                for item in device_list:
                    if item.id == device_id:
                        device = item
                        break

                if device is None:
                    raise ShouldUpdateConfigEntry

                device_info = await self.get_device_info(token.token, device.mac)
                device.model = device_info["model"]
                device.sno = device_info["sno"]
                device.serial_number = device_info["serial_number"]
                succeed = True
                return device
            except InvalidAuthError:
                token_new = await self.login(token.username, token.password)
                async_dispatcher_send(
                    self._hass, EVT_TOKEN_UPDATED.format(token.username), token_new
                )
                succeed = False
                retry_times += 1
                await asyncio.sleep(self._retry_interval)


class VaillantDeviceApiClient:
    """Client to connect to device's cloud websocket endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        hub: VaillantApiHub,
        token: Token,
        device: Device,
    ) -> None:
        """Initialize."""
        self._hub = hub
        self._hass = hass
        self._device = device
        self._token = token
        self._client: VaillantWebsocketClient = VaillantWebsocketClient(
            token,
            device,
            session=aiohttp_client.async_get_clientsession(self._hass),
        )
        self._device_attrs: dict[str, Any] = {}

        @callback
        def device_connected(device_attrs: dict[str, Any]):
            self._device_attrs = device_attrs.copy()
            async_dispatcher_send(
                hass, EVT_DEVICE_CONNECTED.format(device.id), device_attrs
            )

        @callback
        def device_update(event: str, data: dict[str, Any]):
            if event == EVT_DEVICE_ATTR_UPDATE:
                device_attrs = data.get("data", {})
                if len(device_attrs) > 0:
                    self._device_attrs = device_attrs.copy()
                    async_dispatcher_send(
                        hass, EVT_DEVICE_UPDATED.format(device.id), self._device_attrs
                    )

        self._client.on_subscribe(device_connected)
        self._client.on_update(device_update)

    @property
    def client(self) -> VaillantWebsocketClient:
        return self._client

    @property
    def device(self) -> Device:
        return self._device

    @property
    def device_attrs(self) -> dict[str, Any]:
        return self._device_attrs

    async def connect(self) -> None:
        """Connect to cloud. Try to retrieve a new token if token expires."""
        try:
            await self._client.listen()
        except InvalidAuthError:
            token_new = await self._hub.login(
                self._token.username, self._token.password
            )
            self._token = token_new
            self._client._token = token_new
            async_dispatcher_send(
                self._hass, EVT_TOKEN_UPDATED.format(token_new.username), token_new
            )
            await asyncio.sleep(5)
            return await self.connect()

    async def send_command(self, attr: str, value: Any) -> None:
        """Send command about operations for a device to the cloud."""
        if self._client is not None:
            await self._client.send_command(
                "c2s_write", {"did": self._device.id, "attrs": {f"{attr}": value}}
            )

    async def close(self):
        """Close connection to cloud."""
        if self._client is not None:
            await self._client.close()


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class UnknownException(HomeAssistantError):
    """Error that is not known."""


class ShouldUpdateConfigEntry(HomeAssistantError):
    """Error to reconfigure entry"""
