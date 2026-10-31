"""The Vaillant Plus water heater platform."""
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
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import VaillantClient
from .const import (
    CONF_DID,
    DOMAIN,
    WATER_HEATER_OFF,
    WATER_HEATER_ON,
    API_CLIENT,
)
from .discovery import MissingAttributeWarning, async_register_discovery
from .entity import VaillantEntity
from .utils import valid_temperature

# from .entity import VaillantCoordinator, VaillantEntity

_LOGGER = logging.getLogger(__name__)

DEFAULT_TEMPERATURE_INCREASE = 0.5

# Fallbacks for gateways that do not report the DHW setpoint limits. Home
# Assistant raises when min_temp/max_temp are None, which breaks every state
# write for the entity.
DEFAULT_MIN_TEMPERATURE = 35.0
DEFAULT_MAX_TEMPERATURE = 65.0

DHW_ENABLE_ATTRS = (
    "WarmStar_Tank_Loading_Enable",
    "Enabled_DHW",
    "DHW_switch",
)
DHW_SETPOINT_ATTRS = ("Current_DHW_Setpoint", "DHW_readSetPoint", "DHW_setpoint")

SUPPORTED_FEATURES = (
    WaterHeaterEntityFeature.TARGET_TEMPERATURE
    | WaterHeaterEntityFeature.OPERATION_MODE
    | WaterHeaterEntityFeature.ON_OFF
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback
) -> bool:
    """Set up Vaillant devices from a config entry."""

    device_id = entry.data.get(CONF_DID)
    client: VaillantClient = hass.data[DOMAIN][API_CLIENT][
        entry.entry_id
    ]

    added_entities = []
    missing_attribute_warning = MissingAttributeWarning(_LOGGER, "Water Heater")

    @callback
    def async_new_water_heater(device_attrs: dict[str, Any]):
        if "water_heater" in added_entities:
            _LOGGER.debug("Already added water_heater device. skip.")
            return

        if all(device_attrs.get(attr) is None for attr in DHW_SETPOINT_ATTRS):
            missing_attribute_warning.report(DHW_SETPOINT_ATTRS, device_attrs)
            return

        _LOGGER.debug("New water heater found, %s", device_attrs)
        added_entities.append("water_heater")
        async_add_devices([VaillantWaterHeater(client)])

    async_register_discovery(hass, device_id, client, async_new_water_heater)

    return True


class VaillantWaterHeater(VaillantEntity, WaterHeaterEntity):
    """Vaillant vSMART Water Heater."""

    # The main feature of the device: it carries the device name itself.
    _attr_has_entity_name = True

    def _dhw_enabled_value(self) -> Any:
        """Return the current DHW enable value from known API variants."""
        for attr in DHW_ENABLE_ATTRS:
            value = self.get_device_attr(attr)
            if value is not None:
                return value
        return None

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""

        return f"{self.device.id}_water_heater"

    @property
    def name(self) -> str | None:
        """Return the name of the water heater."""

        return None

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
        value = self._dhw_enabled_value()
        if value is None:
            return None
        if value in (1, True, "1", "true", "True", "on"):
            return WATER_HEATER_ON
        return WATER_HEATER_OFF

    @property
    def operation_list(self) -> list[str] | None:
        """Return the list of available operation modes."""
        return [WATER_HEATER_ON, WATER_HEATER_OFF]

    @property
    def current_temperature(self) -> float:
        """Return the current dhw temperature."""

        value = valid_temperature(self.get_device_attr("Tank_temperature"))
        if value is not None:
            return value
        return valid_temperature(self.get_device_attr("Flow_temperature"))

    def _dhw_target_temperature_value(self) -> Any:
        """Return the current target DHW temperature from known API variants."""
        for attr in DHW_SETPOINT_ATTRS:
            value = valid_temperature(self.get_device_attr(attr))
            if value is not None:
                return value
        return None

    @property
    def target_temperature(self) -> float:
        """Return the targeted dhw temperature. Current_DHW_Setpoint or DHW_setpoint"""

        return self._dhw_target_temperature_value()

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

        await self.send_command("DHW_setpoint", new_temperature)

    async def _async_set_dhw_enabled(self, enabled: bool) -> None:
        """Turn domestic hot water on or off."""
        value = 1 if enabled else 0

        _LOGGER.debug("Setting operation mode to: %s", value)

        await self.send_command("WarmStar_Tank_Loading_Enable", value)

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        await self._async_set_dhw_enabled(operation_mode != WATER_HEATER_OFF)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the water heater on."""
        await self._async_set_dhw_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the water heater off."""
        await self._async_set_dhw_enabled(False)

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        value = self.get_device_attr("Lower_Limitation_of_DHW_Setpoint")
        if value is None:
            return DEFAULT_MIN_TEMPERATURE
        return value

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        value = self.get_device_attr("Upper_Limitation_of_DHW_Setpoint")
        if value is None:
            return DEFAULT_MAX_TEMPERATURE
        return value
