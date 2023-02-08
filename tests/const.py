"""Constants for vaillant-plus tests."""

from custom_components.vaillant_plus.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_DID,
    CONF_TOKEN,
)

# Mock config data to be used across multiple tests
MOCK_USERNAME = "test_username"
MOCK_PASSWORD = "test_password"
MOCK_DID = "1"
MOCK_INPUT = {CONF_USERNAME: MOCK_USERNAME, CONF_PASSWORD: MOCK_PASSWORD}
MOCK_CONFIG_ENTRY_DATA = {
    CONF_DID: MOCK_DID,
    CONF_TOKEN: "eyJhcHBfaWQiOiAiMSIsICJ1c2VybmFtZSI6ICJ0ZXN0X3VzZXJuYW1lIiwgInBhc3N3b3JkIjogInRlc3RfcGFzc3dvcmQiLCAidG9rZW4iOiAidGVzdF90b2tlbiIsICJ1aWQiOiAidTEifQ==",
}

CONF_HOST = "https://appapi.vaillant.com.cn"
CONF_HOST_API = "https://api.vaillant.com.cn"
