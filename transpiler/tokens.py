"""Simge (token) tanımları."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    KEYWORD = auto()      # eğer, ise, değilse, bitir, yazdır, döngü, için, ve, veya, değil
    IDENTIFIER = auto()   # değişken adları
    OPERATOR = auto()     # + - * / % == != < > <= >= = ( ) ,
    NUMBER = auto()       # LITERAL: 5, 3.14
    STRING = auto()       # LITERAL: "metin"
    BOOL = auto()         # LITERAL: doğru / yanlış
    NEWLINE = auto()      # deyim ayırıcı
    EOF = auto()


KEYWORDS = frozenset({
    "eğer", "ise", "değilse", "bitir",
    "yazdır",
    "döngü", "için",
    "ve", "veya", "değil",
})

BOOL_LITERALS = {"doğru": True, "yanlış": False}

# Uzun operatörler önce denenir (">=" , ">" den önce).
OPERATORS = ("==", "!=", "<=", ">=", "+", "-", "*", "/", "%", "<", ">", "=", "(", ")", ",")

LITERAL_TYPES = frozenset({TokenType.NUMBER, TokenType.STRING, TokenType.BOOL})


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: Any
    line: int
    col: int

    def is_keyword(self, word: str) -> bool:
        return self.type is TokenType.KEYWORD and self.value == word

    def is_op(self, op: str) -> bool:
        return self.type is TokenType.OPERATOR and self.value == op

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"
