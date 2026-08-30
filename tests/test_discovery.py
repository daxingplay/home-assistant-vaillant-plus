"""Tests for the shared entity discovery helper."""
from unittest.mock import MagicMock

from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.vaillant_plus.const import (
    DISPATCHERS,
    DOMAIN,
    EVT_DEVICE_CONNECTED,
    EVT_DEVICE_UPDATED,
)
from custom_components.vaillant_plus.discovery import (
    MissingAttributeWarning,
    async_register_discovery,
)


async def test_discovery_uses_accumulated_attributes(hass, device_api_client):
    """A partial update must be evaluated against every known attribute."""
    hass.data.setdefault(DOMAIN, {DISPATCHERS: {}})[DISPATCHERS]["1"] = []

    seen = []
    async_register_discovery(hass, "1", device_api_client, seen.append)

    device_api_client._device_attrs = {"Heating_Enable": 1}
    async_dispatcher_send(hass, EVT_DEVICE_CONNECTED.format("1"), {"Heating_Enable": 1})
    await hass.async_block_till_done()

    # A later frame carries only the attribute that changed, but discovery must
    # still see the attributes received earlier.
    device_api_client._device_attrs["Room_Temperature"] = 21
    async_dispatcher_send(hass, EVT_DEVICE_UPDATED.format("1"), {"Room_Temperature": 21})
    await hass.async_block_till_done()

    assert seen == [
        {"Heating_Enable": 1},
        {"Heating_Enable": 1, "Room_Temperature": 21},
    ]


async def test_discovery_skips_empty_attributes(hass, device_api_client):
    """Nothing to discover before the first payload arrives."""
    hass.data.setdefault(DOMAIN, {DISPATCHERS: {}})[DISPATCHERS]["1"] = []

    seen = []
    async_register_discovery(hass, "1", device_api_client, seen.append)

    async_dispatcher_send(hass, EVT_DEVICE_UPDATED.format("1"), {})
    await hass.async_block_till_done()

    assert seen == []


def test_missing_attribute_warning_is_logged_once():
    """Partial updates must not spam the log with setup warnings."""
    logger = MagicMock()
    warning = MissingAttributeWarning(logger, "Climate")

    warning.report(("Heating_Enable",), {"Room_Temperature": 21})
    warning.report(("Heating_Enable",), {"Room_Temperature": 21})

    assert logger.warning.call_count == 1
    assert logger.debug.call_count == 1
