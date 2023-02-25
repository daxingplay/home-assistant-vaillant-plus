"""Vaillant sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import VaillantDeviceApiClient
from .const import CONF_DID, DISPATCHERS, DOMAIN, EVT_DEVICE_CONNECTED, WEBSOCKET_CLIENT
from .entity import VaillantEntity

_LOGGER = logging.getLogger(__name__)


SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="Room_Temperature_Setpoint_Comfort",
        name="Room temperature setpoint of comfort mode",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Room_Temperature_Setpoint_ECO",
        name="Room temperature setpoint of ECO mode",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Outdoor_Temperature",
        name="Outdoor temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Room_Temperature",
        name="Room temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="DHW_setpoint",
        name="Domestic hot water setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Lower_Limitation_of_CH_Setpoint",
        name="Lower limitation of central heating setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Upper_Limitation_of_CH_Setpoint",
        name="Upper limitation of central heating setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Lower_Limitation_of_DHW_Setpoint",
        name="Lower limitation of domestic hot water",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Upper_Limitation_of_DHW_Setpoint",
        name="Upper limitation of domestic hot water",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Current_DHW_Setpoint",
        name="Current domestic hot water setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Flow_Temperature_Setpoint",
        name="Flow temperature setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Flow_temperature",
        name="Flow temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="return_temperature",
        name="Return flow temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Tank_temperature",
        name="Water tank temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Set up Vaillant sensors."""
    device_id = entry.data.get(CONF_DID)
    client: VaillantDeviceApiClient = hass.data[DOMAIN][WEBSOCKET_CLIENT][
        entry.entry_id
    ]

    added_entities = []

    @callback
    def async_new_entities(device_attrs: dict[str, Any]):
        _LOGGER.debug("add vaillant sensor entities. device attrs: %s", device_attrs)
        new_entities = []
        for description in SENSOR_DESCRIPTIONS:
            if (
                description.key in device_attrs
                and description.key not in added_entities
            ):
                new_entities.append(VaillantSensorEntity(client, description))
                added_entities.append(description.key)

        if len(new_entities) > 0:
            async_add_entities(new_entities)

    unsub = async_dispatcher_connect(
        hass, EVT_DEVICE_CONNECTED.format(device_id), async_new_entities
    )

    hass.data[DOMAIN][DISPATCHERS][device_id].append(unsub)

    return True


class VaillantSensorEntity(VaillantEntity, SensorEntity):
    """Define a Vaillant sensor entity."""

    def __init__(
        self,
        client: VaillantDeviceApiClient,
        description: SensorEntityDescription,
    ):
        super().__init__(client)
        self.entity_description = description

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.device.id}_{self.entity_description.key}"

    @callback
    def update_from_latest_data(self, data: dict[str, Any]) -> None:
        """Update the entity from the latest data."""

        value = data.get(self.entity_description.key)
        self._attr_native_value = value
        self._attr_available = value is not None
