"""Decoding of the hex gas consumption attributes, see #67."""

from __future__ import annotations

import pytest

from custom_components.vaillant_plus.utils import decode_gas_consumption


@pytest.mark.parametrize(
    ("raw", "kilojoules"),
    [
        # Samples from the diagnostics in #67.
        ("8023bf47", 97_863),
        ("8007d847", 110_607),
        ("50fccd49", 1_687_434),
        ("b4005d4b", 14_483_636),
        ("00609e44", 1_267),
        ("00a67847", 63_654),
        ("00000000", 0),
    ],
)
def test_decodes_samples_to_kwh(raw, kilojoules):
    assert decode_gas_consumption(raw) == pytest.approx(kilojoules / 3600)


@pytest.mark.parametrize(
    "raw",
    [None, "", "zz", "8023bf", "8023bf4700", "0000c0ff", "0000807f", "000080bf", 5],
)
def test_rejects_values_that_are_not_a_consumption(raw):
    assert decode_gas_consumption(raw) is None


def test_gas_sensors_feed_the_energy_dashboard():
    from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
    from homeassistant.const import UnitOfEnergy

    from custom_components.vaillant_plus.sensor import (
        GAS_CONSUMPTION_KEYS,
        SENSOR_DESCRIPTIONS,
    )

    gas = [d for d in SENSOR_DESCRIPTIONS if d.key in GAS_CONSUMPTION_KEYS]
    assert len(gas) == 9

    for description in gas:
        assert description.device_class is SensorDeviceClass.ENERGY
        assert description.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
        assert description.entity_registry_enabled_default is True
        expected = (
            None
            if description.key.endswith("_yesterday")
            else SensorStateClass.TOTAL_INCREASING
        )
        assert description.state_class == expected, description.key


async def test_entity_reports_decoded_kwh(hass):
    from unittest.mock import MagicMock

    from custom_components.vaillant_plus.sensor import (
        SENSOR_DESCRIPTIONS,
        VaillantSensorEntity,
    )

    description = next(
        d for d in SENSOR_DESCRIPTIONS if d.key == "gas_ch_consumption_today"
    )
    client = MagicMock(is_connected=True)
    client.device_attrs = {"gas_ch_consumption_today": "8023bf47"}
    entity = VaillantSensorEntity(client, description)

    entity.update_from_latest_data({"gas_ch_consumption_today": "8023bf47"})

    assert entity.available
    assert entity.native_value == pytest.approx(97_863 / 3600)


def test_each_gas_attribute_has_a_hidden_raw_sensor():
    from homeassistant.const import EntityCategory

    from custom_components.vaillant_plus.sensor import (
        GAS_CONSUMPTION_KEYS,
        SENSOR_DESCRIPTIONS,
    )

    raw = {d.key: d for d in SENSOR_DESCRIPTIONS if d.key.endswith("_raw")}
    assert set(raw) == {f"{key}_raw" for key in GAS_CONSUMPTION_KEYS}

    for description in raw.values():
        assert description.entity_registry_visible_default is False
        assert description.entity_registry_enabled_default is True
        assert description.entity_category is EntityCategory.DIAGNOSTIC
        assert description.device_class is None
        assert description.native_unit_of_measurement is None


async def test_raw_entity_reports_the_value_as_received(hass):
    from unittest.mock import MagicMock

    from custom_components.vaillant_plus.sensor import (
        SENSOR_DESCRIPTIONS,
        VaillantSensorEntity,
    )

    description = next(
        d for d in SENSOR_DESCRIPTIONS if d.key == "gas_ch_consumption_today_raw"
    )
    client = MagicMock(is_connected=True)
    client.device_attrs = {"gas_ch_consumption_today": "8023bf47"}
    entity = VaillantSensorEntity(client, description)

    entity.update_from_latest_data({"gas_ch_consumption_today": "8023bf47"})

    assert entity.available
    assert entity.native_value == "8023bf47"
    assert entity.unique_id.endswith("_gas_ch_consumption_today_raw")


async def test_both_sensors_are_created_from_one_attribute(hass):
    from unittest.mock import MagicMock, patch

    from custom_components.vaillant_plus import sensor

    created = []
    entry = MagicMock(entry_id="entry", data={"did": "device"})
    hass.data.setdefault(sensor.DOMAIN, {})[sensor.API_CLIENT] = {
        "entry": MagicMock()
    }

    with patch.object(sensor, "async_register_discovery") as register:
        await sensor.async_setup_entry(hass, entry, created.extend)
        discover = register.call_args.args[3]
        discover({"gas_ch_consumption_today": "8023bf47"})

    assert sorted(e.entity_description.key for e in created) == [
        "gas_ch_consumption_today",
        "gas_ch_consumption_today_raw",
    ]
