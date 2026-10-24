from __future__ import annotations

import keyword

from .base import BaseCodeGenerator
from .registry import register


@register("python", aliases=["py", "python3"], ext=".py", display="Python")
class PythonGenerator(BaseCodeGenerator):
    BODY_LEVEL = 0
    END = ""
    TRUE, FALSE = "True", "False"
    BINARY_OPS = {**BaseCodeGenerator.BINARY_OPS, "ve": "and", "veya": "or"}
    UNARY_OPS = {"-": "-", "değil": "not"}
    RESERVED = frozenset(keyword.kwlist) | frozenset({"print", "range", "str", "int", "float", "bool"})

    def declaration(self, name, type_):
        return None  # Python'da bildirim yok

    def empty_block(self):
        return "pass"

    def stmt_print(self, code, type_):
        if type_ == "bool":
            # Diğer dillerle aynı çıktı: True → true
            return f"print(str({code}).lower())"
        return f"print({code})"

    def if_open(self, cond):
        return f"if {cond}:"

    def elif_open(self, cond):
        return f"elif {cond}:"

    def else_open(self):
        return "else:"

    def block_close(self):
        return None

    def while_open(self, cond):
        return f"while {cond}:"

    def visit_ForRange(self, node):
        from .. import ast_nodes as ast
        end = node.end
        if isinstance(end, ast.Literal):
            stop = str(end.value + 1)
        else:
            stop = f"{self.expr(end)} + 1"
        self.line(f"for {self.name(node.var)} in range({self.expr(node.start)}, {stop}):")
        with self.indented():
            self.block(node.body)

    def to_str(self, code, type_):
        if type_ == "str":
            return code
        if type_ == "bool":
            return f"str({code}).lower()"
        return f"str({code})"
