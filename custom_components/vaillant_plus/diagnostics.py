"""Diagnostics support for the Vaillant Plus integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .client import VaillantClient
from .const import API_CLIENT, CONF_DID, DOMAIN

REDACTED = "**REDACTED**"

# Config entry keys and device fields that identify the account or the
# hardware. Device attributes themselves are kept as-is: they are what makes a
# diagnostics download useful when triaging an unsupported gateway.
# `device_sn` is deliberately not listed: like `mac` and `serial_number` it
# identifies the unit rather than the product, so it is left out of the device
# dump entirely rather than included and redacted.
TO_REDACT = {
    "access_token",
    "did",
    "mac",
    "password",
    "serial_number",
    "sno",
    "token",
    "uid",
    "username",
}


def _redact(data: Any) -> Any:
    """Return a copy of ``data`` with sensitive values replaced."""
    if isinstance(data, dict):
        return {
            key: REDACTED if key in TO_REDACT else _redact(value)
            for key, value in data.items()
        }
    if isinstance(data, (list, tuple)):
        return [_redact(item) for item in data]
    return data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    client: VaillantClient | None = hass.data.get(DOMAIN, {}).get(API_CLIENT, {}).get(
        entry.entry_id
    )

    diagnostics: dict[str, Any] = {
        "entry": {
            "data": _redact(dict(entry.data)),
            "options": _redact(dict(entry.options)),
        },
        "device_id_set": entry.data.get(CONF_DID) is not None,
    }

    if client is None:
        diagnostics["client"] = None
        return diagnostics

    device = client.device
    diagnostics["client"] = {
        "is_connected": client.is_connected,
        "device": None
        if device is None
        else {
            "product_key": device.product_key,
            "product_id": device.product_id,
            "product_name": device.product_name,
            "product_verbose_name": device.product_verbose_name,
            # The product family the cloud puts this device in: 0 for a vSMART
            # thermostat, 1 for a familyCONNECT gateway. This is what tells the
            # two apart without inferring it from which attributes happen to
            # arrive, so it is the first thing to look at in a report about an
            # unsupported device. `getattr` because it only exists from
            # vaillant-plus-cn-api 2.1.0 on.
            "platform": getattr(device, "platform", None),
            # Set when the device fronts other appliances, as a gateway does
            # for the boiler behind it.
            "sub_product_key": getattr(device, "sub_product_key", None),
            "model": device.model,
            "model_alias": device.model_alias,
            "is_online": device.is_online,
        },
        "device_attrs": _redact(dict(client.device_attrs)),
    }

    return diagnostics
