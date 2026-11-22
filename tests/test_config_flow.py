"""Test vaillant-plus config flow."""
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from vaillant_plus_cn_api import Device

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
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # If a user were to enter `test_username` for username and `test_password`
    # for password, it would result in this function call
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_INPUT,
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "select"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"select_device": "1"},
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == FlowResultType.CREATE_ENTRY
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
async def _submit_user_step(hass: HomeAssistant) -> FlowResult:
    """Run the user step with the mock credentials."""
    result: FlowResult = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    return await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_INPUT
    )


async def test_failed_config_flow(hass: HomeAssistant, error_on_login):
    """An unexpected error must not be reported as a credential problem."""
    result = await _submit_user_step(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_failed_config_flow_invalid_credentials(
    hass: HomeAssistant, invalid_credentials_on_login
):
    """A wrong username/password combination is reported as such."""
    result = await _submit_user_step(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_failed_config_flow_cannot_connect(
    hass: HomeAssistant, connection_error_on_login
):
    """An unreachable API host must not be reported as a credential problem."""
    result = await _submit_user_step(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_failed_config_flow_unsupported_device(
    hass: HomeAssistant, bypass_login, unsupported_device_on_get_device_list
):
    """A device the API library cannot model must not crash the flow.

    Reported in issues #27 and #28: an account owning an eloCIRC made
    `get_device_list()` raise `TypeError` outside the try block, so the flow
    died with an unhandled exception instead of showing an error.
    """
    result = await _submit_user_step(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unsupported_device"}


async def test_failed_config_flow_no_device(
    hass: HomeAssistant, bypass_login, bypass_get_no_device
):
    """Test a failed config flow due to no device found for this user."""
    result: FlowResult = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_INPUT
    )

    assert result["type"] == FlowResultType.FORM
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
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # If a user were to enter `test_username` for username and `test_password`
    # for password, it would result in this function call
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_INPUT,
    )

    assert result["type"] == FlowResultType.FORM
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
        user_input={"select_device": "1"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
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
#     assert result["type"] == FlowResultType.FORM
#     assert result["step_id"] == "user"

#     # Enter some fake data into the form
#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"],
#         user_input={platform: platform != SENSOR for platform in PLATFORMS},
#     )

#     # Verify that the flow finishes
#     assert result["type"] == FlowResultType.CREATE_ENTRY
#     assert result["title"] == "test_username"

#     # Verify that the options were updated
#     assert entry.options == {BINARY_SENSOR: True, SENSOR: False, SWITCH: True}


def _device(device_id: str, **overrides) -> Device:
    """A bound device as the API library returns it."""
    fields = dict(
        id=device_id,
        mac=f"mac{device_id}",
        product_key="pk",
        product_id="p1",
        product_name="vSMART Pro",
        product_verbose_name="pvn",
        is_online=True,
        is_manager=True,
        group_id=2,
        sno="sno",
        create_time="2000-01-01 00:00:00",
        last_offline_time="2000-12-31 00:00:00",
        model_alias="",
        model="",
        serial_number="",
        services_count=0,
    )
    fields.update(overrides)
    return Device(**fields)


async def _select_form(hass: HomeAssistant, devices: list[Device]) -> FlowResult:
    """Log in with an account that has `devices` bound and stop at selection."""
    with patch(
        "vaillant_plus_cn_api.VaillantApiClient.get_device_list",
        return_value=devices,
    ):
        result = await _submit_user_step(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "select"
    return result


def _options(result: FlowResult) -> dict[str, str]:
    """The choices offered by the selection form, keyed by device id."""
    return result["data_schema"].schema["select_device"].container


async def test_every_bound_device_is_offered(hass: HomeAssistant, bypass_login):
    """Two units of the same model are both listed and tell apart (#64)."""
    result = await _select_form(
        hass,
        [
            _device("d1", dev_alias="客厅"),
            _device("d2", dev_alias="卧室"),
            _device("d3"),
        ],
    )

    options = _options(result)
    assert list(options) == ["d1", "d2", "d3"]
    assert len(set(options.values())) == 3
    assert options["d1"] == "客厅 (vSMART Pro) - d1"
    assert options["d3"] == "vSMART Pro - d3"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"select_device": "d2"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    # The owner's name for it, so two entries for one model differ.
    assert result["title"] == "卧室 (vSMART Pro)"
    assert result["data"][CONF_DID] == "d2"


async def test_second_device_can_be_added(hass: HomeAssistant, bypass_login):
    """With one device set up, the other one is marked and preselected."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="d1",
        data={CONF_DID: "d1", CONF_TOKEN: "test_encoded_token"},
    ).add_to_hass(hass)

    result = await _select_form(hass, [_device("d1"), _device("d2")])

    options = _options(result)
    assert options["d1"].endswith("✓")
    assert not options["d2"].endswith("✓")
    marker = result["data_schema"].schema
    default = next(k for k in marker if k == "select_device").default()
    assert default == "d2"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"select_device": "d2"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_DID] == "d2"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 2
