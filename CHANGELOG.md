# Changelog

<!--next-version-placeholder-->
## v1.2.8 (2026-08-30)
* [#27](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/27) [#28](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/28) Require `vaillant-plus-cn-api` 2.0.1, which no longer crashes on accounts containing a device it cannot describe. Previously a single such device (for example an eloCIRC 循环水魔方, returned by the cloud with `"modelInfo": null`) raised `TypeError: 'NoneType' object is not subscriptable` while reading the device list, so the integration could not be set up at all — including for the supported devices in the same account.

## v1.2.7 (2026-08-30)
* [#34](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/34) Support `water_heater.turn_on` / `water_heater.turn_off`, so device actions and scripts can switch domestic hot water on and off. The DHW temperature limits now fall back to 35–65 °C when the gateway does not report them.
* [#29](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/29) [#35](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/35) Reuse the access token stored in the config entry. Previously every start sent unauthenticated requests, was rejected with `token 过期` and logged in again, which invalidated the session of the Vaillant mobile app. Re-login failures now back off instead of retrying in a tight loop.
* [#33](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/33) [#30](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/30) Discover entities from all attributes received so far, on every gateway frame, instead of only the first one. Attributes that arrive in a later partial update now create their entities, and the "missing required attribute" warning is logged once, listing what was expected and what the device reported.
* Add config entry diagnostics (device attributes with credentials redacted) to make gateway issues reportable in one click.
* Import `DeviceInfo` and `EntityCategory` from their canonical locations, with a fallback for older Home Assistant releases.

## v1.2.6 (2026-08-30)
* Use Home Assistant unit constants for water pressure (`bar`) and Wi-Fi RSSI (`dBm`) instead of hard-coded strings.
* Add regression tests validating every sensor description against the unit table of the Home Assistant version under test, so a missing or invalid unit fails CI instead of warning in users' logs.

## v1.2.5 (2026-06-24)
* Improve China gateway state handling: more device attributes exposed as sensors, better partial-update guards for climate and water heater.
* Declare `°C` on all temperature sensors, fixing the `is using native unit of measurement 'None' which is not a valid unit for the device class ('temperature')` warnings in Home Assistant.
* Fix test compatibility with newer `pytest-homeassistant-custom-component` releases and extend the CI matrix to recent Home Assistant versions.

## v1.2.4 (2024-04-05)
* [#13](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/13) Support to disable IPv6 in this integration for Home Assistant version >= `2023.10.0`.
* Add Github actions for more HA versions.

## v0.6.0 (2023-05-13)
* Refactor to use new API. Resolve [#5](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/5)

## v0.6.0 (2023-05-13)
### Others
* Re-tag to match HACS requirements.

## v0.5.1 (2023-05-13)
### Bug
* Fix login failed issues when auth token expired.

## v0.3.1 (2023-02-27)
### Bug
* Fix custom components cannot be installed due to dependency conflict.