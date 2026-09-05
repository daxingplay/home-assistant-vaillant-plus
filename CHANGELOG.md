# Changelog

<!--next-version-placeholder-->
## v1.5.0 (2026-09-05)
* [#30](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/30) **Support central heating on familyCONNECT gateway devices.** A gateway sits at the boiler and controls the central heating *flow* temperature rather than a room temperature, so it now gets its own climate entity targeting `Flow_Temperature_Setpoint` over a 30–75 °C range. This is why a gateway previously showed hot water control only. The vSMART thermostat is unchanged. Thanks to [@elwinchen1986](https://github.com/elwinchen1986) whose fork worked out the initial gateway attribute mapping.
* **Temperatures a device reports as "no reading" are no longer shown as real measurements.** Neither device omits an attribute it has no value for — it sends the raw eBUS sentinel instead — so a gateway with no boiler bound reported every temperature as 127.5 °C and its room temperature as 255 °C, and a vSMART with no tank reported a 127.5 °C tank. Those values were rendered as genuine readings and written into long term statistics. Affected sensors now show as unavailable instead.
* New sensors: indoor temperature, and the domestic hot water mode setting.
* Requires vaillant-plus-cn-api 2.1.0, which exposes the fields identifying which product family a device belongs to.

## v1.4.0 (2026-08-30)
* **This release requires Home Assistant 2024.2 or later.** Older installations keep working on v1.3.0 and HACS will not offer them the update. Dropping them removes the compatibility shims the integration carried for releases from 2022.11 on, and is what allows entity names to be translated at all.
* Entity names are now translatable. Every sensor and binary sensor carries a `translation_key`, and Chinese names are provided for all of them, so the entities show as 供水温度 / 水箱温度 / 暖气开启状态 rather than English. Languages without a translation keep the English names. Chinese wording follows [@elwinchen1986](https://github.com/elwinchen1986)'s fork where it had a name for an attribute.
* **The displayed names of your entities change.** Entities now use `has_entity_name`, which is what allows Home Assistant to translate them, and it also makes Home Assistant compose the friendly name from the device name and the entity name — `Flow temperature` becomes `威精灵 供水温度`. The climate and water heater entities, which had no name of their own, now show the device name instead of their entity id.
  * **Entity ids do not change**, so automations, scripts and dashboards keep working. Only the displayed names do.
  * Anything that keys on the *name* rather than the entity id — an automatically titled dashboard card, a voice assistant phrase, a template matching `friendly_name` — will see the new name.
  * New installations get device-prefixed entity ids (`sensor.wei_jing_ling_flow_temperature`); existing installations keep the ids they already have.
* **Upgrading from v1.2.4 or earlier: temperature statistics need a one-time fix.** After the restart, Home Assistant logs `The unit of sensor.… (°C) cannot be converted to the unit of previously compiled statistics (None)` once per temperature sensor and stops generating long term statistics for them. v1.2.5 added the `°C` that those sensors were missing, and the recorder will not mix unitless history with `°C` history. Open [Developer tools -> Statistics](https://my.home-assistant.io/redirect/developer_statistics/), pick each listed sensor and update the unit of the historical statistics to `°C` — the old readings were already Celsius, only unlabelled, so nothing is lost. Current values and short term history were never affected. See [Troubleshooting](README.md#troubleshooting).

## v1.3.0 (2026-08-30)
* Support `climate.turn_on` / `climate.turn_off`, so scripts and device actions can switch the central heating on and off. Home Assistant 2024.2 and later only accept these on entities that advertise the feature, the same gap [#34](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/34) hit on the water heater.
* A command that could not be delivered now raises instead of being silently ignored. `control_device` gives up after three failed attempts and nothing re-sends the command, but its result was discarded, so a failed command looked exactly like a successful one.
* Successful commands are applied to the entity state immediately instead of waiting for the cloud to echo them back over the websocket, so the UI no longer snaps back to the old value for a few seconds after a change. Failed commands leave the state untouched, since the device still holds its old value.
* Expose the central heating mode setting (`Mode_Setting_CH`) as a diagnostic sensor.

## v1.2.9 (2026-08-30)
* [#27](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/27) [#28](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/28) The device list is now fetched inside the config flow's error handling, so a device the API library cannot describe shows a proper "unsupported device" message instead of aborting the flow with an unhandled `TypeError` that looked like a login failure.
* Login failures are no longer all reported as `invalid_auth`: wrong credentials, an unreachable server and unexpected errors are told apart, so network problems stop looking like a wrong password.
* Add the missing `no_devices` message to the strings and translations, and fix the Chinese translation of `unknown` (位置错误 → 未知错误).

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