"""Resolving the product family from the device list.

The type must be decided from the device list rather than from whichever
attributes happen to arrive over the websocket, and an unrecognised device
must never lose behaviour an existing installation already had.
"""
from __future__ import annotations

import logging

from vaillant_plus_cn_api import Device

from custom_components.vaillant_plus.device import (
    VaillantDeviceType,
    resolve_device_type,
)


def _device(**overrides) -> Device:
    """Build a Device with the fields the resolver looks at."""
    fields = dict(
        id="1",
        mac="mac",
        product_key="pk",
        product_id=75,
        product_name="威精灵",
        product_verbose_name="威能温控器",
        is_online=True,
        is_manager=True,
        group_id=1,
        sno="sno",
        create_time="2000-01-01 00:00:00",
    )
    fields.update(overrides)
    return Device(**fields)


def test_vsmart_resolves_from_platform_zero():
    """A vSMART reports platform 0."""
    assert resolve_device_type(_device(platform=0)) is VaillantDeviceType.VSMART


def test_gateway_resolves_from_platform_one():
    """A gateway reports platform 1, productId 81."""
    device = _device(
        platform=1,
        product_id=81,
        product_name="智能网关",
        product_verbose_name="WiFiGateway",
    )
    assert resolve_device_type(device) is VaillantDeviceType.GATEWAY


def test_gateway_resolves_from_verbose_name_without_platform():
    """Fallback for a response that omits platform entirely."""
    device = _device(product_id=81, product_verbose_name="WiFiGateway")
    assert device.platform is None
    assert resolve_device_type(device) is VaillantDeviceType.GATEWAY


def test_unknown_family_falls_back_to_vsmart(caplog):
    """An unrecognised device keeps the behaviour every install had before.

    Resolving it as a gateway instead would take the room controls away from
    a working thermostat; resolving it as a vSMART can only fail to add the
    new behaviour, never remove the old one.
    """
    device = _device(platform=7, product_id=999, product_verbose_name="Something")

    with caplog.at_level(logging.WARNING):
        assert resolve_device_type(device) is VaillantDeviceType.VSMART

    # The report has to be actionable without a second round of questions.
    assert "platform=7" in caplog.text
    assert "product_id=999" in caplog.text


def test_missing_fields_do_not_raise():
    """A Device from an older api library has none of these fields."""

    class _OldDevice:
        id = "1"

    assert resolve_device_type(_OldDevice()) is VaillantDeviceType.VSMART
