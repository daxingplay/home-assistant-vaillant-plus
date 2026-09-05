"""Tests for config entry diagnostics."""
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vaillant_plus.const import API_CLIENT, DISPATCHERS, DOMAIN
from custom_components.vaillant_plus.diagnostics import (
    REDACTED,
    async_get_config_entry_diagnostics,
)

from .const import MOCK_CONFIG_ENTRY_DATA, MOCK_DID


async def test_diagnostics_redacts_credentials(hass, device_api_client):
    """Diagnostics expose device attributes but never the account token."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID
    )
    entry.add_to_hass(hass)

    device_api_client._device_attrs = {"Heating_Enable": 1, "Room_Temperature": 21}
    hass.data.setdefault(DOMAIN, {API_CLIENT: {}, DISPATCHERS: {}})
    hass.data[DOMAIN][API_CLIENT][entry.entry_id] = device_api_client

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["entry"]["data"]["token"] == REDACTED
    assert result["client"]["device_attrs"] == {
        "Heating_Enable": 1,
        "Room_Temperature": 21,
    }
    assert result["client"]["device"]["model"] == "model_name"
    assert "mac" not in str(result["client"]["device"])


async def test_diagnostics_without_a_running_client(hass):
    """Diagnostics must still work when the entry failed to set up."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {API_CLIENT: {}, DISPATCHERS: {}})

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["client"] is None
    assert result["entry"]["data"]["token"] == REDACTED


async def test_diagnostics_report_the_device_family(hass, device_api_client):
    """The fields that identify the product family must reach a bug report.

    `platform` is what separates a vSMART (0) from a familyCONNECT gateway
    (1), so a report about an unsupported device is only actionable if the
    dump carries it.
    """
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {API_CLIENT: {}, DISPATCHERS: {}})
    hass.data[DOMAIN][API_CLIENT][entry.entry_id] = device_api_client

    device_api_client._device.platform = 1
    device_api_client._device.sub_product_key = "f133295f1c569096"

    result = await async_get_config_entry_diagnostics(hass, entry)
    device = result["client"]["device"]

    assert device["platform"] == 1
    assert device["sub_product_key"] == "f133295f1c569096"
    assert device["product_id"] == "p1"

    # Per-unit identifiers stay out of the dump entirely.
    assert "device_sn" not in device
    assert "serial_number" not in device


async def test_diagnostics_tolerate_an_older_api_library(hass, device_api_client):
    """`platform` only exists from vaillant-plus-cn-api 2.1.0 on.

    The manifest still pins 2.0.1, so diagnostics must not blow up on a
    `Device` that has no such field.
    """
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY_DATA, entry_id=MOCK_DID
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {API_CLIENT: {}, DISPATCHERS: {}})
    hass.data[DOMAIN][API_CLIENT][entry.entry_id] = device_api_client

    # A stand-in rather than the real dataclass, so the test states which
    # fields a 2.0.1 Device has instead of depending on which version happens
    # to be installed in the test environment.
    class _OldDevice:
        id = "1"
        product_key = "pk"
        product_id = "p1"
        product_name = "pn"
        product_verbose_name = "pvn"
        model = "model_name"
        model_alias = "weijingling"
        is_online = True

    device_api_client._device = _OldDevice()

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["client"]["device"]["platform"] is None
    assert result["client"]["device"]["sub_product_key"] is None
