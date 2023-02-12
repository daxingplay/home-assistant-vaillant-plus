"""Test vaillant-plus binary_sensor."""
from unittest.mock import call, patch

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers.entity import EntityCategory
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vaillant_plus.binary_sensor import (
    VaillantBinarySensorEntity,
    VaillantBinarySensorDescription,
)
from custom_components.vaillant_plus.const import DOMAIN

from .const import MOCK_CONFIG_ENTRY_DATA, MOCK_DID


async def test_binary_sensor_heating_enabled(device_api_client):
    """Test binary sensor."""
    binary_sensor = VaillantBinarySensorEntity(
        device_api_client,
        VaillantBinarySensorDescription(
            key="Heating_Enable",
            name="Heating",
            device_class=BinarySensorDeviceClass.RUNNING,
            entity_category=EntityCategory.DIAGNOSTIC,
            on_state=True,
        ),
    )

    assert binary_sensor.unique_id == "mac2_Heating_Enable"

    binary_sensor.update_from_latest_data({"Heating_Enable": True})
    assert binary_sensor.is_on is True

    binary_sensor.update_from_latest_data({"Heating_Enable": False})
    assert binary_sensor.is_on is False


async def test_binary_sensor_rf_status(device_api_client):
    """Test binary sensor."""
    binary_sensor = VaillantBinarySensorEntity(
        device_api_client,
        VaillantBinarySensorDescription(
            key="RF_Status",
            name="EBus Status",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
            entity_category=EntityCategory.DIAGNOSTIC,
            on_state=True,
        ),
    )

    assert binary_sensor.unique_id == "mac2_RF_Status"

    binary_sensor.update_from_latest_data({"RF_Status": 3})
    assert binary_sensor.is_on is True

    binary_sensor.update_from_latest_data({"RF_Status": 4})
    assert binary_sensor.is_on is False

    binary_sensor.update_from_latest_data({"RF_Status": 0})
    assert binary_sensor.is_on is False


async def test_binary_sensor_boiler_info3_bit0(device_api_client):
    """Test binary sensor."""
    binary_sensor = VaillantBinarySensorEntity(
        device_api_client,
        VaillantBinarySensorDescription(
            key="Boiler_info3_bit0",
            name="Boiler heating demand",
            device_class=BinarySensorDeviceClass.RUNNING,
            entity_category=EntityCategory.DIAGNOSTIC,
            on_state=True,
        ),
    )

    assert binary_sensor.unique_id == "mac2_Boiler_info3_bit0"

    binary_sensor.update_from_latest_data({"Boiler_info3_bit0": [1]})
    assert binary_sensor.is_on is True

    binary_sensor.update_from_latest_data({"Boiler_info3_bit0": [2]})
    assert binary_sensor.is_on is False

    binary_sensor.update_from_latest_data({"Boiler_info3_bit0": [0, 2, 3]})
    assert binary_sensor.is_on is False


async def test_binary_sensor_boiler_info5_bit4(device_api_client):
    """Test binary sensor."""
    binary_sensor = VaillantBinarySensorEntity(
        device_api_client,
        VaillantBinarySensorDescription(
            key="Boiler_info5_bit4",
            name="Boiler need refill water",
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_category=EntityCategory.DIAGNOSTIC,
            on_state=True,
        ),
    )

    assert binary_sensor.unique_id == "mac2_Boiler_info5_bit4"

    binary_sensor.update_from_latest_data({"Boiler_info5_bit4": [1]})
    assert binary_sensor.is_on is True

    binary_sensor.update_from_latest_data({"Boiler_info5_bit4": [2]})
    assert binary_sensor.is_on is False

    binary_sensor.update_from_latest_data({"Boiler_info5_bit4": [0, 2, 3]})
    assert binary_sensor.is_on is False
