"""Static tests for enhanced Vaillant sensor descriptions.

These tests intentionally avoid importing Home Assistant so they can run in a
plain Python environment while still protecting the HACS package surface.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sensor_description_keys() -> set[str]:
    tree = ast.parse(
        (ROOT / "custom_components/vaillant_plus/sensor.py").read_text()
    )
    keys: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "SensorEntityDescription":
            continue
        for keyword in node.keywords:
            if keyword.arg == "key" and isinstance(keyword.value, ast.Constant):
                keys.add(str(keyword.value.value))
    return keys


def test_enhanced_diagnostic_sensor_keys_are_exposed():
    """Enhanced integration exposes raw cloud attrs needed for gas review."""
    expected = {
        "gas_ch_consumption_today",
        "gas_ch_consumption_yesterday",
        "gas_ch_consumption_monthly",
        "gas_ch_consumption_yearly",
        "gas_dhw_consumption_today",
        "gas_dhw_consumption_yesterday",
        "gas_dhw_consumption_monthly",
        "gas_dhw_consumption_yearly",
        "gas_consumption",
        "CH_workTime",
        "CH_startTimes",
        "DHW_workTime",
        "DHW_startTimes",
        "CH_power",
        "DHW_power",
        "Heating_Curve",
        "Heating_System_Setting",
        "water_pressure",
        "burn_status",
        "pump_status",
        "fan_status",
        "fan_speed",
        "ebus_status",
        "modbus_status",
        "WiFi_RSSI",
        "maintainence_remainTime",
        "Fault_List_1",
        "Fault_List_2",
        "Fault_List_3",
        "Fault_List_4",
        "Fault_List_5",
        "Gateway_Fault_List_1",
        "Gateway_Fault_List_2",
        "Gateway_Fault_List_3",
        "Gateway_Fault_List_4",
        "Gateway_Fault_List_5",
    }

    assert expected <= _sensor_description_keys()


def _disabled_by_default_keys() -> set[str]:
    tree = ast.parse(
        (ROOT / "custom_components/vaillant_plus/sensor.py").read_text()
    )
    keys: set[str] = set()
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "SensorEntityDescription"
        ):
            continue
        values = {
            keyword.arg: keyword.value.value
            for keyword in node.keywords
            if isinstance(keyword.value, ast.Constant)
        }
        if values.get("entity_registry_enabled_default") is False:
            keys.add(str(values["key"]))
    return keys


def test_undecoded_gas_sensors_are_disabled_by_default():
    """The raw gas strings look broken, so they must be opted into, see #67."""
    gas_keys = {key for key in _sensor_description_keys() if key.startswith("gas_")}

    assert gas_keys
    assert gas_keys <= _disabled_by_default_keys()
