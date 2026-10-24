"""Komut satırı girişi: `trc` veya `python -m transpiler`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import __version__, compile_source
from ..errors import TranspileError
from ..generators import available_languages, resolve
from .repl import run_repl


def _build_parser() -> argparse.ArgumentParser:
    names = ", ".join(info.name for info in available_languages())
    p = argparse.ArgumentParser(
        prog="trc",
        description="Türkçe sözde kodu C++, Python, Dart, Java, Rust, Go ve JavaScript'e çevirir. "
                    "Dosya verilmezse etkileşimli kabuk açılır.",
    )
    p.add_argument("kaynak", nargs="?", help="sözde kod dosyası (.tr). '-' = standart girdi")
    p.add_argument("-l", "--lang", "--dil", default="python", help=f"hedef dil ({names})")
    p.add_argument("-a", "--all", "--hepsi", action="store_true", help="tüm dillere çevir")
    p.add_argument("-o", "--output", help="çıktı dosyası (--all ile: klasör)")
    p.add_argument("--diller", action="store_true", help="desteklenen dilleri listele")
    p.add_argument("--version", action="version", version=f"trc {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    args = _build_parser().parse_args(argv)

    if args.diller:
        for info in available_languages():
            print(f"{info.name:<11} {info.display:<11} {info.ext}")
        return 0

    try:
        lang = resolve(args.lang).name
    except KeyError as exc:
        print(exc.args[0], file=sys.stderr)
        return 2

    if args.kaynak is None:
        run_repl(lang)
        return 0

    try:
        source = sys.stdin.read() if args.kaynak == "-" else Path(args.kaynak).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Dosya okunamadı: {exc}", file=sys.stderr)
        return 2

    try:
        compiled = compile_source(source)
    except TranspileError as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.all:
        stem = Path(args.kaynak).stem if args.kaynak != "-" else "program"
        for info in available_languages():
            code = compiled.emit(info.name)
            if args.output:
                out_dir = Path(args.output)
                out_dir.mkdir(parents=True, exist_ok=True)
                # Java'da genel sınıf adı dosya adıyla aynı olmalı.
                fname = "Main.java" if info.name == "java" else stem + info.ext
                (out_dir / fname).write_text(code, encoding="utf-8")
            else:
                print(f"=== {info.display} ===")
                print(code)
        if args.output:
            print(f"{len(available_languages())} dosya yazıldı: {args.output}")
        return 0

    code = compiled.emit(lang)
    if args.output:
        Path(args.output).write_text(code, encoding="utf-8")
    else:
        print(code, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
