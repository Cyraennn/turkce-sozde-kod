"""Anlamsal analiz: tip çıkarımı ve değişken tablosu.

Statik tipli hedef diller (C++, Java, Rust, Go, Dart) her değişkenin tipini
bilmek zorunda. Bu modül AST'yi gezer, her ifadeye `.type` yazar ve
{değişken_adı: tip} tablosunu üretir.

Tip genişletme: bir değişkene önce int, sonra float atanırsa değişken float
olur. Bu yüzden analiz, tablo değişmeyene kadar tekrarlanır (sabit nokta).
"""

from __future__ import annotations

from . import ast_nodes as ast
from .errors import SemanticError

NUMERIC = frozenset({"int", "float"})
ARITHMETIC = frozenset({"+", "-", "*", "/", "%"})
EQUALITY = frozenset({"==", "!="})
ORDERING = frozenset({"<", ">", "<=", ">="})
LOGICAL = frozenset({"ve", "veya"})

TYPE_LABELS = {"int": "tam sayı", "float": "ondalık", "str": "metin", "bool": "mantıksal"}


def _label(t: str) -> str:
    return TYPE_LABELS.get(t, t)


def binary_result_type(op: str, left: str, right: str, line: int = 0) -> str:
    """İkili bir işlemin sonuç tipini belirler; geçersizse SemanticError fırlatır."""
    if op in LOGICAL:
        if left == right == "bool":
            return "bool"
        raise SemanticError(f"'{op}' yalnızca mantıksal değerlerle kullanılabilir "
                            f"({_label(left)} {op} {_label(right)})", line)

    if op in EQUALITY:
        if left == right or (left in NUMERIC and right in NUMERIC):
            return "bool"
        raise SemanticError(f"{_label(left)} ile {_label(right)} karşılaştırılamaz", line)

    if op in ORDERING:
        if left in NUMERIC and right in NUMERIC:
            return "bool"
        raise SemanticError(f"'{op}' yalnızca sayılarla kullanılabilir "
                            f"({_label(left)} {op} {_label(right)})", line)

    if op == "+" and "str" in (left, right):
        # Esnek politika: metin + herhangi bir tip → metin. Örn. yazdır "Puan: " + 5
        # Sayı/mantıksal taraf jeneratörlerde otomatik metne çevrilir
        # (C++ yardımcı fonksiyon, Python str(), Go fmt.Sprint, Rust format!, Dart toString()).
        return "str"

    if left in NUMERIC and right in NUMERIC:
        if op == "%":
            if left == right == "int":
                return "int"
            raise SemanticError("'%' yalnızca tam sayılarla kullanılabilir", line)
        if op == "/":
            return "float"  # 7 / 2 her dilde 3.5 olsun
        return "float" if "float" in (left, right) else "int"

    raise SemanticError(f"'{op}' işlemi {_label(left)} ve {_label(right)} için tanımlı değil", line)


def unify(old: str, new: str, name: str, line: int) -> str:
    """Bir değişkene yeni tipte değer atanırken birleşik tipi döndürür."""
    if old == new:
        return old
    if old in NUMERIC and new in NUMERIC:
        return "float"
    raise SemanticError(f"'{name}' değişkeni {_label(old)} tipinde; "
                        f"{_label(new)} atanamaz", line)


class Analyzer:
    MAX_PASSES = 10

    def __init__(self) -> None:
        self.symbols: dict[str, str] = {}
        self._defined: set[str] = set()

    def analyze(self, program: ast.Program) -> dict[str, str]:
        for _ in range(self.MAX_PASSES):
            before = dict(self.symbols)
            self._defined = set()
            self._block(program.body)
            if self.symbols == before:
                break
        return self.symbols

    # --- deyimler ----------------------------------------------------
    def _block(self, body: list[ast.Stmt]) -> None:
        for stmt in body:
            self._stmt(stmt)

    def _stmt(self, s: ast.Stmt) -> None:
        if isinstance(s, ast.Assign):
            t = self._expr(s.value)
            if s.name in self.symbols:
                t = unify(self.symbols[s.name], t, s.name, s.line)
            self.symbols[s.name] = t
            self._defined.add(s.name)
        elif isinstance(s, ast.Print):
            self._expr(s.value)
        elif isinstance(s, ast.If):
            for cond, body in s.branches:
                self._require_bool(cond, "'eğer' koşulu")
                self._block(body)
            if s.else_body is not None:
                self._block(s.else_body)
        elif isinstance(s, ast.ForRange):
            for part, what in ((s.start, "başlangıç"), (s.end, "bitiş")):
                if self._expr(part) != "int":
                    raise SemanticError(f"döngü {what} değeri tam sayı olmalı", s.line)
            old = self.symbols.get(s.var)
            if old is not None and old != "int":
                raise SemanticError(f"döngü sayacı '{s.var}' daha önce {_label(old)} olarak "
                                    f"tanımlanmış", s.line)
            self.symbols[s.var] = "int"
            self._defined.add(s.var)
            self._block(s.body)
        elif isinstance(s, ast.While):
            self._require_bool(s.cond, "döngü koşulu")
            self._block(s.body)
        else:  # pragma: no cover
            raise SemanticError(f"bilinmeyen deyim: {type(s).__name__}", s.line)

    def _require_bool(self, cond: ast.Expr, what: str) -> None:
        if self._expr(cond) != "bool":
            raise SemanticError(f"{what} mantıksal (doğru/yanlış) olmalı, "
                                f"{_label(cond.type)} bulundu", cond.line)

    # --- ifadeler ----------------------------------------------------
    def _expr(self, e: ast.Expr) -> str:
        if isinstance(e, ast.Literal):
            e.type = e.kind
        elif isinstance(e, ast.Identifier):
            if e.name not in self._defined:
                raise SemanticError(f"'{e.name}' tanımlanmadan kullanıldı", e.line)
            e.type = self.symbols[e.name]
        elif isinstance(e, ast.UnaryOp):
            t = self._expr(e.operand)
            if e.op == "-" and t not in NUMERIC:
                raise SemanticError(f"'-' {_label(t)} değere uygulanamaz", e.line)
            if e.op == "değil" and t != "bool":
                raise SemanticError(f"'değil' {_label(t)} değere uygulanamaz", e.line)
            e.type = t
        elif isinstance(e, ast.BinaryOp):
            lt = self._expr(e.left)
            rt = self._expr(e.right)
            e.type = binary_result_type(e.op, lt, rt, e.line)
        else:  # pragma: no cover
            raise SemanticError(f"bilinmeyen ifade: {type(e).__name__}", e.line)
        return e.type


def analyze(program: ast.Program) -> dict[str, str]:
    return Analyzer().analyze(program)
