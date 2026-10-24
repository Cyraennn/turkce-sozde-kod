"""Özyinelemeli iniş (recursive descent) parser.

Dilbilgisi (EBNF):
    program     := { NEWLINE | deyim } EOF
    deyim       := yazdir | atama | eger | dongu
    yazdir      := "yazdır" ifade NEWLINE
    atama       := IDENT "=" ifade NEWLINE
    eger        := "eğer" ifade "ise" NEWLINE blok
                   { "değilse" "eğer" ifade "ise" NEWLINE blok }
                   [ "değilse" NEWLINE blok ] "bitir"
    dongu       := "döngü" ( IDENT "=" ifade "," ifade | ifade ) "için" NEWLINE blok "bitir"
    ifade       := veya
    veya        := ve { "veya" ve }
    ve          := degil { "ve" degil }
    degil       := "değil" degil | karsilastir
    karsilastir := toplama [ ("=="|"!="|"<"|">"|"<="|">=") toplama ]
    toplama     := carpma { ("+"|"-") carpma }
    carpma      := tekli { ("*"|"/"|"%") tekli }
    tekli       := "-" tekli | birincil
    birincil    := SAYI | METIN | MANTIKSAL | IDENT | "(" ifade ")"
"""

from __future__ import annotations

from . import ast_nodes as ast
from .errors import ParseError
from .tokens import Token, TokenType

_COMPARISON = ("==", "!=", "<", ">", "<=", ">=")
_BLOCK_END = ("değilse", "bitir")


