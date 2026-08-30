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
from homeassistant.const import (
    EntityCategory,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import VaillantClient
from .const import CONF_DID, DOMAIN, API_CLIENT
from .discovery import async_register_discovery
from .entity import VaillantEntity

_LOGGER = logging.getLogger(__name__)


SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="Room_Temperature_Setpoint_Comfort",
        name="Room temperature setpoint of comfort mode",
        translation_key="room_temperature_setpoint_comfort",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Room_Temperature_Setpoint_ECO",
        name="Room temperature setpoint of ECO mode",
        translation_key="room_temperature_setpoint_eco",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Outdoor_Temperature",
        name="Outdoor temperature",
        translation_key="outdoor_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Room_Temperature",
        name="Room temperature",
        translation_key="room_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="DHW_setpoint",
        name="Domestic hot water setpoint",
        translation_key="dhw_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="DHW_readSetPoint",
        name="Domestic hot water read setpoint",
        translation_key="dhw_read_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Lower_Limitation_of_CH_Setpoint",
        name="Lower limitation of central heating setpoint",
        translation_key="lower_limitation_of_ch_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Upper_Limitation_of_CH_Setpoint",
        name="Upper limitation of central heating setpoint",
        translation_key="upper_limitation_of_ch_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Lower_Limitation_of_DHW_Setpoint",
        name="Lower limitation of domestic hot water",
        translation_key="lower_limitation_of_dhw_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Upper_Limitation_of_DHW_Setpoint",
        name="Upper limitation of domestic hot water",
        translation_key="upper_limitation_of_dhw_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Current_DHW_Setpoint",
        name="Current domestic hot water setpoint",
        translation_key="current_dhw_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Flow_Temperature_Setpoint",
        name="Flow temperature setpoint",
        translation_key="flow_temperature_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Flow_temperature",
        name="Flow temperature",
        translation_key="flow_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="return_temperature",
        name="Return flow temperature",
        translation_key="return_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Tank_temperature",
        name="Water tank temperature",
        translation_key="tank_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="gas_ch_consumption_today",
        name="Central heating gas consumption today raw",
        translation_key="gas_ch_consumption_today",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="gas_ch_consumption_yesterday",
        name="Central heating gas consumption yesterday raw",
        translation_key="gas_ch_consumption_yesterday",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="gas_ch_consumption_monthly",
        name="Central heating gas consumption monthly raw",
        translation_key="gas_ch_consumption_monthly",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="gas_ch_consumption_yearly",
        name="Central heating gas consumption yearly raw",
        translation_key="gas_ch_consumption_yearly",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="gas_dhw_consumption_today",
        name="Domestic hot water gas consumption today raw",
        translation_key="gas_dhw_consumption_today",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="gas_dhw_consumption_yesterday",
        name="Domestic hot water gas consumption yesterday raw",
        translation_key="gas_dhw_consumption_yesterday",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="gas_dhw_consumption_monthly",
        name="Domestic hot water gas consumption monthly raw",
        translation_key="gas_dhw_consumption_monthly",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="gas_dhw_consumption_yearly",
        name="Domestic hot water gas consumption yearly raw",
        translation_key="gas_dhw_consumption_yearly",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="gas_consumption",
        name="Gas consumption raw",
        translation_key="gas_consumption",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="CH_workTime",
        name="Central heating work time",
        translation_key="ch_work_time",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="CH_startTimes",
        name="Central heating start count",
        translation_key="ch_start_times",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="DHW_workTime",
        name="Domestic hot water work time",
        translation_key="dhw_work_time",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="DHW_startTimes",
        name="Domestic hot water start count",
        translation_key="dhw_start_times",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="CH_power",
        name="Central heating power raw",
        translation_key="ch_power",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="DHW_power",
        name="Domestic hot water power raw",
        translation_key="dhw_power",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Heating_Curve",
        name="Heating curve",
        translation_key="heating_curve",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Mode_Setting_CH",
        name="Central heating mode setting",
        translation_key="mode_setting_ch",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Heating_System_Setting",
        name="Heating system setting",
        translation_key="heating_system_setting",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="water_pressure",
        name="Water pressure",
        translation_key="water_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.BAR,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="burn_status",
        name="Burn status",
        translation_key="burn_status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="pump_status",
        name="Pump status",
        translation_key="pump_status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="fan_status",
        name="Fan status",
        translation_key="fan_status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="fan_speed",
        name="Fan speed",
        translation_key="fan_speed",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="ebus_status",
        name="eBUS status",
        translation_key="ebus_status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="modbus_status",
        name="Modbus status",
        translation_key="modbus_status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="WiFi_RSSI",
        name="Wi-Fi RSSI",
        translation_key="wifi_rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="maintainence_remainTime",
        name="Maintenance remain time",
        translation_key="maintenance_remain_time",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Fault_List_1",
        name="Fault list 1",
        translation_key="fault_list_1",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Fault_List_2",
        name="Fault list 2",
        translation_key="fault_list_2",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Fault_List_3",
        name="Fault list 3",
        translation_key="fault_list_3",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Fault_List_4",
        name="Fault list 4",
        translation_key="fault_list_4",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Fault_List_5",
        name="Fault list 5",
        translation_key="fault_list_5",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Gateway_Fault_List_1",
        name="Gateway fault list 1",
        translation_key="gateway_fault_list_1",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Gateway_Fault_List_2",
        name="Gateway fault list 2",
        translation_key="gateway_fault_list_2",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Gateway_Fault_List_3",
        name="Gateway fault list 3",
        translation_key="gateway_fault_list_3",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Gateway_Fault_List_4",
        name="Gateway fault list 4",
        translation_key="gateway_fault_list_4",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="Gateway_Fault_List_5",
        name="Gateway fault list 5",
        translation_key="gateway_fault_list_5",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Set up Vaillant sensors."""
    device_id = entry.data.get(CONF_DID)
    client: VaillantClient = hass.data[DOMAIN][API_CLIENT][
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

    async_register_discovery(hass, device_id, client, async_new_entities)

    return True


class VaillantSensorEntity(VaillantEntity, SensorEntity):
    """Define a Vaillant sensor entity."""

    # Required for the entity name translations to be used; also makes Home
    # Assistant prefix the friendly name with the device name.
    _attr_has_entity_name = True

    def __init__(
        self,
        client: VaillantClient,
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
        if self.entity_description.key not in data:
            return

        value = data.get(self.entity_description.key)
        self._attr_native_value = value
        self._attr_available = value is not None
