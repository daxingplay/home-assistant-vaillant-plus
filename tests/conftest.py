"""Global fixtures for vaillant-plus integration."""
# Fixtures allow you to replace functions with a Mock object. You can perform
# many options via the Mock to reflect a particular behavior from the original
# function that you want to see without going through the function's actual logic.
# Fixtures can either be passed into tests as parameters, or if autouse=True, they
# will automatically be used across all tests.
#
# Fixtures that are defined in conftest.py are available across all tests. You can also
# define fixtures within a particular test file to scope them locally.
#
# pytest_homeassistant_custom_component provides some fixtures that are provided by
# Home Assistant core. You can find those fixture definitions here:
# https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/blob/master/pytest_homeassistant_custom_component/common.py
#
# See here for more info: https://docs.pytest.org/en/latest/fixture.html (note that
# pytest includes fixtures OOB which you can use as defined on this page)

from unittest.mock import patch

import pytest
from vaillant_plus_cn_api import Device, InvalidAuthError, Token

from custom_components.vaillant_plus import VaillantClient
from .const import MOCK_PASSWORD, MOCK_USERNAME

pytest_plugins = "pytest_homeassistant_custom_component"


# This fixture enables loading custom integrations in all tests.
# Remove to enable selective use of this fixture
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


# This fixture, when used, will result in calls to async_get_data to return None. To have the call
# return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the patch call.
@pytest.fixture(name="bypass_get_data")
def bypass_get_data_fixture():
    """Skip calls to get data from API."""
    with patch(
        "custom_components.vaillant_plus.VaillantClient.async_get_data"
    ):
        yield


@pytest.fixture(name="bypass_login")
def bypass_login_fixture():
    """Skip calls to get data from API."""
    with patch(
        "vaillant_plus_cn_api.VaillantApiClient.login",
        return_value=Token(
            app_id="1",
            username=MOCK_USERNAME,
            password=MOCK_PASSWORD,
            access_token="test_token",
            uid="u1",
        ),
    ):
        yield


@pytest.fixture(name="bypass_get_device")
def bypass_get_device_fixture():
    """Skip calls to get data from API."""
    with patch(
        "vaillant_plus_cn_api.VaillantApiClient.get_device_list",
        return_value=[
            Device(
                id="1",
                mac="mac2",
                product_key="pk",
                product_id="p1",
                product_name="pn",
                product_verbose_name="pvn",
                is_online=True,
                is_manager=True,
                group_id=2,
                sno="sno",
                create_time="2000-01-01 00:00:00",
                last_offline_time="2000-12-31 00:00:00",
                model_alias="weijingling",
                model="model_name",
                serial_number="s1",
                services_count=0,
            )
        ],
    ):
        yield


@pytest.fixture(name="bypass_get_no_device")
def bypass_get_no_device_fixture():
    """Skip calls to get data from API."""
    with patch(
        "vaillant_plus_cn_api.VaillantApiClient.get_device_list",
        return_value=[],
    ):
        yield

@pytest.fixture(name="bypass_control_device")
def bypass_control_device_fixture():
    """Skip calls to get data from API."""
    with patch(
        "vaillant_plus_cn_api.VaillantApiClient.control_device",
        return_value=True,
    ):
        yield

# In this fixture, we are forcing calls to login to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="error_on_login")
def error_login_fixture():
    """Simulate error when retrieving data from API."""
    with patch(
        "vaillant_plus_cn_api.VaillantApiClient.login",
        side_effect=Exception,
    ):
        yield


# In this fixture, we are forcing calls to get device list to raise an InvalidAuthError Exception.
@pytest.fixture(name="invalid_auth_on_device_list")
def error_invaild_auth_when_get_device_list_fixture():
    """Simulate error when retrieving data from API."""
    with patch(
        "vaillant_plus_cn_api.VaillantApiClient.get_device_list",
        side_effect=InvalidAuthError,
    ):
        yield

# In this fixture, we are forcing calls to control device to raise an InvalidAuthError Exception.
@pytest.fixture(name="invalid_auth_on_control_device")
def error_invaild_auth_when_control_device_fixture():
    """Simulate error when retrieving data from API."""
    with patch(
        "vaillant_plus_cn_api.VaillantApiClient.control_device",
        side_effect=InvalidAuthError,
    ):
        yield


# Mock VaillantDeviceApiClient
@pytest.fixture(name="device_api_client")
def device_api_client_fixture(hass):
    device_api_client = VaillantClient(
        hass=hass,
        token=Token("a1", "u1", "p1"),
        device_id="1",
    )
    device_api_client._device = Device(
        id="1",
        mac="mac2",
        product_key="pk",
        product_id="p1",
        product_name="pn",
        product_verbose_name="pvn",
        is_online=True,
        is_manager=True,
        group_id=2,
        sno="sno",
        create_time="2000-01-01 00:00:00",
        last_offline_time="2000-12-31 00:00:00",
        model_alias="weijingling",
        model="model_name",
        serial_number="s1",
        services_count=0,
    )
    yield device_api_client
