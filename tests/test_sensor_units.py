"""Regression tests for the units declared by Vaillant sensor descriptions.

Home Assistant logs (and eventually raises on) a sensor whose device class
requires a unit of measurement but whose ``native_unit_of_measurement`` is
``None``.  These tests keep every description in sync with the unit table of
whichever Home Assistant version the test matrix is running.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Device classes that Home Assistant refuses to accept without a unit.
DEVICE_CLASSES_REQUIRING_UNIT = {
    "TEMPERATURE",
    "PRESSURE",
    "SIGNAL_STRENGTH",
    "POWER",
    "ENERGY",
    "GAS",
    "VOLUME",
    "CURRENT",
    "VOLTAGE",
}


def _descriptions_from_source() -> list[tuple[str, str | None, bool]]:
    """Return (key, device class attribute, has unit) for each description."""
    tree = ast.parse((ROOT / "custom_components/vaillant_plus/sensor.py").read_text())
    found: list[tuple[str, str | None, bool]] = []
    for node in ast.walk(tree):
        if (
            not isinstance(node, ast.Call)
            or not isinstance(node.func, ast.Name)
            or node.func.id != "SensorEntityDescription"
        ):
            continue

        key = None
        device_class = None
        has_unit = False
        for keyword in node.keywords:
            if keyword.arg == "key" and isinstance(keyword.value, ast.Constant):
                key = str(keyword.value.value)
            elif keyword.arg == "device_class" and isinstance(
                keyword.value, ast.Attribute
            ):
                device_class = keyword.value.attr
            elif keyword.arg == "native_unit_of_measurement":
                has_unit = True
        if key is not None:
            found.append((key, device_class, has_unit))
    return found


def test_descriptions_with_device_class_declare_a_unit():
    """Every unit-requiring device class must ship a native unit."""
    missing = [
        key
        for key, device_class, has_unit in _descriptions_from_source()
        if device_class in DEVICE_CLASSES_REQUIRING_UNIT and not has_unit
    ]

    assert not missing, f"sensor descriptions missing a unit: {sorted(missing)}"


def test_native_units_are_valid_for_their_device_class():
    """Validate the descriptions against the running Home Assistant version."""
    from homeassistant.components.sensor import DEVICE_CLASS_UNITS

    from custom_components.vaillant_plus.sensor import SENSOR_DESCRIPTIONS

    invalid = []
    for description in SENSOR_DESCRIPTIONS:
        if description.device_class is None:
            continue
        valid_units = DEVICE_CLASS_UNITS.get(description.device_class)
        if valid_units is None:
            continue
        if description.native_unit_of_measurement not in valid_units:
            invalid.append(
                (
                    description.key,
                    description.device_class,
                    description.native_unit_of_measurement,
                )
            )

    assert not invalid, f"sensor descriptions with an invalid unit: {invalid}"


def test_temperature_sensors_drop_no_data_sentinels():
    """127.5 / 255 mean "no reading" and must never be published.

    Left unfiltered they are recorded into long term statistics as genuine
    temperatures, the kind of poisoned history that #48 had to clean up by
    hand.
    """
    from unittest.mock import MagicMock

    from homeassistant.components.sensor import (
        SensorDeviceClass,
        SensorEntityDescription,
    )
    from homeassistant.const import UnitOfTemperature

    from custom_components.vaillant_plus.sensor import VaillantSensorEntity

    entity = VaillantSensorEntity(
        MagicMock(),
        SensorEntityDescription(
            key="Flow_Temperature_Setpoint",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    )

    for sentinel in (127.5, 255):
        entity.update_from_latest_data({"Flow_Temperature_Setpoint": sentinel})
        assert entity.native_value is None
        assert entity.available is False

    entity.update_from_latest_data({"Flow_Temperature_Setpoint": 45})
    assert entity.native_value == 45


def test_non_temperature_sensors_keep_sentinel_looking_values():
    """255 is a real fault word value, not a sentinel, outside temperatures."""
    from unittest.mock import MagicMock

    from homeassistant.components.sensor import SensorEntityDescription

    from custom_components.vaillant_plus.sensor import VaillantSensorEntity

    entity = VaillantSensorEntity(
        MagicMock(), SensorEntityDescription(key="Gateway_Fault_List_1")
    )
    entity.update_from_latest_data({"Gateway_Fault_List_1": 255})

    assert entity.native_value == 255
