"""Config flow for Vaillant Plus integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from vaillant_plus_cn_api import Token, Device

from .client import VaillantApiHub
from .const import (
    CONF_DID,
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_PRODUCT_NAME,
    CONF_TOKEN,
    CONF_UID,
    CONF_USERNAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        # vol.Required("host"): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class VaillantPlusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vaillant Plus."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._cloud_token: Token | None = None
        self._cloud_device_info: Device | None = None
        self._cloud_devices: dict[str, Device] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        hub = VaillantApiHub(self.hass)

        try:
            user_info = await hub.login(user_input["username"], user_input["password"])
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "invalid_auth"
        else:
            self._cloud_token = user_info
            device_list = await hub.get_device_list(user_info.token)
            if len(device_list) == 0:
                errors["base"] = "no_devices"
            else:
                for device_info in device_list:
                    product_name = device_info.product_name
                    # mac_addr = device_info["mac"]
                    device_id = device_info.id
                    device_name = f"{product_name}_{device_id}"
                    self._cloud_devices[device_name] = device_info
                return await self.async_step_select()

        # try:
        #     info = await validate_input(self.hass, user_input)
        # except CannotConnect:
        #     errors["base"] = "cannot_connect"
        # except InvalidAuth:
        #     errors["base"] = "invalid_auth"
        # except Exception:  # pylint: disable=broad-except
        #     _LOGGER.exception("Unexpected exception")
        #     errors["base"] = "unknown"
        # else:
        #     return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle multiple cloud devices found."""
        errors: dict[str, str] = {}
        if user_input is not None:
            cloud_device = self._cloud_devices[user_input["select_device"]]
            self._cloud_device_info = cloud_device

            unique_id = cloud_device.id
            existing_entry = await self.async_set_unique_id(
                unique_id, raise_on_progress=False
            )

            if existing_entry:
                data = existing_entry.data.copy()
                data[CONF_DID] = unique_id
                data[CONF_TOKEN] = self._cloud_token.serialize()

                if self.hass.config_entries.async_update_entry(
                    existing_entry, data=data
                ):
                    await self.hass.config_entries.async_reload(existing_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

            return self.async_create_entry(
                title=cloud_device.product_name,
                data={
                    CONF_DID: unique_id,
                    CONF_TOKEN: self._cloud_token.serialize(),
                },
            )

        select_schema = vol.Schema(
            {vol.Required("select_device"): vol.In(list(self._cloud_devices))}
        )

        return self.async_show_form(
            step_id="select", data_schema=select_schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
