import inspect
import socket
from homeassistant.helpers import aiohttp_client

def get_aiohttp_session(hass):
    if len(inspect.signature(aiohttp_client.async_get_clientsession).parameters) < 3:
        return aiohttp_client.async_get_clientsession(hass)
    else:
        return aiohttp_client.async_get_clientsession(hass, True, socket.AF_INET)
