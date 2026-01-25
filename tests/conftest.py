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

from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from vaillant_plus_cn_api import Device, InvalidAuthError, Token

from .const import MOCK_PASSWORD, MOCK_USERNAME

pytest_plugins = "pytest_homeassistant_custom_component"

# Global patch for pycares.Channel to prevent _run_safe_shutdown_loop thread creation.
# This thread causes test failures in older versions of pytest-homeassistant-custom-component
# (0.13.128, 0.13.152, 0.13.162) which don't have an exception for this thread.
# We apply this patch at module load time to ensure it's in place before any tests run.
_pycares_patcher = None


def pytest_configure(config):
    """Apply pycares patch at pytest configuration time."""
    global _pycares_patcher
    try:
        _pycares_patcher = patch("pycares.Channel")
        _pycares_patcher.start()
    except Exception:
        # If pycares is not available or patching fails, continue without mock
        pass


def pytest_unconfigure(config):
    """Remove pycares patch when pytest finishes."""
    global _pycares_patcher
    if _pycares_patcher is not None:
        try:
            _pycares_patcher.stop()
        except Exception:
            pass


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
async def device_api_client_fixture(hass):
    """Create a VaillantClient with mocked dependencies to avoid background threads."""
    # Import VaillantClient inside fixture to ensure patches are applied first
    from custom_components.vaillant_plus import VaillantClient

    # Mock the aiohttp session to avoid event loop issues
    mock_session = MagicMock()
    mock_session.close = AsyncMock()

    # Mock VaillantApiClient to prevent background threads (_run_safe_shutdown_loop)
    # Patch at both source and import locations to ensure the mock is used
    mock_api_client = MagicMock()
    mock_api_client.control_device = AsyncMock(return_value=True)
    mock_api_client.get_device_list = AsyncMock(return_value=[])
    mock_api_client.login = AsyncMock()
    mock_api_client.update_token = MagicMock()

    with patch(
        "custom_components.vaillant_plus.utils.get_aiohttp_session",
        return_value=mock_session,
    ), patch(
        "vaillant_plus_cn_api.VaillantApiClient",
        return_value=mock_api_client,
    ), patch(
        "custom_components.vaillant_plus.client.VaillantApiClient",
        return_value=mock_api_client,
    ):
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
