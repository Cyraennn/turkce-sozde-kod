"""BaseCodeGenerator: tüm dil jeneratörlerinin ortak iskeleti.

Tasarım: Template Method + Visitor.
  * AST'nin gezilmesi, girinti, parantezleme, tip dönüşümü (coercion) ve
    isim güvenliği burada BİR KEZ yazılır.
  * Alt sınıflar yalnızca dile özgü küçük parçaları (tablolar ve kancalar)
    doldurur. Çoğu dil 50-80 satırda tamamlanır.

Kanca özeti (alt sınıfta ezilebilir):
    header()/footer()            dosya başı/sonu (include, import, main açılışı)
    body_prologue()              gövdenin ilk satırları
    declaration(name, type)      değişken bildirimi (None → bildirim yok)
    stmt_print(code, type)       yazdır
    stmt_assign(name, code)      atama
    if_open/elif_open/else_open/block_close
    for_open(var, start, end)    sayaç döngüsü (C tarzı varsayılan)
    while_open(cond)
    lit_str/lit_bool/lit_int/lit_float, ident(name, type)
    coerce_to_float(code)        int → float dönüşümü
    to_str(code, type)           metin birleştirme için dönüşüm
    concat(l, lt, r, rt)         metin birleştirme
    string_equals(l, r, negate)  metin eşitliği
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import ClassVar

from .. import ast_nodes as ast
from ..semantic import EQUALITY, ORDERING

# Ortak öncelik tablosu (büyük = sıkı bağlanır). Tüm hedef dillerde sıralama aynı.
PRECEDENCE = {
    "veya": 1, "ve": 2, "değil": 3,
    "==": 4, "!=": 4, "<": 4, ">": 4, "<=": 4, ">=": 4,
    "+": 5, "-": 5,
    "*": 6, "/": 6, "%": 6,
}
UNARY_MINUS_PREC = 7
ATOM_PREC = 8

_TRANSLIT = str.maketrans({
    "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
    "Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U",
    "â": "a", "î": "i", "û": "u",
})


class BaseCodeGenerator:
    LANG: ClassVar = None  # @register doldurur (LanguageInfo)

    INDENT: ClassVar[str] = "    "
    BODY_LEVEL: ClassVar[int] = 1          # gövde kaç seviye içeride (main içi = 1)
    RESERVED: ClassVar[frozenset[str]] = frozenset()

    BINARY_OPS: ClassVar[dict[str, str]] = {
        "+": "+", "-": "-", "*": "*", "/": "/", "%": "%",
        "==": "==", "!=": "!=", "<": "<", ">": ">", "<=": "<=", ">=": ">=",
        "ve": "&&", "veya": "||",
    }
    UNARY_OPS: ClassVar[dict[str, str]] = {"-": "-", "değil": "!"}
    TYPE_NAMES: ClassVar[dict[str, str]] = {"int": "int", "float": "double", "str": "string", "bool": "bool"}
    DEFAULT_VALUES: ClassVar[dict[str, str]] = {"int": "0", "float": "0.0", "str": '""', "bool": "false"}
    TRUE: ClassVar[str] = "true"
    FALSE: ClassVar[str] = "false"
    END: ClassVar[str] = ";"               # deyim sonu

    # ================================================================
    # Ana giriş noktası (Template Method)
    # ================================================================
    def generate(self, program: ast.Program, symbols: dict[str, str]) -> str:
        self.symbols = dict(symbols)
        self.names = self._build_name_map(symbols)
        self.imports: set[str] = set()
        self._lines: list[str] = []
        self._level = self.BODY_LEVEL

        for text in self.body_prologue():
            self.line(text)
        self.declare_variables()
        self.block(program.body)
        for text in self.body_epilogue():
            self.line(text)

        body = self._lines
        # header() en son çağrılır: gövde hangi import'lara ihtiyaç duyduğunu bildirmiş olur.
        out = self.header() + body + self.footer()
        return "\n".join(out).rstrip() + "\n"

    # ================================================================
    # Çıktı yardımcıları
    # ================================================================
    def line(self, text: str = "") -> None:
        self._lines.append(self.INDENT * self._level + text if text else "")

    @contextmanager
    def indented(self):
        self._level += 1
        try:
            yield
        finally:
            self._level -= 1

    def block(self, body: list[ast.Stmt]) -> None:
        if not body:
            empty = self.empty_block()
            if empty:
                self.line(empty)
        for stmt in body:
            self.visit(stmt)

    def visit(self, node: ast.Stmt) -> None:
        method = getattr(self, f"visit_{type(node).__name__}", None)
        if method is None:
            raise NotImplementedError(f"{type(self).__name__}: {type(node).__name__} desteklenmiyor")
        method(node)

    # ================================================================
    # İsim güvenliği
    # ================================================================
    def safe_name(self, name: str) -> str:
        ascii_name = name.translate(_TRANSLIT)
        ascii_name = "".join(ch if (ch.isascii() and (ch.isalnum() or ch == "_")) else "_" for ch in ascii_name)
        if ascii_name in self.RESERVED:
            ascii_name += "_"
        return ascii_name

    def _build_name_map(self, symbols: dict[str, str]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        used: set[str] = set()
        for original in symbols:
            candidate = base = self.safe_name(original)
            n = 2
            while candidate in used:  # "sayaç" ve "sayac" çakışırsa
                candidate = f"{base}_{n}"
                n += 1
            used.add(candidate)
            mapping[original] = candidate
        return mapping

    def name(self, original: str) -> str:
        return self.names.get(original) or self.safe_name(original)

    # ================================================================
    # Deyim ziyaretçileri (ortak)
    # ================================================================
    def declare_variables(self) -> None:
        emitted = False
        for original, type_ in self.symbols.items():
            decl = self.declaration(self.name(original), type_)
            if decl:
                self.line(decl)
                emitted = True
        for text in self.after_declarations():
            self.line(text)
            emitted = True
        if emitted:
            self.line()

    def visit_Assign(self, node: ast.Assign) -> None:
        code = self.expr(node.value)
        target_type = self.symbols.get(node.name)
        if target_type == "float" and node.value.type == "int":
            code = self.coerce_to_float(code)
        self.line(self.stmt_assign(self.name(node.name), code))

    def visit_Print(self, node: ast.Print) -> None:
        self.line(self.stmt_print(self.expr(node.value), node.value.type))

    def visit_If(self, node: ast.If) -> None:
        for i, (cond, body) in enumerate(node.branches):
            c = self.expr(cond)
            self.line(self.if_open(c) if i == 0 else self.elif_open(c))
            with self.indented():
                self.block(body)
        if node.else_body is not None:
            self.line(self.else_open())
            with self.indented():
                self.block(node.else_body)
        self._close()

    def visit_ForRange(self, node: ast.ForRange) -> None:
        self.line(self.for_open(self.name(node.var), self.expr(node.start), self.expr(node.end)))
        with self.indented():
            self.block(node.body)
        self._close()

    def visit_While(self, node: ast.While) -> None:
        self.line(self.while_open(self.expr(node.cond)))
        with self.indented():
            self.block(node.body)
        self._close()

    def _close(self) -> None:
        close = self.block_close()
        if close:
            self.line(close)

    # ================================================================
    # İfadeler (ortak)
    # ================================================================
    def expr(self, node: ast.Expr) -> str:
        if isinstance(node, ast.Literal):
            return {
                "int": self.lit_int, "float": self.lit_float,
                "str": self.lit_str, "bool": self.lit_bool,
            }[node.kind](node.value)
        if isinstance(node, ast.Identifier):
            return self.ident(self.name(node.name), node.type)
        if isinstance(node, ast.UnaryOp):
            operand = self.expr(node.operand)
            if isinstance(node.operand, (ast.BinaryOp, ast.UnaryOp)):
                operand = f"({operand})"
            return self.unary(node.op, operand)
        if isinstance(node, ast.BinaryOp):
            return self.binary(node)
        raise NotImplementedError(type(node).__name__)

    @staticmethod
    def precedence(node: ast.Expr) -> int:
        if isinstance(node, ast.BinaryOp):
            return PRECEDENCE[node.op]
        if isinstance(node, ast.UnaryOp):
            return PRECEDENCE["değil"] if node.op == "değil" else UNARY_MINUS_PREC
        return ATOM_PREC

    def operand(self, child: ast.Expr, parent: ast.BinaryOp, is_right: bool) -> str:
        """Alt ifadeyi üretir; öncelik gerektiriyorsa parantez ekler."""
        code = self.expr(child)
        cp, pp = self.precedence(child), PRECEDENCE[parent.op]
        # Karşılaştırmalar birleşmez (Python'da a < b == c zincir olur), sağ taraf için de parantez.
        if cp < pp or (cp == pp and (is_right or pp == PRECEDENCE["=="])):
            code = f"({code})"
        return code

    def binary(self, node: ast.BinaryOp) -> str:
        op, lt, rt = node.op, node.left.type, node.right.type
        l = self.operand(node.left, node, is_right=False)
        r = self.operand(node.right, node, is_right=True)

        if op == "+" and node.type == "str":
            return self.concat(l, lt, r, rt)

        # Sayısal karışık işlemlerde int tarafı float'a çevrilir (Rust/Go zorunlu kılar,
        # C++/Java'da da 7/2 = 3.5 olması için gerekli).
        needs_float = (node.type == "float") or (
            (op in EQUALITY or op in ORDERING) and {lt, rt} == {"int", "float"})
        if needs_float:
            if lt == "int":
                l = self.coerce_to_float(l)
            if rt == "int":
                r = self.coerce_to_float(r)

        if op in EQUALITY and lt == "str":
            return self.string_equals(l, r, negate=(op == "!="))
        return f"{l} {self.BINARY_OPS[op]} {r}"

    def unary(self, op: str, operand: str) -> str:
        sym = self.UNARY_OPS[op]
        sep = " " if sym[-1].isalpha() else ""
        return f"{sym}{sep}{operand}"

    # ================================================================
    # Varsayılan kancalar (C ailesi). Alt sınıflar gerekeni ezer.
    # ================================================================
    def header(self) -> list[str]:
        return []

    def footer(self) -> list[str]:
        return []

    def body_prologue(self) -> list[str]:
        return []

    def body_epilogue(self) -> list[str]:
        return []

    def after_declarations(self) -> list[str]:
        return []

    def empty_block(self) -> str | None:
        return None

    def declaration(self, name: str, type_: str) -> str | None:
        return f"{self.TYPE_NAMES[type_]} {name} = {self.DEFAULT_VALUES[type_]}{self.END}"

    def stmt_assign(self, name: str, code: str) -> str:
        return f"{name} = {code}{self.END}"

    def stmt_print(self, code: str, type_: str) -> str:  # pragma: no cover - soyut
        raise NotImplementedError

    def if_open(self, cond: str) -> str:
        return f"if ({cond}) {{"

    def elif_open(self, cond: str) -> str:
        return f"}} else if ({cond}) {{"

    def else_open(self) -> str:
        return "} else {"

    def block_close(self) -> str | None:
        return "}"

    def for_open(self, var: str, start: str, end: str) -> str:
        return f"for ({var} = {start}; {var} <= {end}; {var}++) {{"

    def while_open(self, cond: str) -> str:
        return f"while ({cond}) {{"

    # --- literaller ve isimler ---
    def lit_int(self, value: int) -> str:
        return str(value)

    def lit_float(self, value: float) -> str:
        return repr(float(value))

    def lit_bool(self, value: bool) -> str:
        return self.TRUE if value else self.FALSE

    def lit_str(self, value: str) -> str:
        return '"' + self.escape(value) + '"'

    @staticmethod
    def escape(value: str) -> str:
        return (value.replace("\\", "\\\\").replace('"', '\\"')
                .replace("\n", "\\n").replace("\t", "\\t"))

    def ident(self, name: str, type_: str | None) -> str:
        return name

    # --- tip işlemleri ---
    def coerce_to_float(self, code: str) -> str:
        return code

    def to_str(self, code: str, type_: str) -> str:
        return code

    def concat(self, l: str, lt: str, r: str, rt: str) -> str:
        return f"{self.to_str(l, lt)} + {self.to_str(r, rt)}"

    def string_equals(self, l: str, r: str, negate: bool) -> str:
        return f"{l} {'!=' if negate else '=='} {r}"
