"""Constants for vaillant-plus tests."""

from custom_components.vaillant_plus.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
)

# Mock config data to be used across multiple tests
MOCK_USERNAME = "test_username"
MOCK_PASSWORD = "test_password"
MOCK_INPUT = {CONF_USERNAME: MOCK_USERNAME, CONF_PASSWORD: MOCK_PASSWORD}

CONF_HOST = "https://appapi.vaillant.com.cn"
CONF_HOST_API = "https://api.vaillant.com.cn"
