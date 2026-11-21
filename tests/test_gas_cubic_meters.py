"""Reporting gas consumption in m³ through the options flow, see #67."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
import voluptuous as vol

from custom_components.vaillant_plus import async_setup, sensor
from custom_components.vaillant_plus.const import (
    API_CLIENT,
    CONF_GAS_CALORIFIC_VALUE,
    CONF_GAS_UNIT,
    DOMAIN,
)

from .const import MOCK_CONFIG_ENTRY_DATA, MOCK_DID

# 97,863 kJ in the #67 sample.
SAMPLE = {"gas_ch_consumption_today": "8023bf47"}
SAMPLE_KWH = 97_863 / 3600


async def _start_options_flow(hass: HomeAssistant, options: dict | None = None):
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, options=options or {}
    )
    entry.add_to_hass(hass)
    with patch("custom_components.vaillant_plus.async_setup_entry", return_value=True):
        result = await hass.config_entries.options.async_init(entry.entry_id)
    return entry, result


def _defaults(result) -> dict:
    return {
        str(marker): marker.default()
        for marker in result["data_schema"].schema
    }


async def test_options_default_to_kwh(hass: HomeAssistant):
    _, result = await _start_options_flow(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    assert _defaults(result) == {CONF_GAS_UNIT: "kwh", CONF_GAS_CALORIFIC_VALUE: 10.0}


async def test_options_show_the_saved_values(hass: HomeAssistant):
    saved = {CONF_GAS_UNIT: "m3", CONF_GAS_CALORIFIC_VALUE: 9.5}
    _, result = await _start_options_flow(hass, saved)

    assert _defaults(result) == saved


async def test_options_are_saved(hass: HomeAssistant):
    entry, result = await _start_options_flow(hass)

    with patch("custom_components.vaillant_plus.async_setup_entry", return_value=True):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_GAS_UNIT: "m3", CONF_GAS_CALORIFIC_VALUE: "9.5"},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_GAS_UNIT: "m3", CONF_GAS_CALORIFIC_VALUE: 9.5}


@pytest.mark.parametrize("value", [0, 0.5, 51])
async def test_implausible_calorific_values_are_rejected(hass: HomeAssistant, value):
    _, result = await _start_options_flow(hass)

    with pytest.raises(vol.Invalid):
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_GAS_UNIT: "m3", CONF_GAS_CALORIFIC_VALUE: value},
        )


async def _sensors(hass: HomeAssistant, options: dict) -> dict:
    """Set up the sensor platform for `options` and discover `SAMPLE`."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, options=options
    )
    client = MagicMock(is_connected=True, device_attrs=dict(SAMPLE))
    hass.data.setdefault(DOMAIN, {})[API_CLIENT] = {entry.entry_id: client}

    created = []
    with patch.object(sensor, "async_register_discovery") as register:
        await sensor.async_setup_entry(hass, entry, created.extend)
        register.call_args.args[3](SAMPLE)

    for entity in created:
        entity.update_from_latest_data(SAMPLE)
    return {entity.entity_description.key: entity for entity in created}


async def test_sensors_report_kwh_by_default(hass: HomeAssistant):
    entities = await _sensors(hass, {})
    decoded = entities["gas_ch_consumption_today"]

    assert decoded.entity_description.device_class is SensorDeviceClass.ENERGY
    assert decoded.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
    assert decoded.native_value == pytest.approx(SAMPLE_KWH)


async def test_sensors_report_m3_when_chosen(hass: HomeAssistant):
    entities = await _sensors(
        hass, {CONF_GAS_UNIT: "m3", CONF_GAS_CALORIFIC_VALUE: 9.5}
    )
    decoded = entities["gas_ch_consumption_today"]
    raw = entities["gas_ch_consumption_today_raw"]

    assert decoded.entity_description.device_class is SensorDeviceClass.GAS
    assert decoded.native_unit_of_measurement == UnitOfVolume.CUBIC_METERS
    assert decoded.state_class is SensorStateClass.TOTAL_INCREASING
    assert decoded.native_value == pytest.approx(SAMPLE_KWH / 9.5)
    # The unique id does not change with the unit, so history stays attached.
    assert decoded.unique_id.endswith("_gas_ch_consumption_today")

    assert raw.native_value == "8023bf47"
    assert raw.native_unit_of_measurement is None


async def test_m3_descriptions_are_valid_for_home_assistant():
    from homeassistant.components.sensor import DEVICE_CLASS_UNITS

    for key in sensor.GAS_CONSUMPTION_KEYS:
        description = next(d for d in sensor.SENSOR_DESCRIPTIONS if d.key == key)
        converted = sensor._in_cubic_meters(description)
        assert converted.native_unit_of_measurement in DEVICE_CLASS_UNITS[
            converted.device_class
        ]
        assert converted.state_class == description.state_class


async def test_entry_reloads_on_options_change_only(
    hass: HomeAssistant, bypass_login, bypass_get_device
):
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID
    )
    entry.add_to_hass(hass)

    with patch("vaillant_plus_cn_api.VaillantWebsocketClient.connect"):
        assert await async_setup(hass, {})
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        with patch.object(hass.config_entries, "async_reload") as reload:
            # A token refresh only rewrites `data`.
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, "token": entry.data["token"] + "x"}
            )
            await hass.async_block_till_done()
            assert not reload.called

            hass.config_entries.async_update_entry(
                entry, options={CONF_GAS_UNIT: "m3", CONF_GAS_CALORIFIC_VALUE: 10.0}
            )
            await hass.async_block_till_done()
            reload.assert_called_once_with(entry.entry_id)

        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
