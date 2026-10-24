from __future__ import annotations

from .base import BaseCodeGenerator
from .registry import register


@register("java", ext=".java", display="Java")
class JavaGenerator(BaseCodeGenerator):
    BODY_LEVEL = 2
    TYPE_NAMES = {"int": "int", "float": "double", "str": "String", "bool": "boolean"}
    RESERVED = frozenset({
        "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class",
        "const", "continue", "default", "do", "double", "else", "enum", "extends", "final",
        "finally", "float", "for", "goto", "if", "implements", "import", "instanceof", "int",
        "interface", "long", "native", "new", "package", "private", "protected", "public",
        "return", "short", "static", "strictfp", "super", "switch", "synchronized", "this",
        "throw", "throws", "transient", "try", "void", "volatile", "while", "true", "false",
        "null", "var", "record", "yield", "args", "Main", "String", "System",
    })

    def header(self):
        return ["public class Main {", f"{self.INDENT}public static void main(String[] args) {{"]

    def footer(self):
        return [f"{self.INDENT}}}", "}"]

    def stmt_print(self, code, type_):
        return f"System.out.println({code});"

    def coerce_to_float(self, code):
        return f"((double) ({code}))"

    def string_equals(self, l, r, negate):
        # Java'da == metinlerde referans karşılaştırır; içerik için equals gerekir.
        if not (l.isidentifier() or l.startswith('"')):
            l = f"({l})"
        return f"{'!' if negate else ''}{l}.equals({r})"
