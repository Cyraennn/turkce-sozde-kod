"""Arayüzlerin (web, VS Code eklentisi) ortak kullandığı, JSON'a hazır işlemler.

Her fonksiyon düz bir sözlük döndürür; hata durumunda {"hata": {...}} anahtarı bulunur.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

from . import compile_source
from .errors import TranspileError
from .generators import available_languages, resolve

RUN_TIMEOUT = 5.0              # "Çalıştır" için saniye
MAX_OUTPUT = 64 * 1024         # döndürülen çıktı sınırı (sonsuz yazdırmaya karşı)


def error_payload(exc: TranspileError) -> dict:
    return {"hata": {"tur": exc.kind, "mesaj": exc.message, "satir": exc.line,
                     "sutun": exc.col, "metin": str(exc)}}


def languages() -> list[dict]:
    return [{"ad": i.name, "gorunen": i.display, "uzanti": i.ext} for i in available_languages()]


def translate(source: str, lang: str) -> dict:
    """lang="hepsi" → {"kodlar": {dil: kod}}, aksi hâlde → {"kod": ...}.

    Bilinmeyen dil KeyError fırlatır (çağıran tarafından kullanıcı hatasına çevrilir)."""
    if lang != "hepsi":
        lang = resolve(lang).name
    try:
        compiled = compile_source(source)
    except TranspileError as exc:
        return error_payload(exc)
    if lang == "hepsi":
        return {"kodlar": {info.name: compiled.emit(info.name) for info in available_languages()}}
    return {"kod": compiled.emit(lang)}


def run_python(source: str, timeout: float = RUN_TIMEOUT) -> dict:
    """Sözde kodu Python'a çevirip ayrı, yalıtılmış bir süreçte zaman sınırıyla çalıştırır."""
    try:
        code = compile_source(source).emit("python")
    except TranspileError as exc:
        return error_payload(exc)
    start = time.perf_counter()
    try:
        # -I ortam değişkenlerini yok saydığı için UTF-8'i -X utf8 ile açıkça veriyoruz;
        # kod argüman yerine stdin'den gider (Windows komut satırı kodlamasından bağımsız).
        proc = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", "-"],
            input=code.encode("utf-8"), capture_output=True, timeout=timeout,
            # Windows'ta Python, SYSTEMROOT olmadan rastgele sayı üretecini başlatamaz.
            env={"SYSTEMROOT": os.environ.get("SYSTEMROOT", "")},
        )
        out, err, timed_out = proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as exc:
        out, err, timed_out = exc.stdout or b"", exc.stderr or b"", True
    return {
        "cikti": out[:MAX_OUTPUT].decode("utf-8", "replace"),
        "hata_cikti": err[:MAX_OUTPUT].decode("utf-8", "replace"),
        "sure_ms": round((time.perf_counter() - start) * 1000),
        "zaman_asimi": timed_out,
    }
