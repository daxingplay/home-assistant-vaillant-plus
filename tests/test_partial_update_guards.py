"""Static checks for partial websocket update handling."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sensor_entities_ignore_partial_updates_without_their_key():
    """Sensor update handlers should keep state when an update omits their key."""
    source = (ROOT / "custom_components/vaillant_plus/sensor.py").read_text()

    assert "if self.entity_description.key not in data:" in source


def test_binary_sensor_entities_ignore_partial_updates_without_their_key():
    """Binary sensor update handlers should keep state on unrelated updates."""
    source = (ROOT / "custom_components/vaillant_plus/binary_sensor.py").read_text()

    assert "if self.entity_description.key not in data:" in source


def test_binary_sensor_bit_fields_accept_integer_values():
    """Vaillant+ may send boiler bit fields as either strings or integers."""
    source = (ROOT / "custom_components/vaillant_plus/binary_sensor.py").read_text()

    assert 'str(value).startswith("1")' in source


def test_climate_accepts_current_heating_enable_attribute():
    """Current China gateway payloads may expose Heating_Enable only."""
    source = (ROOT / "custom_components/vaillant_plus/climate.py").read_text()

    assert 'device_attrs.get("Heating_Enable") is not None' in source
    assert 'return self.get_device_attr("Heating_Enable")' in source


def test_client_merges_partial_device_updates():
    """Websocket updates should not drop attributes omitted from a partial frame."""
    source = (ROOT / "custom_components/vaillant_plus/client.py").read_text()

    assert "self._device_attrs.update(device_attrs)" in source
    assert "self._device_attrs = device_attrs.copy()" in source


def test_climate_can_be_created_from_later_update_events():
    """Climate creation should not depend only on the first connected frame."""
    source = (ROOT / "custom_components/vaillant_plus/climate.py").read_text()

    assert "EVT_DEVICE_UPDATED" in source
    assert "for signal in (EVT_DEVICE_CONNECTED, EVT_DEVICE_UPDATED):" in source


def test_water_heater_accepts_current_dhw_enable_attributes():
    """Current China gateway payloads may omit the legacy Enabled_DHW key."""
    source = (ROOT / "custom_components/vaillant_plus/water_heater.py").read_text()

    assert "_dhw_enabled_value" in source
    assert '"WarmStar_Tank_Loading_Enable"' in source
    assert '"DHW_switch"' in source


def test_water_heater_uses_tank_temperature_when_available():
    """DHW current temperature should prefer the tank temperature sensor."""
    source = (ROOT / "custom_components/vaillant_plus/water_heater.py").read_text()

    assert '"Tank_temperature"' in source
    assert 'return self.get_device_attr("Flow_temperature")' in source


def test_water_heater_prefers_current_dhw_setpoint():
    """DHW target temperature should prefer the current setpoint when available."""
    source = (ROOT / "custom_components/vaillant_plus/water_heater.py").read_text()

    assert (
        'for attr in ("Current_DHW_Setpoint", "DHW_readSetPoint", "DHW_setpoint"):'
        in source
    )
    assert "return self._dhw_target_temperature_value()" in source


def test_sensor_descriptions_include_current_gateway_dhw_read_setpoint():
    """Expose the China gateway's DHW read setpoint field for diagnostics."""
    source = (ROOT / "custom_components/vaillant_plus/sensor.py").read_text()

    assert 'key="DHW_readSetPoint"' in source
