"""Vaillant Plus client."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from vaillant_plus_cn_api import (
    EVT_DEVICE_ATTR_UPDATE,
    Device,
    InvalidAuthError,
    Token,
    VaillantApiClient,
    VaillantWebsocketClient,
)

from .utils import get_aiohttp_session
from .const import EVT_DEVICE_CONNECTED, EVT_DEVICE_UPDATED, EVT_TOKEN_UPDATED

_LOGGER = logging.getLogger(__name__)

class VaillantClient:
    """API client for communicating with the cloud."""

    def __init__(
        self,
        hass: HomeAssistant,
        token: Token,
        device_id: str,
    ) -> None:
        self._hass = hass
        self._device_id = device_id
        self._device_attrs: dict[str, Any] = {}
        self._device: Device | None = None
        self._token = token

        self._api_client = VaillantApiClient(session=get_aiohttp_session(self._hass))

        self._websocket_client: VaillantWebsocketClient | None = None

        self._failed_attempts: int = 0
        self._sleep_task: asyncio.Task | None = None

        self._state = "INITED"

    @property
    def device(self) -> Device:
        return self._device

    @property
    def device_attrs(self) -> dict[str, Any]:
        return self._device_attrs

    async def _connect(self) -> None:
        device_list = await self._api_client.get_device_list()
        filtered_device_list = [device for device in device_list if device.id == self._device_id]
        if len(filtered_device_list) == 0:
            raise ShouldUpdateConfigEntry

        self._device = filtered_device_list[0]

        if self._websocket_client is not None:
            try:
                await self._websocket_client.close()
            except:
                pass

        @callback
        def device_connected(device_attrs: dict[str, Any]):
            self._device_attrs = device_attrs.copy()
            async_dispatcher_send(
                self._hass, EVT_DEVICE_CONNECTED.format(self._device_id), device_attrs.copy()
            )

        @callback
        def device_update(event: str, data: dict[str, Any]):
            if event == EVT_DEVICE_ATTR_UPDATE:
                device_attrs: dict[str, Any] = data.get("data", {})
                if len(device_attrs) > 0:
                    self._device_attrs = device_attrs.copy()
                    async_dispatcher_send(
                        self._hass, EVT_DEVICE_UPDATED.format(self._device.id), device_attrs.copy()
                    )

        self._websocket_client = VaillantWebsocketClient(
            token=self._token,
            device=self._device,
            session=get_aiohttp_session(self._hass),
        )
        self._websocket_client.on_subscribe(device_connected)
        self._websocket_client.on_update(device_update)

        await self._websocket_client.connect()

    async def _get_token(self) -> None:
        _LOGGER.info("Token expired, retrieve new token...")
        token_new = await self._api_client.login(self._token.username, self._token.password)
        self._token = token_new
        self._api_client.update_token(token_new)
        async_dispatcher_send(
            self._hass, EVT_TOKEN_UPDATED.format(token_new.username), token_new
        )

    async def start(self) -> None:
        """Start connection to cloud."""
        while self._state != "CLOSED":
            try:
                await self._connect()
            except InvalidAuthError:
                await self._get_token()
            except Exception as error:
                _LOGGER.warning("Unhandled client exception: %s", error)

            self._sleep_task = asyncio.create_task(asyncio.sleep(5))
            await self._sleep_task

    async def close(self) -> None:
        """Close connection to cloud."""
        if self._websocket_client is not None:
            try:
                await self._websocket_client.close()
            except Exception as error:
                _LOGGER.exception(error)
                pass

        if self._sleep_task is not None:
            self._sleep_task.cancel()
            try:
                await self._sleep_task
            except asyncio.CancelledError:
                pass

        self._state = "CLOSED"

    async def control_device(self, attrs: dict[str, Any]) -> bool:
        """Send command to control device."""
        retry_times = 0
        while retry_times < 3:
            try:
                await self._api_client.control_device(self._device_id, attrs)
                return True
            except InvalidAuthError:
                await self._get_token()
                await asyncio.sleep(retry_times * 5)
                retry_times = retry_times + 1
                _LOGGER.warning("Control device failed due to invaild token, retry %d time", retry_times)

        return False



class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class UnknownException(HomeAssistantError):
    """Error that is not known."""


class ShouldUpdateConfigEntry(HomeAssistantError):
    """Error to reconfigure entry"""
