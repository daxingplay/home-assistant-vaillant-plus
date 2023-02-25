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
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import VaillantDeviceApiClient
from .const import CONF_DID, DISPATCHERS, DOMAIN, EVT_DEVICE_CONNECTED, WEBSOCKET_CLIENT
from .entity import VaillantEntity

_LOGGER = logging.getLogger(__name__)

DEFAULT_TEMPERATURE_INCREASE = 0.5

PRESET_SUMMER = "Summer"
PRESET_WINTER = "Winter"

SUPPORTED_FEATURES = (
    ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
)
SUPPORTED_HVAC_MODES = [HVACMode.HEAT, HVACMode.OFF]
SUPPORTED_PRESET_MODES = [PRESET_COMFORT]


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
    def async_new_climate(device_attrs: dict[str, Any]):
        _LOGGER.debug("New climate found")
        if "climate" not in added_entities:
            if device_attrs.get("Enabled_Heating") is not None:
                new_devices = [VaillantClimate(client)]
                async_add_devices(new_devices)
                added_entities.append("climate")
            else:
                _LOGGER.warning(
                    "Missing required attribute to setup Vaillant Climate. skip."
                )
        else:
            _LOGGER.debug("Already added climate device. skip.")

    unsub = async_dispatcher_connect(
        hass, EVT_DEVICE_CONNECTED.format(device_id), async_new_climate
    )

    hass.data[DOMAIN][DISPATCHERS][device_id].append(unsub)

    return True


class VaillantClimate(VaillantEntity, ClimateEntity):
    """Vaillant vSMART Climate."""

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""

        return f"{self.device.id}_climate"

    @property
    def name(self) -> str:
        """Return the name of the climate."""

        return self.device.product_name

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
        if self.get_device_attr("Enabled_Heating"):
            return HVACMode.HEAT

        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """
        Return the currently running HVAC action.
        """

        if not self.get_device_attr("Enabled_Heating"):
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
            await self._client.send_command(
                "Heating_Enable",
                False,
            )
        elif hvac_mode == HVACMode.HEAT:
            await self._client.send_command(
                "Heating_Enable",
                True,
            )

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

        await self._client.send_command(
            "Room_Temperature_Setpoint_Comfort",
            new_temperature,
        )
