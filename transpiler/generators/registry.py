"""Dil jeneratörleri için kayıt defteri.

Yeni dil eklemek için:

    @register("kotlin", aliases=["kt"], ext=".kt", display="Kotlin")
    class KotlinGenerator(BaseCodeGenerator):
        ...

ve modülü generators/__init__.py içindeki LANGUAGE_MODULES listesine ekleyin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseCodeGenerator


@dataclass(frozen=True)
class LanguageInfo:
    name: str
    display: str
    ext: str
    aliases: tuple[str, ...]
    cls: type["BaseCodeGenerator"]


_REGISTRY: dict[str, LanguageInfo] = {}   # ana ad -> bilgi
_ALIASES: dict[str, str] = {}             # takma ad / ana ad -> ana ad


def register(name: str, *, ext: str, display: str | None = None, aliases: tuple[str, ...] | list[str] = ()):
    def decorator(cls):
        key = name.lower()
        if key in _REGISTRY:
            raise ValueError(f"'{key}' dili zaten kayıtlı")
        info = LanguageInfo(key, display or name, ext, tuple(a.lower() for a in aliases), cls)
        _REGISTRY[key] = info
        for alias in (key, *info.aliases):
            _ALIASES[alias] = key
        cls.LANG = info
        return cls
    return decorator


def resolve(name: str) -> LanguageInfo:
    key = _ALIASES.get(name.strip().lower())
    if key is None:
        options = ", ".join(_REGISTRY)
        raise KeyError(f"bilinmeyen dil: '{name}'. Seçenekler: {options}")
    return _REGISTRY[key]


def get_generator(name: str) -> "BaseCodeGenerator":
    return resolve(name).cls()


def available_languages() -> list[LanguageInfo]:
    return list(_REGISTRY.values())
