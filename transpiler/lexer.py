"""Lexer: kaynak metni simge (token) listesine çevirir."""

from __future__ import annotations

import unicodedata

from .errors import LexerError
from .tokens import BOOL_LITERALS, KEYWORDS, OPERATORS, Token, TokenType

_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


class Lexer:
    def __init__(self, source: str):
        # NFC: "ğ" gibi harflerin birleşik (combining) yazımlarını tek karaktere indirir.
        self.src = unicodedata.normalize("NFC", source).replace("\r\n", "\n").replace("\r", "\n")
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    # --- yardımcılar -------------------------------------------------
    def _peek(self, offset: int = 0) -> str:
        i = self.pos + offset
        return self.src[i] if i < len(self.src) else ""

    def _advance(self) -> str:
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _add(self, type_: TokenType, value, line: int, col: int) -> None:
        self.tokens.append(Token(type_, value, line, col))

    # --- ana döngü ---------------------------------------------------
    def tokenize(self) -> list[Token]:
        while self.pos < len(self.src):
            ch = self._peek()
            line, col = self.line, self.col

            if ch == "\n":
                self._advance()
                # Ardışık boş satırlar tek NEWLINE olur.
                if self.tokens and self.tokens[-1].type is not TokenType.NEWLINE:
                    self._add(TokenType.NEWLINE, "\n", line, col)
            elif ch.isspace():
                self._advance()
            elif ch == "#":
                while self.pos < len(self.src) and self._peek() != "\n":
                    self._advance()
            elif ch.isdigit():
                self._number(line, col)
            elif ch == '"':
                self._string(line, col)
            elif ch.isalpha() or ch == "_":
                self._word(line, col)
            else:
                self._operator(line, col)

        if self.tokens and self.tokens[-1].type is not TokenType.NEWLINE:
            self._add(TokenType.NEWLINE, "\n", self.line, self.col)
        self._add(TokenType.EOF, None, self.line, self.col)
        return self.tokens

    def _number(self, line: int, col: int) -> None:
        start = self.pos
        while self._peek().isdigit():
            self._advance()
        is_float = False
        if self._peek() == "." and self._peek(1).isdigit():
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()
        if self._peek().isalpha() or self._peek() == "_":
            raise LexerError(f"geçersiz sayı: '{self.src[start:self.pos + 1]}'", line, col)
        text = self.src[start:self.pos]
        self._add(TokenType.NUMBER, float(text) if is_float else int(text), line, col)

    def _string(self, line: int, col: int) -> None:
        self._advance()  # açılış tırnağı
        chars: list[str] = []
        while True:
            ch = self._peek()
            if ch == "" or ch == "\n":
                raise LexerError("kapanmamış metin (\" eksik)", line, col)
            self._advance()
            if ch == '"':
                break
            if ch == "\\":
                esc = self._peek()
                if esc not in _ESCAPES:
                    raise LexerError(f"bilinmeyen kaçış dizisi: '\\{esc}'", self.line, self.col)
                self._advance()
                chars.append(_ESCAPES[esc])
            else:
                chars.append(ch)
        self._add(TokenType.STRING, "".join(chars), line, col)

    def _word(self, line: int, col: int) -> None:
        start = self.pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        word = self.src[start:self.pos]
        if word in KEYWORDS:
            self._add(TokenType.KEYWORD, word, line, col)
        elif word in BOOL_LITERALS:
            self._add(TokenType.BOOL, BOOL_LITERALS[word], line, col)
        else:
            self._add(TokenType.IDENTIFIER, word, line, col)

    def _operator(self, line: int, col: int) -> None:
        for op in OPERATORS:
            if self.src.startswith(op, self.pos):
                for _ in op:
                    self._advance()
                self._add(TokenType.OPERATOR, op, line, col)
                return
        raise LexerError(f"beklenmeyen karakter: '{self._peek()}'", line, col)


def tokenize(source: str) -> list[Token]:
    return Lexer(source).tokenize()
