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
    from custom_components.vaillant_plus.climate import HEATING_ENABLE_ATTRS

    assert HEATING_ENABLE_ATTRS == ("Enabled_Heating", "Heating_Enable")


def test_client_merges_partial_device_updates():
    """Websocket updates should not drop attributes omitted from a partial frame."""
    source = (ROOT / "custom_components/vaillant_plus/client.py").read_text()

    assert "self._device_attrs.update(device_attrs)" in source
    assert "self._device_attrs = device_attrs.copy()" in source


def test_all_platforms_discover_entities_from_accumulated_attributes():
    """Every platform must keep discovering on later, partial update frames."""
    discovery = (ROOT / "custom_components/vaillant_plus/discovery.py").read_text()

    assert "for signal in (EVT_DEVICE_CONNECTED, EVT_DEVICE_UPDATED):" in discovery
    assert "device_attrs = client.device_attrs" in discovery

    for platform in ("climate", "water_heater", "sensor", "binary_sensor"):
        source = (
            ROOT / f"custom_components/vaillant_plus/{platform}.py"
        ).read_text()
        assert "async_register_discovery(hass, device_id, client," in source


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
    assert 'valid_temperature(self.get_device_attr("Flow_temperature"))' in source


def test_water_heater_prefers_current_dhw_setpoint():
    """DHW target temperature should prefer the current setpoint when available."""
    source = (ROOT / "custom_components/vaillant_plus/water_heater.py").read_text()

    from custom_components.vaillant_plus.water_heater import DHW_SETPOINT_ATTRS

    assert DHW_SETPOINT_ATTRS == (
        "Current_DHW_Setpoint",
        "DHW_readSetPoint",
        "DHW_setpoint",
    )
    assert "return self._dhw_target_temperature_value()" in source


def test_sensor_descriptions_include_current_gateway_dhw_read_setpoint():
    """Expose the China gateway's DHW read setpoint field for diagnostics."""
    source = (ROOT / "custom_components/vaillant_plus/sensor.py").read_text()

    assert 'key="DHW_readSetPoint"' in source