def _describe(tok: Token) -> str:
    if tok.type is TokenType.EOF:
        return "dosya sonu"
    if tok.type is TokenType.NEWLINE:
        return "satır sonu"
    if tok.type is TokenType.STRING:
        return f'"{tok.value}"'
    if tok.type is TokenType.BOOL:
        return "doğru" if tok.value else "yanlış"
    return f"'{tok.value}'"


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # --- yardımcılar -------------------------------------------------
    @property
    def cur(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        i = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[i]

    def _advance(self) -> Token:
        tok = self.cur
        if tok.type is not TokenType.EOF:
            self.pos += 1
        return tok

    def _error(self, expected: str, tok: Token | None = None) -> ParseError:
        tok = tok or self.cur
        return ParseError(f"{expected} bekleniyordu, {_describe(tok)} bulundu", tok.line, tok.col)

    def _expect_keyword(self, word: str) -> Token:
        if not self.cur.is_keyword(word):
            raise self._error(f"'{word}'")
        return self._advance()

    def _expect_op(self, op: str) -> Token:
        if not self.cur.is_op(op):
            raise self._error(f"'{op}'")
        return self._advance()

    def _expect_newline(self) -> None:
        if self.cur.type is TokenType.NEWLINE:
            self._advance()
        elif self.cur.type is not TokenType.EOF:
            raise self._error("satır sonu")

    def _skip_newlines(self) -> None:
        while self.cur.type is TokenType.NEWLINE:
            self._advance()

    # --- deyimler ----------------------------------------------------
    def parse(self) -> ast.Program:
        body: list[ast.Stmt] = []
        self._skip_newlines()
        while self.cur.type is not TokenType.EOF:
            if self.cur.type is TokenType.KEYWORD and self.cur.value in _BLOCK_END:
                raise ParseError(f"'{self.cur.value}' için açık bir blok yok", self.cur.line, self.cur.col)
            body.append(self._statement())
            self._skip_newlines()
        return ast.Program(body, line=1)

    def _block(self) -> list[ast.Stmt]:
        """'değilse' veya 'bitir' görülene kadar deyimleri toplar."""
        body: list[ast.Stmt] = []
        self._skip_newlines()
        while not (self.cur.type is TokenType.KEYWORD and self.cur.value in _BLOCK_END):
            if self.cur.type is TokenType.EOF:
                raise self._error("'bitir'")
            body.append(self._statement())
            self._skip_newlines()
        return body

    def _statement(self) -> ast.Stmt:
        tok = self.cur
        if tok.is_keyword("yazdır"):
            self._advance()
            stmt = ast.Print(self._expression(), line=tok.line)
            self._expect_newline()
            return stmt
        if tok.is_keyword("eğer"):
            return self._if()
        if tok.is_keyword("döngü"):
            return self._loop()
        if tok.type is TokenType.IDENTIFIER:
            self._advance()
            self._expect_op("=")
            stmt = ast.Assign(tok.value, self._expression(), line=tok.line)
            self._expect_newline()
            return stmt
        raise self._error("deyim ('yazdır', 'eğer', 'döngü' veya atama)")

    def _if(self) -> ast.If:
        first = self._expect_keyword("eğer")
        cond = self._expression()
        self._expect_keyword("ise")
        self._expect_newline()
        branches = [(cond, self._block())]
        else_body = None

        while self.cur.is_keyword("değilse"):
            self._advance()
            if self.cur.is_keyword("eğer"):
                self._advance()
                cond = self._expression()
                self._expect_keyword("ise")
                self._expect_newline()
                branches.append((cond, self._block()))
            else:
                self._expect_newline()
                else_body = self._block()
                if self.cur.is_keyword("değilse"):
                    raise ParseError("'değilse' bloğundan sonra başka 'değilse' gelemez",
                                     self.cur.line, self.cur.col)
                break

        self._expect_keyword("bitir")
        self._expect_newline()
        return ast.If(branches, else_body, line=first.line)

    def _loop(self) -> ast.Stmt:
        first = self._expect_keyword("döngü")
        # Sayaç biçimi: döngü i = 1, 10 için
        if self.cur.type is TokenType.IDENTIFIER and self._peek().is_op("="):
            var = self._advance().value
            self._advance()  # "="
            start = self._expression()
            self._expect_op(",")
            end = self._expression()
            self._expect_keyword("için")
            self._expect_newline()
            body = self._block()
            self._expect_keyword("bitir")
            self._expect_newline()
            return ast.ForRange(var, start, end, body, line=first.line)

        # Koşul biçimi: döngü x < 10 için
        cond = self._expression()
        self._expect_keyword("için")
        self._expect_newline()
        body = self._block()
        self._expect_keyword("bitir")
        self._expect_newline()
        return ast.While(cond, body, line=first.line)

    # --- ifadeler ----------------------------------------------------
    def _expression(self) -> ast.Expr:
        return self._or()

    def _or(self) -> ast.Expr:
        left = self._and()
        while self.cur.is_keyword("veya"):
            tok = self._advance()
            left = ast.BinaryOp("veya", left, self._and(), line=tok.line)
        return left

    def _and(self) -> ast.Expr:
        left = self._not()
        while self.cur.is_keyword("ve"):
            tok = self._advance()
            left = ast.BinaryOp("ve", left, self._not(), line=tok.line)
        return left

    def _not(self) -> ast.Expr:
        if self.cur.is_keyword("değil"):
            tok = self._advance()
            return ast.UnaryOp("değil", self._not(), line=tok.line)
        return self._comparison()

    def _comparison(self) -> ast.Expr:
        left = self._additive()
        if self.cur.type is TokenType.OPERATOR and self.cur.value in _COMPARISON:
            tok = self._advance()
            left = ast.BinaryOp(tok.value, left, self._additive(), line=tok.line)
            if self.cur.type is TokenType.OPERATOR and self.cur.value in _COMPARISON:
                raise ParseError("karşılaştırmalar zincirlenemez; 've' kullanın (ör. a < b ve b < c)",
                                 self.cur.line, self.cur.col)
        return left

    def _additive(self) -> ast.Expr:
        left = self._multiplicative()
        while self.cur.type is TokenType.OPERATOR and self.cur.value in ("+", "-"):
            tok = self._advance()
            left = ast.BinaryOp(tok.value, left, self._multiplicative(), line=tok.line)
        return left

    def _multiplicative(self) -> ast.Expr:
        left = self._unary()
        while self.cur.type is TokenType.OPERATOR and self.cur.value in ("*", "/", "%"):
            tok = self._advance()
            left = ast.BinaryOp(tok.value, left, self._unary(), line=tok.line)
        return left

    def _unary(self) -> ast.Expr:
        if self.cur.is_op("-"):
            tok = self._advance()
            return ast.UnaryOp("-", self._unary(), line=tok.line)
        return self._primary()

    def _primary(self) -> ast.Expr:
        tok = self.cur
        if tok.type is TokenType.NUMBER:
            self._advance()
            kind = "float" if isinstance(tok.value, float) else "int"
            return ast.Literal(tok.value, kind, line=tok.line)
        if tok.type is TokenType.STRING:
            self._advance()
            return ast.Literal(tok.value, "str", line=tok.line)
        if tok.type is TokenType.BOOL:
            self._advance()
            return ast.Literal(tok.value, "bool", line=tok.line)
        if tok.type is TokenType.IDENTIFIER:
            self._advance()
            return ast.Identifier(tok.value, line=tok.line)
        if tok.is_op("("):
            self._advance()
            expr = self._expression()
            self._expect_op(")")
            return expr
        raise self._error("ifade (sayı, metin, değişken veya '(')")


def parse(tokens: list[Token]) -> ast.Program:
    return Parser(tokens).parse()
