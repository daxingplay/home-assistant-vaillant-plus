"""Vaillant number entities: writable setpoints that are not part of a climate."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import VaillantClient
from .const import API_CLIENT, CONF_DID, DOMAIN
from .discovery import async_register_discovery
from .entity import VaillantEntity

_LOGGER = logging.getLogger(__name__)


NUMBER_DESCRIPTIONS = (
    # The "indoor temperature" knob on the weather compensation page of the
    # Vaillant app (issue #66). It is a different field from the climate
    # target, `Room_Temperature_Setpoint_Comfort`, which has no effect while
    # weather compensation is active. The gateway does not report limits for
    # it, so the range is the usual room setpoint range.
    NumberEntityDescription(
        key="indoor_temperature",
        name="Weather compensation indoor temperature",
        translation_key="indoor_temperature",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=5.0,
        native_max_value=30.0,
        native_step=0.5,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Set up Vaillant number entities."""
    device_id = entry.data.get(CONF_DID)
    client: VaillantClient = hass.data[DOMAIN][API_CLIENT][entry.entry_id]

    added_entities: list[str] = []

    @callback
    def async_new_entities(device_attrs: dict[str, Any]) -> None:
        new_entities = []
        for description in NUMBER_DESCRIPTIONS:
            if (
                description.key in device_attrs
                and description.key not in added_entities
            ):
                new_entities.append(VaillantNumberEntity(client, description))
                added_entities.append(description.key)

        if new_entities:
            async_add_entities(new_entities)

    async_register_discovery(hass, device_id, client, async_new_entities)

    return True


class VaillantNumberEntity(VaillantEntity, NumberEntity):
    """Define a Vaillant number entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        client: VaillantClient,
        description: NumberEntityDescription,
    ) -> None:
        super().__init__(client)
        self.entity_description = description

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.device.id}_{self.entity_description.key}"

    @callback
    def update_from_latest_data(self, data: dict[str, Any]) -> None:
        """Update the entity from the latest data."""
        if self.entity_description.key not in data:
            return

        value = data.get(self.entity_description.key)
        self._attr_native_value = value
        self._attr_available = value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Send the new value to the cloud."""
        _LOGGER.debug("Setting %s to: %s", self.entity_description.key, value)
        await self.send_command(self.entity_description.key, value)
