"""Vaillant number entities: settings that are not part of a climate.

A gateway reports `indoor_temperature`. With a room sensor paired it is that
sensor's reading, shown by the read-only sensor. Without one it reads 255, and
the value is the indoor temperature weather compensation works with, which the
Vaillant app lets the user set (issue #66). Once written it no longer reads
255, so a setting cannot be told from a measurement by its value: the first
255 is recorded in the config entry, and the device keeps the setting from
then on.
"""
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
from .const import API_CLIENT, CONF_DID, CONF_NO_ROOM_SENSOR, DOMAIN
from .device import VaillantDeviceType, resolve_device_type
from .discovery import async_register_discovery
from .entity import VaillantEntity
from .utils import TEMPERATURE_SENTINELS, valid_temperature

_LOGGER = logging.getLogger(__name__)

INDOOR_TEMPERATURE = "indoor_temperature"

NUMBER_DESCRIPTIONS = (
    # The gateway reports no limits for it, so the usual room setpoint range.
    NumberEntityDescription(
        key=INDOOR_TEMPERATURE,
        name="Indoor temperature setting",
        translation_key="indoor_temperature_setting",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=5.0,
        native_max_value=30.0,
        native_step=0.5,
    ),
)


def has_no_room_sensor(entry: ConfigEntry) -> bool:
    """Return whether this gateway was seen without a room sensor."""
    return bool(entry.data.get(CONF_NO_ROOM_SENSOR))


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Set up Vaillant number entities."""
    device_id = entry.data.get(CONF_DID)
    client: VaillantClient = hass.data[DOMAIN][API_CLIENT][entry.entry_id]

    added_entities: list[str] = []

    @callback
    def async_new_entities(device_attrs: dict[str, Any]) -> None:
        if added_entities:
            return
        if resolve_device_type(client.device) is not VaillantDeviceType.GATEWAY:
            return
        if INDOOR_TEMPERATURE not in device_attrs:
            return

        if not has_no_room_sensor(entry):
            # With no boiler on the bus every reading is a sentinel, which says
            # nothing about a room sensor.
            if device_attrs.get("ebus_status") == 0:
                return
            if device_attrs[INDOOR_TEMPERATURE] not in TEMPERATURE_SENTINELS:
                return
            _LOGGER.info(
                "Gateway %s reports no room sensor; offering its indoor"
                " temperature as a setting",
                device_id,
            )
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_NO_ROOM_SENSOR: True}
            )

        added_entities.append(INDOOR_TEMPERATURE)
        async_add_entities(
            [VaillantNumberEntity(client, description) for description in NUMBER_DESCRIPTIONS]
        )

    async_register_discovery(hass, device_id, client, async_new_entities)

    return True


class VaillantNumberEntity(VaillantEntity, NumberEntity):
    """A writable Vaillant setting."""

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
        key = self.entity_description.key
        if key not in data:
            return
        # 255 until it is first set: unknown, but still settable.
        self._attr_native_value = valid_temperature(data.get(key))

    async def async_set_native_value(self, value: float) -> None:
        """Write the new value to the device."""
        await self.send_command(self.entity_description.key, value)
