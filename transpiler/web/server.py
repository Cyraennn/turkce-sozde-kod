"""Yalnızca standart kütüphaneyle yerel web sunucusu.

Uç noktalar:
    GET  /               arayüz sayfası
    GET  /api/diller     [{ad, gorunen, uzanti}]
    POST /api/cevir      {kaynak, dil}  → {kod} | {kodlar: {dil: kod}} (dil="hepsi") | {hata}
    POST /api/calistir   {kaynak}       → {cikti, hata_cikti, sure_ms, zaman_asimi} | {hata}

Sunucu yalnızca 127.0.0.1'e bağlanır; dışarıdan erişilemez.
"""

from __future__ import annotations

import json
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources

from .. import __version__
from ..service import languages, run_python, translate

HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_BODY = 256 * 1024          # istek gövdesi sınırı


class Handler(BaseHTTPRequestHandler):
    server_version = f"trc/{__version__}"

    def log_message(self, fmt, *args):   # konsolu sessiz tut
        pass

    # --- yardımcılar ---
    def _send(self, status: int, body: bytes, ctype: str):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status: int = HTTPStatus.OK):
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _read_json(self) -> dict | None:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            self._json({"hata": {"metin": "İstek gövdesi boş ya da çok büyük"}}, HTTPStatus.BAD_REQUEST)
            return None
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("kaynak"), str):
                raise ValueError
            return data
        except (ValueError, UnicodeDecodeError):
            self._json({"hata": {"metin": "Geçersiz istek"}}, HTTPStatus.BAD_REQUEST)
            return None

    # --- yönlendirme ---
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            page = resources.files(__package__).joinpath("static/index.html").read_bytes()
            self._send(HTTPStatus.OK, page, "text/html; charset=utf-8")
        elif path == "/api/diller":
            self._json(languages())
        else:
            self._json({"hata": {"metin": "Bulunamadı"}}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path not in ("/api/cevir", "/api/calistir"):
            self._json({"hata": {"metin": "Bulunamadı"}}, HTTPStatus.NOT_FOUND)
            return
        data = self._read_json()
        if data is None:
            return
        if path == "/api/calistir":
            self._json(run_python(data["kaynak"]))
            return
        try:
            self._json(translate(data["kaynak"], str(data.get("dil") or "python")))
        except KeyError as exc:
            self._json({"hata": {"metin": exc.args[0]}}, HTTPStatus.BAD_REQUEST)


def make_server(port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """Verilen portu dener; doluysa işletim sisteminin seçtiği boş bir porta geçer."""
    try:
        return ThreadingHTTPServer((HOST, port), Handler)
    except OSError:
        return ThreadingHTTPServer((HOST, 0), Handler)


def serve(port: int = DEFAULT_PORT, open_browser: bool = True) -> None:
    httpd = make_server(port)
    url = f"http://{HOST}:{httpd.server_address[1]}/"
    print(f"Arayüz açık: {url}  (kapatmak için Ctrl+C)")
    if open_browser:
        threading.Timer(0.3, webbrowser.open, args=(url,)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArayüz kapatıldı.")
    finally:
        httpd.server_close()
