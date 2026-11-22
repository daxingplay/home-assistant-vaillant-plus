# Changelog

<!--next-version-placeholder-->
## v2.0.0 (2026-11-22)
* **First stable release of 2.0.** It contains everything from [v2.0.0-beta.1](#v200-beta1-2026-11-21) and [v2.0.0-beta.2](#v200-beta2-2026-11-22) below, with no changes since beta.2. **Read v2.0.0-beta.1 before upgrading from v1.5.1:** the climate and water heater entities are renamed (entity ids do not change), familyCONNECT gateways get central heating control, and vSMART owners see changes too.
* Verified on a vSMART Pro by the maintainer, and on a familyCONNECT VC 100p CN with a turboTEC plus by [@Archie87](https://github.com/Archie87) (#62).

## v2.0.0-beta.2 (2026-11-22)
* [#64](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/64) **Devices in a second home, and devices shared from another account, can now be added.** Only the first home of an account was read, so its other devices never appeared in the device list.
* **Several devices of the same model can be told apart when adding them.** The device list shows the name each device was given in the Vaillant app and its device id, instead of only the shared model name, and a new entry is titled with that name, so two vSMART Pro no longer both show as "vSMART Pro". Devices that are already set up are marked ✓, and the first one not yet set up is preselected. Each device is still added as its own entry: add the integration again for the next device. Existing entries keep their titles, and nothing changes for devices already set up.
* Requires vaillant-plus-cn-api 2.2.0, which reads every home of the account and the devices shared into it.

## v2.0.0-beta.1 (2026-11-21)
* [#30](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/30) **Support central heating on familyCONNECT gateway devices.** A gateway sits at the boiler and controls the central heating *flow* temperature rather than a room temperature, so it now gets its own climate entity targeting `Flow_Temperature_Setpoint`. It shows the measured flow temperature (`Flow_temperature`) as its current temperature, and takes its setpoint range from the boiler's reported central heating limits (30–60 °C on a turboTEC plus), falling back to 30–75 °C when none are reported, in 0.5 °C steps. It shows as heating only while the burner fires for central heating (`burn_status` 4, Vaillant's S.4), not whenever the water has cooled below the setpoint. This is why a gateway previously showed hot water control only. **vSMART owners see changes too:** the entity names below, and on a vSMART without a hot water tank the water heater shows the flow temperature again (as before v1.2.5) instead of 127.5 °C. Verified on a familyCONNECT VC 100p CN with a turboTEC plus by [@Archie87](https://github.com/Archie87). Thanks to [@elwinchen1986](https://github.com/elwinchen1986) whose fork worked out the initial gateway attribute mapping.
* **The climate and water heater entities have names of their own** - 供暖 / 生活热水 (Central heating / Domestic hot water) after the device name - instead of both showing the device name alone, which listed two identical rows on a gateway's device page. Entity ids do not change.
* **The water heater shows its target temperature again.** It reported the settable DHW limits as a target range, so the UI showed "35 °C-65 °C" instead of the setpoint; the limits stay as the entity's min / max. Its "on" / "off" operations are now translated (开启 / 关闭).
* **Temperatures a device reports as "no reading" are no longer shown as real measurements.** Neither device omits an attribute it has no value for — it sends the raw eBUS sentinel instead — so a gateway with no boiler bound reported every temperature as 127.5 °C and its room temperature as 255 °C, and a vSMART with no tank reported a 127.5 °C tank. Those values were rendered as genuine readings and written into long term statistics. Affected sensors now show as unavailable instead.
* Domestic hot water limits sent as the "no reading" sentinel (127.5 °C) no longer become the water heater's range; the 35–65 °C defaults apply instead.
* **Accounts with more than one device no longer fight over the login session.** The cloud keeps a single session per account, and each bound device gets its own config entry, so two entries would take turns logging in and invalidating each other's token — showing up as entries repeatedly going unavailable and reconnecting, and as the Vaillant app being logged out. A token obtained by one entry is now adopted by the others instead of being answered with another login, and entries rejected at the same moment, typically at startup, log in once between them.
* Turning a vSMART's heating on or off from Home Assistant now shows straight away instead of snapping back until the cloud echoes the change. The state is still read from `Enabled_Heating`, so changes made at the thermostat or in the Vaillant app keep showing up.
* [#66](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/66) **New "Indoor temperature setting" (室内温度设定) on gateways.** It writes `indoor_temperature`, the indoor temperature weather compensation works with, as in the Vaillant app (5–30 °C, 0.5 °C steps). Every gateway with a boiler connected gets it. If a room sensor is paired, the gateway reports the sensor's reading in the same field, so leave the setting alone in that case.
* New sensors: indoor temperature, the domestic hot water mode setting, and **burner modulation**. The gateway reports how hard the burner is firing (`valueModulation_currentValue`, 0–100 %); it is now a sensor, so a slow warm-up can be told apart from a burner that is barely lit. The value stays at its last reading after the flame goes out, so read it together with the burn status.
* Requires vaillant-plus-cn-api 2.1.0, which exposes the fields identifying which product family a device belongs to.

## v1.5.1 (2026-11-21)
* **Diagnostics no longer expose a familyCONNECT gateway's Wi-Fi name, home network address, serial numbers or location code.** The gateway reports these as device attributes, several of them hex-encoded, so they were included as-is. If you have posted a gateway diagnostics file in a public issue, consider editing it to remove the `WiFi_SSID`, `WiFi_IP`, `gateway_sn`, `device_sn`, `device_serial_number`, `traceability_number`, `Gateway_traceability_number` and `location_group` values. Found and fixed by [@Archie87](https://github.com/Archie87) in #62.

## v1.5.0 (2026-11-21)
* [#65](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/65) **Chinese entity names now actually show up.** The Chinese translations shipped as `translations/zh.json`, but Home Assistant asks for `zh-Hans.json` on a Simplified Chinese install and never reads `zh`, so every entity name, and the config flow, quietly fell back to English. The file is now `zh-Hans.json`. If you worked around this by copying `zh.json` to `zh-Hans.json` by hand, nothing more is needed: the update replaces your copy with the same content. The translation test now compares the names Home Assistant resolves with the language's own file. The old check only asked whether a name resolved, which the English fallback always satisfies.
* [#67](https://github.com/daxingplay/home-assistant-vaillant-plus/issues/67) **The gas consumption sensors now show kWh instead of hex strings, and can be added to the Energy dashboard.** The cloud's 8-digit values are decoded as kilojoules and converted to kWh. **The unit is inferred from sample data, not documented by Vaillant**: if the figures disagree with the Vaillant app, please comment on #67. The today, monthly, yearly and total sensors are `total_increasing`, so any of them can be picked as a gas source in the Energy dashboard (pick one, or the consumption is counted twice). The yesterday sensors carry no state class, since their value jumps once a day. These sensors keep their entity ids, are no longer diagnostic entities, and lose "raw" from their names. The undecoded hex values move to new `…_raw` diagnostic sensors, which are hidden by default: they keep updating and recording history, so the conversion can be checked. Unhide them from the entity settings to see them.
* Diagnostics now report the fields that identify a device's product family (`platform`, `product_id`, `sub_product_key`), so a report about an unsupported device can be acted on without asking for a second round of information. Per-unit identifiers such as the serial number stay out of the dump, as before.

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