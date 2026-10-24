"""Türkçe sözde kod → çoklu dil dönüştürücü (yapay zeka kullanmadan, kural tabanlı).

Hat: Lexer → Parser → (AST) → Anlamsal analiz → Code Generator
"""

from __future__ import annotations

from dataclasses import dataclass

from . import ast_nodes
from .errors import LexerError, ParseError, SemanticError, TranspileError
from .generators import available_languages, get_generator, resolve
from .lexer import tokenize
from .parser import parse
from .semantic import analyze

__version__ = "1.0.0"


@dataclass
class CompiledProgram:
    """Dilden bağımsız ara sonuç: bir kez derlenir, istenen her dile çevrilir."""
    program: ast_nodes.Program
    symbols: dict[str, str]

    def emit(self, lang: str) -> str:
        return get_generator(lang).generate(self.program, self.symbols)


def compile_source(source: str) -> CompiledProgram:
    program = parse(tokenize(source))
    symbols = analyze(program)
    return CompiledProgram(program, symbols)


def transpile(source: str, lang: str) -> str:
    return compile_source(source).emit(lang)


__all__ = [
    "transpile", "compile_source", "CompiledProgram", "available_languages", "resolve",
    "TranspileError", "LexerError", "ParseError", "SemanticError", "__version__",
]
