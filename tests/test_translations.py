"""Keep the entity descriptions and the translation files in sync.

Entity names are translated by Home Assistant through the `entity` section of
the translation files, keyed by the description's `translation_key`. A key that
is present in one place and missing in the other silently falls back to the
English name in the description, which is easy to miss in review.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/vaillant_plus"

# Files that must carry the full set of entity names. `translations/pt.json`
# is deliberately absent: it has no entity section yet, and Home Assistant
# falls back to English for the languages that do not translate them.
TRANSLATION_FILES = (
    COMPONENT / "strings.json",
    COMPONENT / "translations/en.json",
    COMPONENT / "translations/zh.json",
)


def _descriptions(module_name: str, container: str) -> list:
    module = __import__(
        f"custom_components.vaillant_plus.{module_name}", fromlist=[container]
    )
    return list(getattr(module, container))


DOMAINS = {
    "sensor": ("sensor", "SENSOR_DESCRIPTIONS"),
    "binary_sensor": ("binary_sensor", "BINARY_SENSOR_DESCRIPTIONS"),
}


@pytest.mark.parametrize("domain", sorted(DOMAINS))
def test_every_description_has_a_translation_key(domain):
    """A description without a translation key can never be translated."""
    module_name, container = DOMAINS[domain]
    missing = [
        description.key
        for description in _descriptions(module_name, container)
        if getattr(description, "translation_key", None) is None
    ]

    assert not missing, f"{domain} descriptions without a translation key: {missing}"


@pytest.mark.parametrize("domain", sorted(DOMAINS))
def test_every_description_keeps_an_english_fallback_name(domain):
    """Home Assistant releases without entity translations use `name`."""
    module_name, container = DOMAINS[domain]
    missing = [
        description.key
        for description in _descriptions(module_name, container)
        if not getattr(description, "name", None)
    ]

    assert not missing, f"{domain} descriptions without a fallback name: {missing}"


@pytest.mark.parametrize("path", TRANSLATION_FILES, ids=lambda p: p.name)
@pytest.mark.parametrize("domain", sorted(DOMAINS))
def test_translation_files_cover_every_entity(path: Path, domain: str):
    """Every translation key is translated, and nothing extra is left behind."""
    module_name, container = DOMAINS[domain]
    expected = {
        description.translation_key
        for description in _descriptions(module_name, container)
    }

    translations = json.loads(path.read_text())
    translated = set(translations.get("entity", {}).get(domain, {}))

    assert not expected - translated, (
        f"{path.name} is missing {domain} names for: {sorted(expected - translated)}"
    )
    assert not translated - expected, (
        f"{path.name} has {domain} names for keys that no longer exist: "
        f"{sorted(translated - expected)}"
    )


@pytest.mark.parametrize("path", TRANSLATION_FILES, ids=lambda p: p.name)
def test_translated_names_are_not_empty(path: Path):
    """An empty name would render as the entity id."""
    translations = json.loads(path.read_text())
    empty = [
        f"{domain}.{key}"
        for domain, entries in translations.get("entity", {}).items()
        for key, entry in entries.items()
        if not entry.get("name")
    ]

    assert not empty, f"{path.name} has empty names: {empty}"


async def test_home_assistant_resolves_every_entity_name(hass):
    """The files are in the format Home Assistant actually looks up.

    A wrong shape does not fail loudly: the lookup misses and every entity
    quietly falls back to the English name in its description.
    """
    from homeassistant.helpers.translation import async_get_translations
    from homeassistant.setup import async_setup_component

    from custom_components.vaillant_plus.const import DOMAIN

    await async_setup_component(hass, DOMAIN, {})

    for language in ("en", "zh"):
        translations = await async_get_translations(
            hass, language, "entity", {DOMAIN}
        )
        if not translations:
            pytest.skip("Home Assistant version does not support entity translations")

        for domain, (module_name, container) in DOMAINS.items():
            for description in _descriptions(module_name, container):
                key = (
                    f"component.{DOMAIN}.entity.{domain}"
                    f".{description.translation_key}.name"
                )
                assert translations.get(key), f"{language}: {key} did not resolve"
