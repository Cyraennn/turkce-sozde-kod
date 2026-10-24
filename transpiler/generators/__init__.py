"""Kod jeneratörleri. Modüller içe aktarılınca @register ile kendilerini kaydeder."""

from importlib import import_module

from .base import BaseCodeGenerator
from .registry import LanguageInfo, available_languages, get_generator, register, resolve

# Yeni dil eklerken buraya modül adını yazmanız yeterli.
LANGUAGE_MODULES = ["cpp", "python", "dart", "java", "rust", "go", "javascript"]

for _mod in LANGUAGE_MODULES:
    import_module(f"{__name__}.{_mod}")

__all__ = ["BaseCodeGenerator", "LanguageInfo", "available_languages", "get_generator",
           "register", "resolve", "LANGUAGE_MODULES"]
