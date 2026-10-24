"""Soyut Sözdizimi Ağacı (AST) düğümleri.

Tipler: "int", "float", "str", "bool". İfade düğümlerinin `type` alanını
anlamsal analiz (semantic.py) doldurur.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    line: int = field(default=0, kw_only=True, compare=False)


# --- İfadeler ---------------------------------------------------------
@dataclass
class Expr(Node):
    type: str | None = field(default=None, kw_only=True, compare=False)


@dataclass
class Literal(Expr):
    value: int | float | str | bool
    kind: str  # "int" | "float" | "str" | "bool"


@dataclass
class Identifier(Expr):
    name: str


@dataclass
class BinaryOp(Expr):
    op: str  # + - * / % == != < > <= >= ve veya
    left: Expr
    right: Expr


@dataclass
class UnaryOp(Expr):
    op: str  # "-" | "değil"
    operand: Expr


# --- Deyimler ---------------------------------------------------------
@dataclass
class Stmt(Node):
    pass


@dataclass
class Assign(Stmt):
    name: str
    value: Expr


@dataclass
class Print(Stmt):
    value: Expr


@dataclass
class If(Stmt):
    # [(koşul, gövde), ...] — ilki "eğer", kalanlar "değilse eğer"
    branches: list[tuple[Expr, list[Stmt]]]
    else_body: list[Stmt] | None = None


@dataclass
class ForRange(Stmt):
    var: str
    start: Expr
    end: Expr  # dahil
    body: list[Stmt]


@dataclass
class While(Stmt):
    cond: Expr
    body: list[Stmt]


@dataclass
class Program(Node):
    body: list[Stmt]
