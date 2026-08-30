"""Compatibility helpers for the Home Assistant versions this integration supports."""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, TypeVar

T = TypeVar("T")


def supports_translation_key(description_class: Any) -> bool:
    """Return True if entity descriptions accept a `translation_key`."""
    return any(field.name == "translation_key" for field in fields(description_class))


def with_translation_key(description_class: T) -> T:
    """Return a description class that accepts a `translation_key`.

    `EntityDescription.translation_key` was added in Home Assistant 2023.1, and
    entity *names* are only translated from 2023.7 on. Older releases raise
    ``TypeError: __init__() got an unexpected keyword argument
    'translation_key'`` when a description passes one, which would stop the
    integration from loading at all.

    On those releases, return a subclass that accepts the argument and ignores
    it; nothing reads it, and the English `name` on the description is used, as
    it is on every release that has no entity name translations.
    """
    if supports_translation_key(description_class):
        return description_class

    @dataclass
    class _TranslatableDescription(description_class):  # type: ignore[valid-type,misc]
        translation_key: str | None = None

    _TranslatableDescription.__name__ = description_class.__name__
    _TranslatableDescription.__qualname__ = description_class.__qualname__
    return _TranslatableDescription  # type: ignore[return-value]
