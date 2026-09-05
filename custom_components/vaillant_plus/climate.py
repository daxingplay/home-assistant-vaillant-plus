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
from .device import VaillantDeviceType, resolve_device_type
from .discovery import MissingAttributeWarning, async_register_discovery
from .entity import VaillantEntity
from .utils import valid_temperature

_LOGGER = logging.getLogger(__name__)

DEFAULT_TEMPERATURE_INCREASE = 0.5

PRESET_SUMMER = "Summer"
PRESET_WINTER = "Winter"

BASE_FEATURES = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.TURN_ON
    | ClimateEntityFeature.TURN_OFF
)
SUPPORTED_HVAC_MODES = [HVACMode.HEAT, HVACMode.OFF]
SUPPORTED_PRESET_MODES = [PRESET_COMFORT]

# A vSMART reports both; a gateway reports only `Heating_Enable`.
HEATING_ENABLE_ATTRS = ("Enabled_Heating", "Heating_Enable")

# The central heating range a gateway is given. It reports no
# `Lower/Upper_Limitation_of_CH_Setpoint` of its own - those are vSMART
# fields - so this is not a fallback but the only bound it ever gets. The
# values match the range the Vaillant app offers.
FLOW_MIN_TEMPERATURE = 30.0
FLOW_MAX_TEMPERATURE = 75.0


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

        device_type = resolve_device_type(client.device)
        entity_class = _ENTITY_CLASSES[device_type]

        _LOGGER.debug("New %s climate found", device_type.value)
        added_entities.append("climate")
        async_add_devices([entity_class(client)])

    async_register_discovery(hass, device_id, client, async_new_climate)

    return True


class VaillantClimate(VaillantEntity, ClimateEntity):
    """Shared behaviour of the Vaillant climate entities.

    Everything here is true of both product families. What differs - which
    setpoint is written, which sensor is read back, whether a comfort preset
    exists - is declared by the subclasses rather than decided at runtime.
    """

    # The main feature of the device: it carries the device name itself.
    _attr_has_entity_name = True

    # The attribute this entity writes when the target temperature changes.
    _setpoint_attr: str
    # The attributes read back as the current temperature, in priority order.
    _temperature_attrs: tuple[str, ...] = ()

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

        return BASE_FEATURES

    @property
    def temperature_unit(self) -> str:
        """Return the measurement unit for all temperature values."""

        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float | None:
        """Return the temperature this entity is controlling towards."""

        for attr in self._temperature_attrs:
            value = valid_temperature(self.get_device_attr(attr))
            if value is not None:
                return value
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the targeted temperature."""

        return valid_temperature(self.get_device_attr(self._setpoint_attr))

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

        current = self.current_temperature
        target = self.target_temperature
        # Either can be unknown - a gateway with no boiler bound reports both
        # as sentinels - and no claim about heating can be made without both.
        if current is not None and target is not None and current < target:
            return HVACAction.HEATING

        return HVACAction.IDLE

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Select new HVAC operation mode."""

        _LOGGER.debug("Setting HVAC mode to: %s", hvac_mode)

        if hvac_mode == HVACMode.OFF:
            await self.send_commands({"Heating_Enable": False})
        elif hvac_mode == HVACMode.HEAT:
            # Both families report Mode_Setting_CH: "Cruising", so both get it.
            await self.send_commands({
                "Heating_Enable": True,
                "Mode_Setting_CH": "Cruising",
            })

    async def async_turn_on(self) -> None:
        """Turn the central heating on."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn the central heating off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_temperature(self, **kwargs) -> None:
        """Update the target temperature."""

        new_temperature = kwargs.get(ATTR_TEMPERATURE)
        if new_temperature is None:
            return

        _LOGGER.debug("Setting target temperature to: %s", new_temperature)

        await self.send_commands({self._setpoint_attr: new_temperature})


class VaillantVSmartClimate(VaillantClimate):
    """The vSMART thermostat, which controls the temperature of a room."""

    _setpoint_attr = "Room_Temperature_Setpoint_Comfort"
    _temperature_attrs = ("Room_Temperature",)

    @property
    def supported_features(self) -> int:
        """Return the flag of supported features for the climate."""

        return BASE_FEATURES | ClimateEntityFeature.PRESET_MODE

    @property
    def preset_modes(self) -> list[str]:
        """Return the list of available HVAC preset modes."""

        return SUPPORTED_PRESET_MODES

    @property
    def preset_mode(self) -> str:
        """Return the currently selected HVAC preset mode."""

        return PRESET_COMFORT

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Select new HVAC preset mode."""

        _LOGGER.debug("Setting HVAC preset mode to: %s", preset_mode)

        return


class VaillantGatewayClimate(VaillantClimate):
    """The familyCONNECT gateway, which controls the boiler flow temperature.

    It has no room setpoint, so it advertises no comfort preset: Home
    Assistant rejects a climate entity that offers PRESET_MODE and then
    returns None for it.
    """

    _setpoint_attr = "Flow_Temperature_Setpoint"
    # A gateway names its room reading `indoor_temperature`, and reports no
    # measured `Flow_temperature` to fall back on.
    _temperature_attrs = ("indoor_temperature",)

    @property
    def min_temp(self) -> float:
        """Return the minimum flow temperature that can be set."""

        return FLOW_MIN_TEMPERATURE

    @property
    def max_temp(self) -> float:
        """Return the maximum flow temperature that can be set."""

        return FLOW_MAX_TEMPERATURE


_ENTITY_CLASSES = {
    VaillantDeviceType.VSMART: VaillantVSmartClimate,
    VaillantDeviceType.GATEWAY: VaillantGatewayClimate,
}
