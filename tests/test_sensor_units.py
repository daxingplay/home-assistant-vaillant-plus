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
