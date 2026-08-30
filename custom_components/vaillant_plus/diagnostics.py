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
            "product_name": device.product_name,
            "product_verbose_name": device.product_verbose_name,
            "model": device.model,
            "model_alias": device.model_alias,
            "is_online": device.is_online,
        },
        "device_attrs": _redact(dict(client.device_attrs)),
    }

    return diagnostics
