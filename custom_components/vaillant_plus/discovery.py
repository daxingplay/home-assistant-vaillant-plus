"""Shared entity discovery helpers for the Vaillant Plus platforms.

The gateway only sends the full attribute set once, when the websocket
subscription is established; every later frame is a partial update carrying
just the attributes that changed.  Platforms must therefore evaluate their
discovery conditions against the attributes accumulated by the client instead
of the payload of a single event, and they must keep re-evaluating them as new
frames arrive.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .client import VaillantClient
from .const import (
    DISPATCHERS,
    DOMAIN,
    EVT_DEVICE_CONNECTED,
    EVT_DEVICE_UPDATED,
)

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_discovery(
    hass: HomeAssistant,
    device_id: str,
    client: VaillantClient,
    discover: Callable[[dict[str, Any]], None],
) -> None:
    """Run ``discover`` with all known device attributes on every update."""

    @callback
    def _handle_event(_: dict[str, Any]) -> None:
        device_attrs = client.device_attrs
        if not device_attrs:
            return
        discover(dict(device_attrs))

    for signal in (EVT_DEVICE_CONNECTED, EVT_DEVICE_UPDATED):
        unsub = async_dispatcher_connect(
            hass, signal.format(device_id), _handle_event
        )
        hass.data[DOMAIN][DISPATCHERS][device_id].append(unsub)


class MissingAttributeWarning:
    """Log a "cannot set up this platform yet" warning only once."""

    def __init__(self, logger: logging.Logger, platform: str) -> None:
        self._logger = logger
        self._platform = platform
        self._reported = False

    def report(self, expected: tuple[str, ...], device_attrs: dict[str, Any]) -> None:
        """Warn about the missing attributes, at most once per platform."""
        if self._reported:
            self._logger.debug(
                "Still missing required attribute to setup Vaillant %s. skip.",
                self._platform,
            )
            return

        self._reported = True
        self._logger.warning(
            (
                "Missing required attribute to setup Vaillant %s, expected one of"
                " %s. Known device attributes: %s. Please report this together with"
                " the integration diagnostics if your device supports this feature."
            ),
            self._platform,
            list(expected),
            sorted(device_attrs),
        )
