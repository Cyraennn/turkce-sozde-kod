from __future__ import annotations

from .. import ast_nodes as ast
from .base import BaseCodeGenerator
from .registry import register


@register("rust", aliases=["rs"], ext=".rs", display="Rust")
class RustGenerator(BaseCodeGenerator):
    TYPE_NAMES = {"int": "i64", "float": "f64", "str": "String", "bool": "bool"}
    DEFAULT_VALUES = {"int": "0", "float": "0.0", "str": "String::new()", "bool": "false"}
    RESERVED = frozenset({
        "as", "break", "const", "continue", "crate", "else", "enum", "extern", "false", "fn",
        "for", "if", "impl", "in", "let", "loop", "match", "mod", "move", "mut", "pub", "ref",
        "return", "self", "Self", "static", "struct", "super", "trait", "true", "type",
        "unsafe", "use", "where", "while", "async", "await", "dyn", "abstract", "become",
        "box", "do", "final", "macro", "override", "priv", "typeof", "unsized", "virtual",
        "yield", "try", "main", "String",
    })

    def header(self):
        # Gövde başındaki toplu bildirimler "kullanılmayan atama" uyarısı üretir; sustur.
        return ["#![allow(unused)]", "", "fn main() {"]

    def footer(self):
        return ["}"]

    def declaration(self, name, type_):
        return f"let mut {name}: {self.TYPE_NAMES[type_]} = {self.DEFAULT_VALUES[type_]};"

    # Rust'ta "{}" 30.0'ı "30" yazar; "{:?}" (Debug) ise "30.0" ve "3.5" — Python ile aynı.
    @staticmethod
    def placeholder(type_):
        return "{:?}" if type_ == "float" else "{}"

    def stmt_print(self, code, type_):
        return f'println!("{self.placeholder(type_)}", {code});'

    # --- metin birleştirme: zinciri düzleştirip tek biçim dizesi üret ---
    @staticmethod
    def _concat_leaves(node):
        """a + b + "x" + c  →  [a, b, "x", c]. Metin birleştirme birleşmeli olduğundan
        sağdaki parantezli zincirler de güvenle açılır."""
        if isinstance(node, ast.BinaryOp) and node.op == "+" and node.type == "str":
            return RustGenerator._concat_leaves(node.left) + RustGenerator._concat_leaves(node.right)
        return [node]

    def _format_parts(self, node):
        """(biçim dizesi, argüman listesi). Sabit metinler dizenin içine gömülür."""
        fmt, args = [], []
        for leaf in self._concat_leaves(node):
            if isinstance(leaf, ast.Literal) and leaf.kind == "str":
                fmt.append(self.escape(leaf.value).replace("{", "{{").replace("}", "}}"))
            else:
                fmt.append(self.placeholder(leaf.type))
                # format! argümanı ödünç alır; String değişkeni kopyalamaya gerek yok.
                is_var = isinstance(leaf, ast.Identifier)
                args.append(self.name(leaf.name) if is_var else self.expr(leaf))
        return "".join(fmt), args

    @staticmethod
    def _macro(name, fmt, args):
        return f'{name}!("{fmt}"' + "".join(f", {a}" for a in args) + ")"

    def visit_Print(self, node):
        if node.value.type == "str" and isinstance(node.value, (ast.BinaryOp, ast.Literal)):
            # format!/String::from ara adımı olmadan doğrudan println!
            self.line(self._macro("println", *self._format_parts(node.value)) + ";")
        else:
            super().visit_Print(node)

    def binary(self, node):
        if node.op == "+" and node.type == "str":
            return self._macro("format", *self._format_parts(node))
        return super().binary(node)

    def if_open(self, cond):
        return f"if {cond} {{"

    def elif_open(self, cond):
        return f"}} else if {cond} {{"

    def while_open(self, cond):
        return f"while {cond} {{"

    def visit_ForRange(self, node):
        # Diğer C tarzı dillerle aynı semantik: sayaç dış değişkendir.
        var = self.name(node.var)
        self.line(f"{var} = {self.expr(node.start)};")
        self.line(f"while {var} <= {self.expr(node.end)} {{")
        with self.indented():
            self.block(node.body)
            self.line(f"{var} += 1;")
        self.line("}")

    def lit_str(self, value):
        return f'String::from("{self.escape(value)}")'

    def lit_float(self, value):
        return repr(float(value))

    def ident(self, name, type_):
        # String sahipliği taşınmasın diye her okumada kopya.
        return f"{name}.clone()" if type_ == "str" else name

    def coerce_to_float(self, code):
        return f"(({code}) as f64)"
