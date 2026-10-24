"""Tarayıcı arayüzü sunucusu: gerçek bir porta bağlanıp uç noktaları çağırır."""

import json
import threading
import unittest
import urllib.error
import urllib.request

from transpiler.web import make_server


class WebServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = make_server(0)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as r:
            return r.status, r.headers.get("Content-Type"), r.read()

    def post(self, path, payload):
        req = urllib.request.Request(self.base + path, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_index_page(self):
        status, ctype, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)
        self.assertIn("Sözde Kod Dönüştürücü".encode(), body)

    def test_languages(self):
        _, _, body = self.get("/api/diller")
        names = [d["ad"] for d in json.loads(body)]
        self.assertEqual(len(names), 7)
        self.assertIn("rust", names)

    def test_translate_single(self):
        status, data = self.post("/api/cevir", {"kaynak": "yazdır 1", "dil": "py"})
        self.assertEqual(status, 200)
        self.assertEqual(data["kod"].strip(), "print(1)")

    def test_translate_all(self):
        _, data = self.post("/api/cevir", {"kaynak": "x = 2", "dil": "hepsi"})
        self.assertEqual(len(data["kodlar"]), 7)

    def test_translate_error_has_position(self):
        _, data = self.post("/api/cevir", {"kaynak": "x = 1\nyazdır y", "dil": "python"})
        self.assertEqual(data["hata"]["satir"], 2)
        self.assertIn("Anlam hatası", data["hata"]["metin"])

    def test_unknown_language(self):
        status, data = self.post("/api/cevir", {"kaynak": "x = 1", "dil": "cobol"})
        self.assertEqual(status, 400)
        self.assertIn("bilinmeyen dil", data["hata"]["metin"])

    def test_bad_request(self):
        status, _ = self.post("/api/cevir", {"dil": "python"})
        self.assertEqual(status, 400)

    def test_run(self):
        _, data = self.post("/api/calistir", {"kaynak": 'yazdır "çalıştı " + (7 / 2)'})
        self.assertEqual(data["cikti"].strip(), "çalıştı 3.5")
        self.assertFalse(data["zaman_asimi"])

    def test_unknown_path(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get("/yok")
        self.assertEqual(cm.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
