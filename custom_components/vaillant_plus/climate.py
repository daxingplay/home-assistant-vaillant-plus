"""The Vaillant Plus climate platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    PRESET_COMFORT,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import VaillantClient
from .const import CONF_DID, DOMAIN, API_CLIENT
from .discovery import MissingAttributeWarning, async_register_discovery
from .entity import VaillantEntity

_LOGGER = logging.getLogger(__name__)

DEFAULT_TEMPERATURE_INCREASE = 0.5

PRESET_SUMMER = "Summer"
PRESET_WINTER = "Winter"

SUPPORTED_FEATURES = (
    ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
)

# `TURN_ON`/`TURN_OFF` only exist from Home Assistant 2024.2 on, where a
# climate entity must advertise them for climate.turn_on / climate.turn_off to
# be accepted; older releases register the services unconditionally.
_TURN_ON_FEATURE = getattr(ClimateEntityFeature, "TURN_ON", None)
_TURN_OFF_FEATURE = getattr(ClimateEntityFeature, "TURN_OFF", None)
if _TURN_ON_FEATURE is not None and _TURN_OFF_FEATURE is not None:
    SUPPORTED_FEATURES |= _TURN_ON_FEATURE | _TURN_OFF_FEATURE
SUPPORTED_HVAC_MODES = [HVACMode.HEAT, HVACMode.OFF]
SUPPORTED_PRESET_MODES = [PRESET_COMFORT]

HEATING_ENABLE_ATTRS = ("Enabled_Heating", "Heating_Enable")


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback
) -> bool:
    """Set up Vaillant devices from a config entry."""

    device_id = entry.data.get(CONF_DID)
    client: VaillantClient = hass.data[DOMAIN][API_CLIENT][
        entry.entry_id
    ]

    added_entities = []
    missing_attribute_warning = MissingAttributeWarning(_LOGGER, "Climate")

    @callback
    def async_new_climate(device_attrs: dict[str, Any]):
        if "climate" in added_entities:
            _LOGGER.debug("Already added climate device. skip.")
            return

        if all(device_attrs.get(attr) is None for attr in HEATING_ENABLE_ATTRS):
            missing_attribute_warning.report(HEATING_ENABLE_ATTRS, device_attrs)
            return

        _LOGGER.debug("New climate found")
        added_entities.append("climate")
        async_add_devices([VaillantClimate(client)])

    async_register_discovery(hass, device_id, client, async_new_climate)

    return True


class VaillantClimate(VaillantEntity, ClimateEntity):
    """Vaillant vSMART Climate."""

    def _heating_enabled_value(self) -> Any:
        """Return the current heating enable value from known API variants."""
        for attr in HEATING_ENABLE_ATTRS:
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

        return f"{self.device.id}_climate"

    @property
    def name(self) -> str | None:
        """Return the name of the climate."""

        return None

    @property
    def supported_features(self) -> int:
        """Return the flag of supported features for the climate."""

        return SUPPORTED_FEATURES

    @property
    def temperature_unit(self) -> str:
        """Return the measurement unit for all temperature values."""

        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float:
        """Return the current room temperature."""

        return self.get_device_attr("Room_Temperature")

    @property
    def target_temperature(self) -> float:
        """Return the targeted room temperature."""

        return self.get_device_attr("Room_Temperature_Setpoint_Comfort")

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available HVAC operation modes."""

        return SUPPORTED_HVAC_MODES

    @property
    def hvac_mode(self) -> HVACMode:
        """
        Return currently selected HVAC operation mode.
        """

        # TODO whether support HVACMode.AUTO
        if self._heating_enabled_value() == 1:
            return HVACMode.HEAT

        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """
        Return the currently running HVAC action.
        """

        if self._heating_enabled_value() in (0, False):
            return HVACAction.OFF

        try:
            if self.get_device_attr("Room_Temperature") < self.get_device_attr(
                "Room_Temperature_Setpoint_Comfort"
            ):
                return HVACAction.HEATING
        except TypeError:
            pass

        return HVACAction.IDLE

    @property
    def preset_modes(self) -> list[str]:
        """Return the list of available HVAC preset modes."""

        return SUPPORTED_PRESET_MODES

    @property
    def preset_mode(self) -> str:
        """Return the currently selected HVAC preset mode."""

        return PRESET_COMFORT

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Select new HVAC operation mode."""

        _LOGGER.debug("Setting HVAC mode to: %s", hvac_mode)

        if hvac_mode == HVACMode.OFF:
            await self._client.control_device({
                "Heating_Enable": False,
            })
            self.set_optimistic_value("Heating_Enable", 0)
        elif hvac_mode == HVACMode.HEAT:
            await self._client.control_device({
                "Heating_Enable": True,
                "Mode_Setting_CH": "Cruising",
            })
            self.set_optimistic_value("Heating_Enable", 1)

    async def async_turn_on(self) -> None:
        """Turn the central heating on."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn the central heating off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Select new HVAC preset mode."""

        _LOGGER.debug("Setting HVAC preset mode to: %s", preset_mode)

        return

    async def async_set_temperature(self, **kwargs) -> None:
        """Update target room temperature value."""

        new_temperature = kwargs.get(ATTR_TEMPERATURE)
        if new_temperature is None:
            return

        _LOGGER.debug("Setting target temperature to: %s", new_temperature)

        await self._client.control_device({
            "Room_Temperature_Setpoint_Comfort": new_temperature,
        })
        self.set_optimistic_value(
            "Room_Temperature_Setpoint_Comfort", new_temperature
        )
