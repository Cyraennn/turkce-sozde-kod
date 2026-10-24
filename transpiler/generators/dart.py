from __future__ import annotations

from .base import BaseCodeGenerator
from .registry import register


@register("dart", ext=".dart", display="Dart")
class DartGenerator(BaseCodeGenerator):
    TYPE_NAMES = {"int": "int", "float": "double", "str": "String", "bool": "bool"}
    RESERVED = frozenset({
        "abstract", "as", "assert", "async", "await", "break", "case", "catch", "class",
        "const", "continue", "covariant", "default", "deferred", "do", "dynamic", "else",
        "enum", "export", "extends", "extension", "external", "factory", "false", "final",
        "finally", "for", "Function", "get", "hide", "if", "implements", "import", "in",
        "interface", "is", "late", "library", "mixin", "new", "null", "on", "operator",
        "part", "required", "rethrow", "return", "set", "show", "static", "super", "switch",
        "sync", "this", "throw", "true", "try", "typedef", "var", "void", "while", "with",
        "yield", "int", "double", "String", "bool", "print", "main",
    })

    def header(self):
        return ["void main() {"]

    def footer(self):
        return ["}"]

    def stmt_print(self, code, type_):
        return f"print({code});"

    @staticmethod
    def escape(value):
        # Dart metinlerinde $ değişken yerleştirme başlatır.
        return BaseCodeGenerator.escape(value).replace("$", "\\$")

    def coerce_to_float(self, code):
        return f"({code}).toDouble()"

    def to_str(self, code, type_):
        return code if type_ == "str" else f"({code}).toString()"
