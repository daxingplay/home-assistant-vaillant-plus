from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Literal

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import VaillantDeviceApiClient
from .const import CONF_DID, DISPATCHERS, DOMAIN, EVT_DEVICE_CONNECTED, WEBSOCKET_CLIENT
from .entity import VaillantEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class VaillantBinarySensorDescriptionMixin:
    """Define an entity description mixin for binary sensors."""

    on_state: Literal[False, True]


@dataclass
class VaillantBinarySensorDescription(
    BinarySensorEntityDescription, VaillantBinarySensorDescriptionMixin
):
    """Describe a Vaillant binary sensor."""


BINARY_SENSOR_DESCRIPTIONS = (
    VaillantBinarySensorDescription(
        key="Circulation_Enable",
        name="Circulation",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        on_state=True,
    ),
    VaillantBinarySensorDescription(
        key="Heating_Enable",
        name="Heating",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        on_state=True,
    ),
    VaillantBinarySensorDescription(
        key="WarmStar_Tank_Loading_Enable",
        name="WarmStar tank loading",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        on_state=True,
    ),
    VaillantBinarySensorDescription(
        key="Enabled_Heating",
        name="Heating boiler",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        on_state=True,
    ),
    VaillantBinarySensorDescription(
        key="Enabled_DHW",
        name="Domestic hot water",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        on_state=True,
    ),
    VaillantBinarySensorDescription(
        key="BMU_Platform",
        name="BMU platform",
        # device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        on_state=True,
    ),
    VaillantBinarySensorDescription(
        key="Weather_compensation",
        name="Weather compensation",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        on_state=True,
    ),
    VaillantBinarySensorDescription(
        key="RF_Status",
        name="EBus status",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        on_state=True,
    ),
    VaillantBinarySensorDescription(
        key="Boiler_info3_bit0",
        name="Boiler heating demand",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        on_state=True,
    ),
    VaillantBinarySensorDescription(
        key="Boiler_info5_bit4",
        name="Boiler need refill water",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        on_state=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Set up Vaillant binary sensors."""
    device_id = entry.data.get(CONF_DID)
    client: VaillantDeviceApiClient = hass.data[DOMAIN][WEBSOCKET_CLIENT][
        entry.entry_id
    ]

    added_entities = []

    @callback
    def async_new_entities(device_attrs: dict[str, Any]):
        _LOGGER.debug(
            "add vaillant binary sensor entities. device attrs: %s", device_attrs
        )
        new_entities = []
        for description in BINARY_SENSOR_DESCRIPTIONS:
            if (
                description.key in device_attrs
                and description.key not in added_entities
            ):
                new_entities.append(VaillantBinarySensorEntity(client, description))
                added_entities.append(description.key)

        if len(new_entities) > 0:
            async_add_entities(new_entities)

    unsub = async_dispatcher_connect(
        hass, EVT_DEVICE_CONNECTED.format(device_id), async_new_entities
    )

    hass.data[DOMAIN][DISPATCHERS][device_id].append(unsub)

    return True


class VaillantBinarySensorEntity(VaillantEntity, BinarySensorEntity):
    """Define a Vaillant binary sensor entity."""

    entity_description: VaillantBinarySensorDescription

    def __init__(
        self,
        client: VaillantDeviceApiClient,
        description: VaillantBinarySensorDescription,
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
        self._attr_available = data[self.entity_description.key] is not None

        value: Any = data.get(self.entity_description.key)
        if self.entity_description.key == "RF_Status":
            self._attr_is_on = value == 3
        elif self.entity_description.key == "Boiler_info3_bit0":
            self._attr_is_on = value[0] == 1
        elif self.entity_description.key == "Boiler_info5_bit4":
            self._attr_is_on = value[0] == 1
        else:
            self._attr_is_on = value is True
