"""Vaillant vSMART entity classes."""
import logging
from typing import Any

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from vaillant_plus_cn_api import Device

from .client import VaillantClient
from .const import DOMAIN, EVT_DEVICE_UPDATED

_LOGGER: logging.Logger = logging.getLogger(__package__)


class VaillantEntity(Entity):
    """Base class for Vaillant entities."""

    def __init__(
        self,
        client: VaillantClient,
    ):
        """Initialize."""
        self._client = client

    @property
    def device_attrs(self) -> dict[str, Any]:
        return self._client.device_attrs

    @property
    def device(self) -> Device:
        return self._client.device

    def get_device_attr(self, attr: str) -> Any:
        return self._client.device_attrs.get(attr)

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        @callback
        def update(data: dict[str, Any]) -> None:
            """Update the state."""
            _LOGGER.debug("write ha state: %s", data)
            self.update_from_latest_data(data)
            self.async_schedule_update_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, EVT_DEVICE_UPDATED.format(self.device.id), update
            )
        )

        if len(self.device_attrs) > 0:
            self.update_from_latest_data(self.device_attrs)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        """Return True if the entity has device data from an active connection."""
        if not self._client.is_connected or len(self.device_attrs) == 0:
            return False
        # Platforms mark themselves unavailable when their own attribute is
        # missing from the payload; `_attr_available` defaults to True.
        return self._attr_available

    @property
    def device_info(self) -> DeviceInfo:
        """Return all device info available for this entity."""

        return DeviceInfo(
            identifiers={(DOMAIN, self.device.id)},
            name=self.device.product_name,
            model=self.device.model,
            # sw_version=self.device.mcu_soft_version,
            # hw_version=self.device.mcu_hard_version,
            manufacturer="Vaillant",
        )

    @callback
    def update_from_latest_data(self, data: dict[str, Any]) -> None:
        """Update the entity from the latest data."""

    @callback
    def set_optimistic_value(self, attr: str, value: Any) -> None:
        """Apply a value locally without waiting for the device to echo it.

        The cloud can take several seconds to report a change back over the
        websocket; until then the UI would snap back to the old value.
        """
        self._client.device_attrs[attr] = value
        self.update_from_latest_data({attr: value})
        if self.hass is not None:
            self.async_write_ha_state()

    async def send_command(self, attr: str, value: Any) -> None:
        """Send one attribute to the cloud and apply it locally."""
        await self.send_commands({attr: value})

    async def send_commands(self, attrs: dict[str, Any]) -> None:
        """Send attributes to the cloud and apply them locally.

        `control_device` returns False once it has exhausted its retries, which
        means the command never reached the cloud and nothing will re-send it.
        Raise, so the failure reaches the user instead of looking like a
        successful command, and do not apply the values locally: the device
        still holds its old state.
        """
        if not await self._client.control_device(attrs):
            raise HomeAssistantError(
                f"Failed to send {list(attrs)} to the Vaillant cloud"
            )

        for attr, value in attrs.items():
            self.set_optimistic_value(attr, value)
