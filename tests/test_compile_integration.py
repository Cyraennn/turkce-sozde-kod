"""Uçtan uca test: üretilen kodu gerçek derleyici/yorumlayıcıyla çalıştırır.

Araç PATH'te yoksa o dilin testi atlanır (skip). Tüm dillerin çıktısı aynı
olmalı — bu, jeneratörlerin anlamsal olarak eşdeğer kod ürettiğinin kanıtı.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from transpiler import transpile

PROGRAM = """\
toplam = 0
döngü i = 1, 10 için
    toplam = toplam + i
bitir
yazdır toplam
oran = 7 / 2
yazdır oran
isim = "Ada"
eğer isim == "Ada" ve toplam > 50 ise
    yazdır "evet"
değilse
    yazdır "hayir"
bitir
n = 1
döngü n < 100 için
    n = n * 3
bitir
yazdır n
yazdır isim + "!"
yazdır 10 > 3
yazdır "Puan: " + toplam + ", oran: " + oran + ", " + (toplam > 50)
yazdır 1 + 2 + "!"
ortalama = 150 / 5
yazdır ortalama
yazdır "ortalama: " + ortalama
yazdır 0.1 + 0.2
yazdır -2.0
"""
EXPECTED = ["55", "3.5", "evet", "243", "Ada!", "true", "Puan: 55, oran: 3.5, true", "3!",
            "30.0", "ortalama: 30.0", "0.30000000000000004", "-2.0"]


def _which(*names):
    for n in names:
        path = shutil.which(n)
        if path:
            return path
    return None


def _run(cmd, cwd, timeout=180):
    # Windows'ta .bat/.cmd dosyaları (dart.bat) için shell gerekmez; liste olarak verilir.
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                         errors="replace", timeout=timeout)
    if res.returncode != 0:
        raise AssertionError(f"{cmd[0]} başarısız ({res.returncode}):\n{res.stdout}\n{res.stderr}")
    return res.stdout


class CompileIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="trc_")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def write(self, lang, filename):
        path = os.path.join(self.tmp, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(transpile(PROGRAM, lang))
        return path

    def check(self, stdout):
        self.assertEqual([ln.strip() for ln in stdout.strip().splitlines()], EXPECTED)

    def test_python(self):
        path = self.write("python", "main.py")
        self.check(_run([sys.executable, path], self.tmp))

    def test_javascript(self):
        node = _which("node")
        if not node:
            self.skipTest("node bulunamadı")
        self.check(_run([node, self.write("javascript", "main.js")], self.tmp))

    def test_java(self):
        java = _which("java")
        if not java:
            self.skipTest("java bulunamadı")
        # Java 11+ tek dosyalı kaynak kodu doğrudan çalıştırabilir.
        self.check(_run([java, self.write("java", "Main.java")], self.tmp))

    def test_dart(self):
        dart = _which("dart")
        if not dart:
            self.skipTest("dart bulunamadı")
        self.check(_run([dart, "run", self.write("dart", "main.dart")], self.tmp))

    def test_cpp(self):
        cxx = _which("g++", "clang++")
        if not cxx:
            self.skipTest("g++/clang++ bulunamadı")
        exe = os.path.join(self.tmp, "main_cpp.exe")
        _run([cxx, "-std=c++17", self.write("cpp", "main.cpp"), "-o", exe], self.tmp)
        self.check(_run([exe], self.tmp))

    def test_rust(self):
        rustc = _which("rustc")
        if not rustc:
            self.skipTest("rustc bulunamadı")
        exe = os.path.join(self.tmp, "main_rs.exe")
        _run([rustc, self.write("rust", "main.rs"), "-o", exe], self.tmp)
        self.check(_run([exe], self.tmp))

    def test_go(self):
        go = _which("go")
        if not go:
            self.skipTest("go bulunamadı")
        self.check(_run([go, "run", self.write("go", "main.go")], self.tmp))


if __name__ == "__main__":
    unittest.main()
