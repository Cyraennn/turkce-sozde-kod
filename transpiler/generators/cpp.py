from __future__ import annotations

from .base import BaseCodeGenerator
from .registry import register


@register("cpp", aliases=["c++", "cxx"], ext=".cpp", display="C++")
class CppGenerator(BaseCodeGenerator):
    TYPE_NAMES = {"int": "int", "float": "double", "str": "std::string", "bool": "bool"}
    DEFAULT_VALUES = {"int": "0", "float": "0.0", "str": '""', "bool": "false"}
    RESERVED = frozenset({
        "auto", "bool", "break", "case", "char", "class", "const", "continue", "default",
        "delete", "do", "double", "else", "enum", "extern", "false", "float", "for", "goto",
        "if", "int", "long", "main", "namespace", "new", "operator", "private", "protected",
        "public", "return", "short", "signed", "sizeof", "static", "std", "string", "struct",
        "switch", "template", "this", "throw", "true", "try", "typedef", "union", "unsigned",
        "using", "virtual", "void", "volatile", "while", "and", "or", "not", "double_to_str",
    })

    def header(self):
        lines = ["#include <iostream>", "#include <string>"]
        if "double_to_str" in self.imports:
            # cout 30.0'ı "30", std::to_string "30.000000" yazar. Python ile aynı çıktı için:
            # en kısa gösterim (to_chars, C++17) + tam sayıysa ".0" eki → "30.0", "3.5".
            i = self.INDENT
            lines += [
                "#include <charconv>",
                "",
                "std::string double_to_str(double v) {",
                f"{i}char buf[32];",
                f"{i}auto res = std::to_chars(buf, buf + sizeof(buf), v);",
                f"{i}std::string s(buf, res.ptr);",
                f'{i}if (s.find_first_of(".ein") == std::string::npos) s += ".0";',
                f"{i}return s;",
                "}",
            ]
        return lines + ["", "int main() {"]

    def body_prologue(self):
        return ["std::cout << std::boolalpha;"]

    def footer(self):
        return ["", f"{self.INDENT}return 0;", "}"]

    def stmt_print(self, code, type_):
        # << operatörü karşılaştırma ve mantık işleçlerinden sıkı bağlanır:
        # mantıksal sonuçlu bileşik ifadeleri paranteze al (aritmetik zaten güvenli).
        if type_ == "bool" and not (code.isidentifier() or code in (self.TRUE, self.FALSE)):
            code = f"({code})"
        if type_ == "float":
            code = self.to_str(code, "float")
        return f'std::cout << {code} << "\\n";'

    def lit_str(self, value):
        # İki C dizgisi + ile toplanamaz; her metin std::string olur.
        return f'std::string("{self.escape(value)}")'

    def coerce_to_float(self, code):
        return f"static_cast<double>({code})"

    def to_str(self, code, type_):
        if type_ == "str":
            return code
        if type_ == "bool":
            return f'std::string(({code}) ? "true" : "false")'
        if type_ == "float":
            self.imports.add("double_to_str")
            return f"double_to_str({code})"
        return f"std::to_string({code})"
