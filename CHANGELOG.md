# Changelog

<!--next-version-placeholder-->
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