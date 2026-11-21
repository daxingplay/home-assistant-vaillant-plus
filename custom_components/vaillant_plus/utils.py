import inspect
import math
import socket
import struct
from typing import Any

from homeassistant.helpers import aiohttp_client

KILOJOULES_PER_KILOWATT_HOUR = 3600


def get_aiohttp_session(hass):
    if len(inspect.signature(aiohttp_client.async_get_clientsession).parameters) < 3:
        return aiohttp_client.async_get_clientsession(hass)
    else:
        return aiohttp_client.async_get_clientsession(hass, True, socket.AF_INET)


def decode_gas_consumption(value: Any) -> float | None:
    """Decode a gas consumption attribute into kWh.

    The cloud sends 8 hex digits holding a little-endian float32 in kJ. The
    unit is inferred from sample data, not documented (#67).
    """
    try:
        (kilojoules,) = struct.unpack("<f", bytes.fromhex(str(value)))
    except (TypeError, ValueError, struct.error):
        return None
    if not math.isfinite(kilojoules) or kilojoules < 0:
        return None
    return kilojoules / KILOJOULES_PER_KILOWATT_HOUR
