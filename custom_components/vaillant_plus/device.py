"""Which product family a bound device belongs to.

The cloud sells two things this integration talks to, and they are different
shapes rather than different attribute sets:

* the **vSMART** (威精灵) room thermostat, which controls a room temperature;
* the **familyCONNECT WiFi gateway** (智能网关), which sits at the boiler and
  controls the central heating flow temperature instead.

The type is resolved once, from the device list, rather than inferred from
which attributes happen to arrive in a websocket frame. Attribute sniffing
reads as a heuristic buried in the entity code and silently changes behaviour
if the cloud starts or stops reporting an attribute; the device list answers
the question directly.
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Any

_LOGGER = logging.getLogger(__name__)

# `verboseName` for a gateway. Only used when the cloud omits `platform`,
# which no observed response does - see `resolve_device_type`.
_GATEWAY_VERBOSE_NAME = "WiFiGateway"

# Observed values of the `platform` field, which is a family flag rather than
# a per-SKU identifier: a vSMART (productId 75) reports 0, a gateway
# (productId 81) reports 1.
_PLATFORM_VSMART = 0
_PLATFORM_GATEWAY = 1


class VaillantDeviceType(Enum):
    """The product family of a bound device."""

    VSMART = "vsmart"
    GATEWAY = "gateway"


def resolve_device_type(device: Any) -> VaillantDeviceType:
    """Return the product family of ``device``.

    Resolves to GATEWAY only on positive evidence. Anything unrecognised is
    treated as a vSMART, which is what every installation did before gateways
    were supported at all, so an unknown device can never change the
    behaviour of a working setup - it can only fail to gain the new one.

    An unrecognised device is logged with its full identity, so the first
    report of a misresolved device is a one line fix rather than another wait
    for hardware.
    """
    platform = getattr(device, "platform", None)

    if platform == _PLATFORM_GATEWAY:
        return VaillantDeviceType.GATEWAY

    if platform == _PLATFORM_VSMART:
        return VaillantDeviceType.VSMART

    # `platform` is the reliable signal and every observed response carries
    # it. Fall back to the verbose name only if a response ever omits it.
    if getattr(device, "product_verbose_name", None) == _GATEWAY_VERBOSE_NAME:
        _LOGGER.debug(
            "Device %s has no platform field; resolved as a gateway by its"
            " verbose name",
            getattr(device, "id", None),
        )
        return VaillantDeviceType.GATEWAY

    _LOGGER.warning(
        "Unrecognised Vaillant product family, treating it as a vSMART"
        " thermostat. If this device is a gateway and its central heating"
        " controls are missing, please report these values:"
        " platform=%r product_id=%r product_key=%r verbose_name=%r"
        " product_name=%r",
        platform,
        getattr(device, "product_id", None),
        getattr(device, "product_key", None),
        getattr(device, "product_verbose_name", None),
        getattr(device, "product_name", None),
    )
    return VaillantDeviceType.VSMART
