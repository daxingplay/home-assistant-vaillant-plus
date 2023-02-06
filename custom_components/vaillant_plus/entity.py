"""Vaillant vSMART entity classes."""
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .client import VaillantDeviceApiClient
from .const import DOMAIN, EVT_DEVICE_UPDATED

from vaillant_plus_cn_api import Device

UPDATE_INTERVAL = timedelta(minutes=1)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class VaillantEntity(Entity):
    """Base class for Vaillant entities."""

    def __init__(
        self,
        client: VaillantDeviceApiClient,
    ):
        """Initialize."""
        self._client = client

    @property
    def device_attrs(self) -> dict[str, Any]:
        return self._client.device_attrs

    @property
    def device(self) -> Device:
        return self._client.device

    def get_device_attr(self, attr) -> Any:
        if hasattr(self._client.device_attrs, attr):
            return self._client.device_attrs.get(attr)
        return None

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        @callback
        def update(data: dict[str, Any]) -> None:
            """Update the state."""
            _LOGGER.debug("write ha state: %s", data)
            self.update_from_latest_data(data)
            self.async_write_ha_state()

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
    def device_info(self) -> dict[str, Any]:
        """Return all device info available for this entity."""

        return {
            "identifiers": {(DOMAIN, self.device.id)},
            "name": self.device.model,
            "sw_version": self.device.mcu_soft_version,
            "manufacturer": "Vaillant",
            "via_device": (DOMAIN, self.device.id),
        }

    @callback
    def update_from_latest_data(self, data: dict[str, Any]) -> None:
        """Update the entity from the latest data."""

    async def send_command(self, attr: str, value: Any) -> None:
        await self._client.send_command(attr, value)
