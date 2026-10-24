from __future__ import annotations

from .base import BaseCodeGenerator
from .registry import register


@register("go", aliases=["golang"], ext=".go", display="Go")
class GoGenerator(BaseCodeGenerator):
    END = ""
    INDENT = "\t"  # gofmt standardı
    TYPE_NAMES = {"int": "int", "float": "float64", "str": "string", "bool": "bool"}
    RESERVED = frozenset({
        "break", "case", "chan", "const", "continue", "default", "defer", "else",
        "fallthrough", "for", "func", "go", "goto", "if", "import", "interface", "map",
        "package", "range", "return", "select", "struct", "switch", "type", "var",
        "fmt", "main", "int", "float64", "string", "bool", "true", "false", "nil",
        "len", "append", "make", "new", "strconv", "strings", "formatFloat",
    })

    def header(self):
        lines = ["package main", ""]
        pkgs = sorted(p for p in self.imports if p in ("fmt", "strconv", "strings"))
        if len(pkgs) == 1:
            lines += [f'import "{pkgs[0]}"', ""]
        elif pkgs:
            lines += ["import ("] + [f'\t"{p}"' for p in pkgs] + [")", ""]
        if "formatFloat" in self.imports:
            # fmt 30.0'ı "30" yazar. Python ile aynı "30.0" için en kısa gösterim + ".0".
            lines += [
                "func formatFloat(v float64) string {",
                "\ts := strconv.FormatFloat(v, 'f', -1, 64)",
                '\tif !strings.ContainsAny(s, ".IN") {',
                '\t\ts += ".0"',
                "\t}",
                "\treturn s",
                "}",
                "",
            ]
        return lines + ["func main() {"]

    def footer(self):
        return ["}"]

    def declaration(self, name, type_):
        return f"var {name} {self.TYPE_NAMES[type_]}"  # Go sıfır değerle başlatır

    def after_declarations(self):
        # Go, kullanılmayan değişkeni derleme hatası sayar.
        return [f"_ = {self.name(n)}" for n in self.symbols]

    def stmt_print(self, code, type_):
        self.imports.add("fmt")
        if type_ == "float":
            code = self.to_str(code, "float")
        return f"fmt.Println({code})"

    def if_open(self, cond):
        return f"if {cond} {{"

    def elif_open(self, cond):
        return f"}} else if {cond} {{"

    def for_open(self, var, start, end):
        return f"for {var} = {start}; {var} <= {end}; {var}++ {{"

    def while_open(self, cond):
        return f"for {cond} {{"

    def coerce_to_float(self, code):
        return f"float64({code})"

    def to_str(self, code, type_):
        if type_ == "str":
            return code
        if type_ == "float":
            self.imports.update({"formatFloat", "strconv", "strings"})
            return f"formatFloat({code})"
        self.imports.add("fmt")
        return f"fmt.Sprint({code})"
