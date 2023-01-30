"""Tests for vaillant-plus client."""
import asyncio

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.vaillant_plus.client import VaillantApiHub
from .const import CONF_USERNAME, CONF_PASSWORD, CONF_HOST, CONF_HOST_API


async def test_client(hass, aioclient_mock, caplog):
    """Test API calls."""

    # To test the api submodule, we first create an instance of our API client
    client = VaillantApiHub(hass=hass)

    # Use aioclient_mock which is provided by `pytest_homeassistant_custom_components`
    # to mock responses to aiohttp requests.
    aioclient_mock.post(
        f"{CONF_HOST}/app/user/login",
        json={"code": 200, "data": {"token": "1", "uid": "2"}},
    )
    token = await client.login(CONF_USERNAME, CONF_PASSWORD)
    assert token.username == CONF_USERNAME
    assert token.password == CONF_PASSWORD
    assert token.token == "1"
    assert token.uid == "2"

    # We do the same for `async_set_title`. Note the difference in the mock call
    # between the previous step and this one. We use `patch` here instead of `get`
    # because we know that `async_set_title` calls `api_wrapper` with `patch` as the
    # first parameter
    aioclient_mock.get(
        f"{CONF_HOST_API}/app/bindings",
        json={
            "devices": [
                {
                    "remark": "",
                    "protoc": 3,
                    "wss_port": 8,
                    "ws_port": 9,
                    "did": "1",
                    "port_s": 10,
                    "is_disabled": False,
                    "wifi_soft_version": "wsv1",
                    "product_key": "abcdefg",
                    "port": 11,
                    "mac": "12345678abcd",
                    "role": "owner",
                    "dev_alias": "",
                    "is_sandbox": True,
                    "is_online": True,
                    "host": "test_host",
                    "type": "normal",
                    "product_name": "vSmartPro",
                }
            ]
        },
    )
    device_list = await client.get_device_list("test")
    assert device_list is not None
    assert len(device_list) == 1

    # In order to get 100% coverage, we need to test `api_wrapper` to test the code
    # that isn't already called by `async_get_data` and `async_set_title`. Because the
    # only logic that lives inside `api_wrapper` that is not being handled by a third
    # party library (aiohttp) is the exception handling, we also want to simulate
    # raising the exceptions to ensure that the function handles them as expected.
    # The caplog fixture allows access to log messages in tests. This is particularly
    # useful during exception handling testing since often the only action as part of
    # exception handling is a logging statement
    # caplog.clear()
    # aioclient_mock.put(
    #     "https://jsonplaceholder.typicode.com/posts/1", exc=asyncio.TimeoutError
    # )
    # assert (
    #     await api.api_wrapper("put", "https://jsonplaceholder.typicode.com/posts/1")
    #     is None
    # )
    # assert (
    #     len(caplog.record_tuples) == 1
    #     and "Timeout error fetching information from" in caplog.record_tuples[0][2]
    # )

    # caplog.clear()
    # aioclient_mock.post(
    #     "https://jsonplaceholder.typicode.com/posts/1", exc=aiohttp.ClientError
    # )
    # assert (
    #     await api.api_wrapper("post", "https://jsonplaceholder.typicode.com/posts/1")
    #     is None
    # )
    # assert (
    #     len(caplog.record_tuples) == 1
    #     and "Error fetching information from" in caplog.record_tuples[0][2]
    # )

    # caplog.clear()
    # aioclient_mock.post("https://jsonplaceholder.typicode.com/posts/2", exc=Exception)
    # assert (
    #     await api.api_wrapper("post", "https://jsonplaceholder.typicode.com/posts/2")
    #     is None
    # )
    # assert (
    #     len(caplog.record_tuples) == 1
    #     and "Something really wrong happened!" in caplog.record_tuples[0][2]
    # )

    # caplog.clear()
    # aioclient_mock.post("https://jsonplaceholder.typicode.com/posts/3", exc=TypeError)
    # assert (
    #     await api.api_wrapper("post", "https://jsonplaceholder.typicode.com/posts/3")
    #     is None
    # )
    # assert (
    #     len(caplog.record_tuples) == 1
    #     and "Error parsing information from" in caplog.record_tuples[0][2]
    # )
