"""The Vaillant Plus climate platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_HALVES, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import VaillantDeviceApiClient
from .const import (
    CONF_DID,
    DISPATCHERS,
    DOMAIN,
    EVT_DEVICE_CONNECTED,
    WATER_HEATER_OFF,
    WATER_HEATER_ON,
    WEBSOCKET_CLIENT,
)
from .entity import VaillantEntity

# from .entity import VaillantCoordinator, VaillantEntity

_LOGGER = logging.getLogger(__name__)

DEFAULT_TEMPERATURE_INCREASE = 0.5

SUPPORTED_FEATURES = (
    WaterHeaterEntityFeature.TARGET_TEMPERATURE
    | WaterHeaterEntityFeature.OPERATION_MODE
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback
) -> bool:
    """Set up Vaillant devices from a config entry."""

    device_id = entry.data.get(CONF_DID)
    client: VaillantDeviceApiClient = hass.data[DOMAIN][WEBSOCKET_CLIENT][
        entry.entry_id
    ]

    added_entities = []

    @callback
    def async_new_water_heater(device_attrs: dict[str, Any]):
        _LOGGER.debug("New water heater found, %s", device_attrs)
        if "water_heater" not in added_entities:
            if device_attrs.get("DHW_setpoint") is not None:
                new_devices = [VaillantWaterHeater(client)]
                async_add_devices(new_devices)
                added_entities.append("water_heater")
            else:
                _LOGGER.warning(
                    "Missing required attribute to setup Vaillant Water Heater. skip."
                )
        else:
            _LOGGER.debug("Already added water_heater device. skip.")

    unsub = async_dispatcher_connect(
        hass, EVT_DEVICE_CONNECTED.format(device_id), async_new_water_heater
    )

    hass.data[DOMAIN][DISPATCHERS][device_id].append(unsub)

    return True


class VaillantWaterHeater(VaillantEntity, WaterHeaterEntity):
    """Vaillant vSMART Water Heater."""

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""

        return f"{self.device.id}_water_heater"

    @property
    def name(self) -> str:
        """Return the name of the water heater."""

        return self.device.product_name

    @property
    def supported_features(self) -> int:
        """Return the flag of supported features for the climate."""

        return SUPPORTED_FEATURES

    @property
    def precision(self) -> float:
        """Return the precision of the system."""
        return PRECISION_HALVES

    @property
    def temperature_unit(self) -> str:
        """Return the measurement unit for all temperature values."""

        return UnitOfTemperature.CELSIUS

    @property
    def current_operation(self) -> str | None:
        """Return current operation ie. eco, electric, performance, ..."""
        value = self.get_device_attr("Enabled_DHW")
        if value is None:
            return None
        if value == 1:
            return WATER_HEATER_ON
        return WATER_HEATER_OFF

    @property
    def operation_list(self) -> list[str] | None:
        """Return the list of available operation modes."""
        return [WATER_HEATER_ON, WATER_HEATER_OFF]

    @property
    def current_temperature(self) -> float:
        """Return the current dhw temperature. FIXME"""

        return self.get_device_attr("Tank_Temperature")

    @property
    def target_temperature(self) -> float:
        """Return the targeted dhw temperature. Current_DHW_Setpoint or DHW_setpoint"""

        return self.get_device_attr("DHW_setpoint")

    @property
    def target_temperature_high(self) -> float | None:
        """Return the highbound target temperature we try to reach."""
        return self.get_device_attr("Upper_Limitation_of_DHW_Setpoint")

    @property
    def target_temperature_low(self) -> float | None:
        """Return the lowbound target temperature we try to reach."""
        return self.get_device_attr("Lower_Limitation_of_DHW_Setpoint")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        new_temperature = kwargs.get(ATTR_TEMPERATURE)
        if new_temperature is None:
            return

        _LOGGER.debug("Setting target temperature to: %s", new_temperature)

        await self.send_command(
            "DHW_setpoint",
            new_temperature,
        )

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        value = 1
        if operation_mode == WATER_HEATER_OFF:
            value = 0

        _LOGGER.debug("Setting operation mode to: %s", value)

        await self.send_command("WarmStar_Tank_Loading_Enable", value)

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return self.get_device_attr("Lower_Limitation_of_DHW_Setpoint")

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return self.get_device_attr("Upper_Limitation_of_DHW_Setpoint")
