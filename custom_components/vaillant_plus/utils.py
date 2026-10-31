import inspect
import socket
from homeassistant.helpers import aiohttp_client

def get_aiohttp_session(hass):
    if len(inspect.signature(aiohttp_client.async_get_clientsession).parameters) < 3:
        return aiohttp_client.async_get_clientsession(hass)
    else:
        return aiohttp_client.async_get_clientsession(hass, True, socket.AF_INET)


# Neither device omits an attribute it has no reading for: it sends the raw
# eBUS "no data" sentinel instead. 127.5 is 0xFF at the half-degree resolution
# the protocol uses, 255 is 0xFF read as a whole-degree byte.
#
# This is protocol level rather than device specific - a gateway with no
# boiler bound reports every temperature as 127.5 and `indoor_temperature` as
# 255, and a vSMART with no tank sends `Tank_temperature: 127.5` the same way.
#
# Left unfiltered these are rendered as real readings and recorded into long
# term statistics, which is the kind of poisoned history that had to be
# cleaned up by hand in #48.
TEMPERATURE_SENTINELS = (127.5, 255)


def valid_temperature(value):
    """Return ``value`` unless it is a "no reading" sentinel, else ``None``."""
    if value is None or isinstance(value, bool):
        return value
    if value in TEMPERATURE_SENTINELS:
        return None
    return value
