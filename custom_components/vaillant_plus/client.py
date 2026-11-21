"""Vaillant Plus client."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
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
        # Reuse the token stored in the config entry. Without this every start
        # would send unauthenticated requests, get rejected with
        # `{"code":9006,"msg":"token 过期"}` and re-login, which invalidates the
        # session of the Vaillant mobile app.
        self._api_client.update_token(token)

        self._websocket_client: VaillantWebsocketClient | None = None

        self._sleep_task: asyncio.Task | None = None

        self._state = "INITED"

        self._unsub_token_update: Callable[[], None] | None = None

        # One account can have several config entries - one per bound device -
        # and the cloud keeps a single session per account, so a login from one
        # of them invalidates the token every other one is holding. Each entry
        # publishes the token it obtains; listen for those so a refresh
        # anywhere is adopted here instead of answered with a login of our
        # own, which would in turn invalidate theirs.
        self._unsub_token_update = async_dispatcher_connect(
            self._hass,
            EVT_TOKEN_UPDATED.format(token.username),
            self._handle_token_update,
        )

    @callback
    def _handle_token_update(self, token_new: Token) -> None:
        """Adopt a token another config entry obtained for this account."""
        if Token.equals(self._token, token_new):
            return

        _LOGGER.debug("Adopting the token refreshed by another config entry")
        self._token = token_new
        self._api_client.update_token(token_new)

    @property
    def device(self) -> Device:
        return self._device

    @property
    def device_attrs(self) -> dict[str, Any]:
        return self._device_attrs

    @property
    def is_connected(self) -> bool:
        """Return True if the client is connected to the cloud."""
        return self._state != "CLOSED" and self._device is not None

    async def _connect(self) -> None:
        device_list = await self._api_client.get_device_list()
        filtered_device_list = [device for device in device_list if device.id == self._device_id]
        if len(filtered_device_list) == 0:
            raise ShouldUpdateConfigEntry

        self._device = filtered_device_list[0]

        if self._websocket_client is not None:
            try:
                await self._websocket_client.close()
            except Exception:
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
                    self._device_attrs.update(device_attrs)
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

    async def _get_token(self, failed_token: Token | None = None) -> None:
        """Get a working token, by login only if nobody else already did.

        `failed_token` is the token the rejected request used. If the current
        token is no longer that one, another config entry for this account
        refreshed it while this request was in flight, and logging in again
        would invalidate the token it just published - each entry knocking the
        other offline in turn. Adopt theirs instead.
        """
        if failed_token is not None and not Token.equals(self._token, failed_token):
            _LOGGER.debug(
                "Token was refreshed by another config entry, retrying with it"
            )
            self._api_client.update_token(self._token)
            return

        _LOGGER.info("Token expired, retrieve new token...")
        token_new = await self._api_client.login(self._token.username, self._token.password)
        self._token = token_new
        self._api_client.update_token(token_new)
        async_dispatcher_send(
            self._hass, EVT_TOKEN_UPDATED.format(token_new.username), token_new
        )

    async def start(self) -> None:
        """Start connection to cloud."""
        retry_delay = 5
        max_delay = 300  # 5 minutes max
        while self._state != "CLOSED":
            # Remember which token this attempt used, so a rejection can tell
            # "the token is stale" from "another entry already replaced it".
            token_in_use = self._token
            try:
                await self._connect()
                retry_delay = 5  # Reset on success
            except InvalidAuthError:
                try:
                    await self._get_token(token_in_use)
                    retry_delay = 5
                except Exception as error:  # pylint: disable=broad-except
                    # Do not hammer the login endpoint when the credentials
                    # themselves are rejected.
                    retry_delay = min(retry_delay * 2, max_delay)
                    _LOGGER.error(
                        "Failed to refresh the access token: %s, retrying in %ds",
                        error,
                        retry_delay,
                    )
            except ShouldUpdateConfigEntry:
                _LOGGER.error("Device not found, config entry needs update")
                break
            except Exception as error:
                _LOGGER.warning(
                    "Unhandled client exception: %s, retrying in %ds",
                    error,
                    retry_delay,
                )
                retry_delay = min(retry_delay * 2, max_delay)

            self._sleep_task = asyncio.create_task(asyncio.sleep(retry_delay))
            await self._sleep_task

    async def close(self) -> None:
        """Close connection to cloud."""
        if self._websocket_client is not None:
            try:
                await self._websocket_client.close()
            except Exception as error:
                _LOGGER.exception("%s", error)

        if self._sleep_task is not None:
            self._sleep_task.cancel()
            try:
                await self._sleep_task
            except asyncio.CancelledError:
                pass

        self._state = "CLOSED"

        if self._unsub_token_update is not None:
            self._unsub_token_update()
            self._unsub_token_update = None

    async def control_device(self, attrs: dict[str, Any]) -> bool:
        """Send command to control device."""
        retry_times = 0
        while retry_times < 3:
            token_in_use = self._token
            try:
                await self._api_client.control_device(self._device_id, attrs)
                return True
            except InvalidAuthError:
                await self._get_token(token_in_use)
                await asyncio.sleep(retry_times * 5)
                retry_times = retry_times + 1
                _LOGGER.warning("Control device failed due to invalid token, retry %d time", retry_times)

        return False


class ShouldUpdateConfigEntry(HomeAssistantError):
    """Error to reconfigure entry"""
