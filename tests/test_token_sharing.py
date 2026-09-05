"""One account, several config entries, one cloud session.

The cloud keeps a single session per account: logging in invalidates the
token every other session holds. An account with more than one bound device
gets one config entry per device, so without coordination each entry answers
the other's login by logging in itself, and the two knock each other offline
in turn.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.helpers.dispatcher import async_dispatcher_send
from vaillant_plus_cn_api import InvalidAuthError, Token

from custom_components.vaillant_plus.const import EVT_TOKEN_UPDATED


# The username the `device_api_client` fixture is built with. The token
# update signal is keyed by account, so a test using any other name would
# simply not be listened to.
USERNAME = "u1"


def _token(access_token: str) -> Token:
    return Token(
        app_id="a1",
        username=USERNAME,
        password="p1",
        access_token=access_token,
        uid="1",
    )


async def test_client_adopts_a_token_published_by_another_entry(
    hass, device_api_client
):
    """A refresh anywhere on the account is picked up here."""
    device_api_client._token = _token("old")

    new = _token("new")
    async_dispatcher_send(hass, EVT_TOKEN_UPDATED.format(new.username), new)
    await hass.async_block_till_done()

    assert device_api_client._token.access_token == "new"
    # The API client must be updated too, or the next request still sends the
    # dead token and triggers another pointless login.
    device_api_client._api_client.update_token.assert_called_with(new)


async def test_stale_token_rejection_does_not_trigger_a_second_login(
    hass, device_api_client
):
    """The ping-pong: do not log in over a token someone else just published.

    The request failed with the *old* token, but by the time the failure is
    handled the current token is already the new one. Logging in here would
    invalidate the token the other entry is using, and it would then log in
    and invalidate ours.
    """
    failed = _token("old")
    device_api_client._token = _token("new")
    device_api_client._api_client.login = AsyncMock()

    await device_api_client._get_token(failed)

    device_api_client._api_client.login.assert_not_awaited()
    device_api_client._api_client.update_token.assert_called_with(_token("new"))


async def test_genuinely_stale_token_still_logs_in(hass, device_api_client):
    """A rejection with the current token is a real expiry."""
    current = _token("current")
    device_api_client._token = current
    fresh = _token("fresh")
    device_api_client._api_client.login = AsyncMock(return_value=fresh)

    await device_api_client._get_token(current)

    device_api_client._api_client.login.assert_awaited_once()
    assert device_api_client._token.access_token == "fresh"


async def test_two_entries_settle_on_one_token(hass, device_api_client):
    """End to end: the second entry must not answer a login with a login."""
    from custom_components.vaillant_plus.client import VaillantClient

    first = device_api_client
    first._token = _token("t1")

    with patch(
        "custom_components.vaillant_plus.utils.get_aiohttp_session"
    ), patch("custom_components.vaillant_plus.client.VaillantApiClient"):
        second = VaillantClient(hass, _token("t1"), "2")

    try:
        # The first entry's token expires and it logs in, publishing t2.
        first._api_client.login = AsyncMock(return_value=_token("t2"))
        await first._get_token(_token("t1"))
        await hass.async_block_till_done()

        # The second entry was holding t1 and has now adopted t2 ...
        assert second._token.access_token == "t2"

        # ... so its own in-flight request failing on t1 must not log in.
        second._api_client.login = AsyncMock()
        await second._get_token(_token("t1"))
        second._api_client.login.assert_not_awaited()
    finally:
        await second.close()


async def test_close_stops_listening_for_token_updates(hass, device_api_client):
    """An unloaded entry must not keep adopting tokens."""
    await device_api_client.close()

    device_api_client._token = _token("old")
    new = _token("new")
    async_dispatcher_send(hass, EVT_TOKEN_UPDATED.format(new.username), new)
    await hass.async_block_till_done()

    assert device_api_client._token.access_token == "old"
