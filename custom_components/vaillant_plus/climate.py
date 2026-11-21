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

# The attributes carrying the heating on/off state, in the order a vSMART
# reads them. A vSMART reports both, a gateway only `Heating_Enable`, which is
# also the one the entity writes.
HEATING_ENABLE_ATTRS = ("Enabled_Heating", "Heating_Enable")

# `burn_status` while the burner fires for central heating: Vaillant status
# code S.4. Hot water (S.14), pump/fan overrun and anti-cycling are not.
BURN_STATUS_HEATING = 4

# The central heating range a gateway falls back to. A gateway with a boiler
# bound reports the boiler's own `Lower/Upper_Limitation_of_CH_Setpoint`
# (30-60 °C on a turboTEC plus), which takes precedence; one without a boiler
# reports none, or the "no reading" sentinel.
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

    _attr_has_entity_name = True
    # A gateway also has a water heater on the same device, so the climate
    # cannot carry the device name alone: both would show as the same row.
    _attr_translation_key = "central_heating"

    # The attribute this entity writes when the target temperature changes.
    _setpoint_attr: str
    # The attributes read back as the current temperature, in priority order.
    _temperature_attrs: tuple[str, ...] = ()
    # The attributes read back as the heating on/off state, in priority order.
    _heating_enable_attrs: tuple[str, ...] = HEATING_ENABLE_ATTRS

    def _heating_enabled_value(self) -> Any:
        """Return the current heating enable value from known API variants."""
        for attr in self._heating_enable_attrs:
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
            self._mirror_heating_enable(False)
        elif hvac_mode == HVACMode.HEAT:
            # Both families report Mode_Setting_CH: "Cruising", so both get it.
            await self.send_commands({
                "Heating_Enable": True,
                "Mode_Setting_CH": "Cruising",
            })
            self._mirror_heating_enable(True)

    def _mirror_heating_enable(self, enabled: bool) -> None:
        """Apply a written `Heating_Enable` to the other state attributes too.

        A vSMART's state is read from `Enabled_Heating`, which the cloud only
        updates once the device has acted on the change. Until then the mode
        would snap back, so mirror the value locally; the next push from the
        cloud replaces it either way.
        """
        for attr in self._heating_enable_attrs:
            if attr != "Heating_Enable" and self.get_device_attr(attr) is not None:
                self.set_optimistic_value(attr, int(enabled))

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
    # It reports only `Heating_Enable`.
    _heating_enable_attrs = ("Heating_Enable",)
    # eBUS setpoints have half-degree resolution.
    _attr_target_temperature_step = 0.5
    # The setpoint is a flow temperature, so the current temperature must be
    # one too: comparing the room (`indoor_temperature`, ~21 °C) against a
    # 45 °C flow setpoint made the heating always look like it was running.
    # A gateway with no boiler bound reports no `Flow_temperature`; the
    # entity then shows no current temperature rather than the wrong one.
    # The room reading stays available as its own sensor.
    _temperature_attrs = ("Flow_temperature",)

    @property
    def hvac_action(self) -> HVACAction:
        """Return whether the burner is heating, from its status code.

        Comparing the flow temperature with its setpoint says nothing once the
        room is warm: the burner stops, the water cools below the setpoint, and
        the entity would claim to be heating all night. The comparison is only
        a fallback for a gateway that reports no `burn_status`.
        """
        if self._heating_enabled_value() in (0, False):
            return HVACAction.OFF

        try:
            burn_status = int(self.get_device_attr("burn_status"))
        except (TypeError, ValueError):
            return super().hvac_action

        if burn_status == BURN_STATUS_HEATING:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def min_temp(self) -> float:
        """Return the minimum flow temperature that can be set."""

        value = valid_temperature(self.get_device_attr("Lower_Limitation_of_CH_Setpoint"))
        return FLOW_MIN_TEMPERATURE if value is None else value

    @property
    def max_temp(self) -> float:
        """Return the maximum flow temperature that can be set."""

        value = valid_temperature(self.get_device_attr("Upper_Limitation_of_CH_Setpoint"))
        return FLOW_MAX_TEMPERATURE if value is None else value


_ENTITY_CLASSES = {
    VaillantDeviceType.VSMART: VaillantVSmartClimate,
    VaillantDeviceType.GATEWAY: VaillantGatewayClimate,
}
