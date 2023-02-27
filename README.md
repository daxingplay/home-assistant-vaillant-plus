# home-assistant-vaillant-plus
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![Coverage][coverage-shield]][coverage]
![GitHub all releases][download-all]
![GitHub release (latest by SemVer)][download-latest]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Community Forum][forum-shield]][forum]

Home Assistant custom component for controlling vSmart in Vaillant+ cn app.

## Screenshot

![screenshot](docs/images/screenshot-all.jpg)

## Installation

### Pre-requirements
- You need connect your Vaillant vSmart device through Vaillant+([iOS](https://apps.apple.com/cn/app/%E5%A8%81%E7%AE%A1%E5%AE%B6/id1465568192) | Android ) App.

### Installation Methods
#### HACS
Add custom repository `daxingplay/home-assistant-vaillant-plus` in HACS.

#### Manual
Copy `custom_components/vaillant_plus` into your Home Assistant `config` directory.

### Post installation steps
- Restart HA
- Search for this integration in `Settings -> Devices & Services`
- Click `Add integration` and search for `Vaillant Plus`
- Click `Configure` in Vaillant Plus integration to start config flow
- Enter your username and password for the Vaillant+ App
- If login successfully, select the proper Vaillant vSmart device from the list
- All done

## Contributions are welcome!
If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

Component built with integration_blueprint.

***

[vaillant-plus]: https://github.com/daxingplay/home-assistant-vaillant-plus
[buymecoffee]: https://www.buymeacoffee.com/daxingplay
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square
[commits-shield]: https://img.shields.io/github/commit-activity/y/daxingplay/home-assistant-vaillant-plus.svg?style=flat-square
[commits]: https://github.com/daxingplay/home-assistant-vaillant-plus/commits/master
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square
[coverage-shield]: https://img.shields.io/coverallsCoverage/github/daxingplay/home-assistant-vaillant-plus?style=flat-square
[coverage]: https://coveralls.io/github/daxingplay/home-assistant-vaillant-plus?branch=master
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=flat-square
[forum]: https://github.com/daxingplay/home-assistant-vaillant-plus/issues
[license]: https://github.com/daxingplay/home-assistant-vaillant-plus/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/daxingplay/home-assistant-vaillant-plus.svg?style=flat-square
[maintenance-shield]: https://img.shields.io/badge/maintainer-daxingplay-blue.svg?style=flat-square
[releases-shield]: https://img.shields.io/github/release/daxingplay/home-assistant-vaillant-plus.svg?style=flat-square
[releases]: https://github.com/daxingplay/home-assistant-vaillant-plus/releases
[user_profile]: https://github.com/daxingplay
[download-all]: https://img.shields.io/github/downloads/daxingplay/home-assistant-vaillant-plus/total?style=flat-square
[download-latest]: https://img.shields.io/github/downloads/daxingplay/home-assistant-vaillant-plus/latest/total?style=flat-square