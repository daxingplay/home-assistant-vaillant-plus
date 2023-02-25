"""Test vaillant-plus config flow."""
from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vaillant_plus.const import CONF_DID, CONF_TOKEN, DOMAIN

from .const import MOCK_INPUT


# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent setup."""
    with patch(
        "custom_components.vaillant_plus.async_setup",
        return_value=True,
    ), patch(
        "custom_components.vaillant_plus.async_setup_entry",
        return_value=True,
    ):
        yield


# Here we simiulate a successful config flow from the backend.
# Note that we use the `bypass_login` fixture here because
# we want the config flow validation to succeed during the test.
async def test_successful_config_flow(
    hass: HomeAssistant, bypass_login, bypass_get_device
):
    """Test a successful config flow."""
    # Initialize a config flow
    result: FlowResult = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # If a user were to enter `test_username` for username and `test_password`
    # for password, it would result in this function call
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_INPUT,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "select"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"select_device": "pn_1"},
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "pn"
    assert result["data"] == {
        CONF_DID: "1",
        CONF_TOKEN: "eyJhcHBfaWQiOiAiMSIsICJ1c2VybmFtZSI6ICJ0ZXN0X3VzZXJuYW1lIiwgInBhc3N3b3JkIjogInRlc3RfcGFzc3dvcmQiLCAidG9rZW4iOiAidGVzdF90b2tlbiIsICJ1aWQiOiAidTEifQ==",
    }
    assert result["result"]


# In this case, we want to simulate a failure during the config flow.
# We use the `error_login_fixture` mock instead of `bypass_login`
# (note the function parameters) to raise an Exception during
# validation of the input config.
async def test_failed_config_flow(hass: HomeAssistant, error_on_login):
    """Test a failed config flow due to credential validation failure."""
    result: FlowResult = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_INPUT
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_failed_config_flow_no_device(
    hass: HomeAssistant, bypass_login, bypass_get_no_device
):
    """Test a failed config flow due to no device found for this user."""
    result: FlowResult = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_INPUT
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "no_devices"}


# FIXME seems not to work
async def test_update_existing_entry(
    hass: HomeAssistant, bypass_login, bypass_get_device
):
    """Test a successful config flow and update existing entry."""

    # Initialize a config flow
    result: FlowResult = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # If a user were to enter `test_username` for username and `test_password`
    # for password, it would result in this function call
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_INPUT,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "select"

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_DID: "1",
            CONF_TOKEN: "test_encoded_token",
        },
        entry_id="1",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"select_device": "pn_1"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "pn"
    assert result["data"] == {
        CONF_DID: "1",
        CONF_TOKEN: "eyJhcHBfaWQiOiAiMSIsICJ1c2VybmFtZSI6ICJ0ZXN0X3VzZXJuYW1lIiwgInBhc3N3b3JkIjogInRlc3RfcGFzc3dvcmQiLCAidG9rZW4iOiAidGVzdF90b2tlbiIsICJ1aWQiOiAidTEifQ==",
    }
    assert result["result"]


# # Our config flow also has an options flow, so we must test it as well.
# async def test_options_flow(hass):
#     """Test an options flow."""
#     # Create a new MockConfigEntry and add to HASS (we're bypassing config
#     # flow entirely)
#     entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")
#     entry.add_to_hass(hass)

#     # Initialize an options flow
#     result = await hass.config_entries.options.async_init(entry.entry_id)

#     # Verify that the first options step is a user form
#     assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
#     assert result["step_id"] == "user"

#     # Enter some fake data into the form
#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"],
#         user_input={platform: platform != SENSOR for platform in PLATFORMS},
#     )

#     # Verify that the flow finishes
#     assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
#     assert result["title"] == "test_username"

#     # Verify that the options were updated
#     assert entry.options == {BINARY_SENSOR: True, SENSOR: False, SWITCH: True}
