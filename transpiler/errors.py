"""Transpiler hata sınıfları. Tüm mesajlar Türkçe ve konum bilgilidir."""

from __future__ import annotations


class TranspileError(Exception):
    """Tüm dönüştürücü hatalarının ortak atası."""

    kind = "Hata"

    def __init__(self, message: str, line: int | None = None, col: int | None = None):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(str(self))

    def __str__(self) -> str:
        where = ""
        if self.line is not None:
            where = f"Satır {self.line}"
            if self.col is not None:
                where += f", sütun {self.col}"
            where += ": "
        return f"{self.kind} — {where}{self.message}"


class LexerError(TranspileError):
    kind = "Sözcük hatası"


class ParseError(TranspileError):
    kind = "Sözdizimi hatası"


class SemanticError(TranspileError):
    kind = "Anlam hatası"
