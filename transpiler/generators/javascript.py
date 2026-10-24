from __future__ import annotations

from .base import BaseCodeGenerator
from .registry import register


@register("javascript", aliases=["js", "node"], ext=".js", display="JavaScript")
class JavaScriptGenerator(BaseCodeGenerator):
    BODY_LEVEL = 0
    BINARY_OPS = {**BaseCodeGenerator.BINARY_OPS, "==": "===", "!=": "!=="}
    RESERVED = frozenset({
        "break", "case", "catch", "class", "const", "continue", "debugger", "default",
        "delete", "do", "else", "export", "extends", "false", "finally", "for", "function",
        "if", "import", "in", "instanceof", "let", "new", "null", "return", "super",
        "switch", "this", "throw", "true", "try", "typeof", "var", "void", "while", "with",
        "yield", "await", "enum", "console", "undefined", "NaN", "formatFloat",
    })

    def header(self):
        if "formatFloat" not in self.imports:
            return []
        # JS'te sayılar tek tiptir: 30.0 "30" yazılır. Python ile aynı "30.0" için:
        return [
            "function formatFloat(v) {",
            f"{self.INDENT}return Number.isInteger(v) ? v.toFixed(1) : String(v);",
            "}",
            "",
        ]

    def declaration(self, name, type_):
        return f"let {name} = {self.DEFAULT_VALUES[type_]};"

    def stmt_print(self, code, type_):
        if type_ == "float":
            code = self.to_str(code, "float")
        return f"console.log({code});"

    def string_equals(self, l, r, negate):
        return f"{l} {'!==' if negate else '==='} {r}"

    def to_str(self, code, type_):
        if type_ == "float":
            self.imports.add("formatFloat")
            return f"formatFloat({code})"
        return code  # JS + işleci diğer tipleri metne kendisi çevirir
