import os
import tempfile
import unittest

from transpiler.cli.repl import ReplSession


class FakeIO:
    def __init__(self, answers=()):
        self.lines: list[str] = []
        self.answers = list(answers)

    def out(self, text):
        self.lines.append(text)

    def input(self, prompt):
        return self.answers.pop(0)

    @property
    def text(self):
        return "\n".join(self.lines)


def session(lang="python", answers=()):
    io = FakeIO(answers)
    return ReplSession(lang, out=io.out, input_fn=io.input), io


def feed(s, *lines):
    for ln in lines:
        s.handle(ln)


class ReplTests(unittest.TestCase):
    def test_blank_line_translates_buffer(self):
        s, io = session()
        feed(s, "x = 5", "yazdır x", "")
        self.assertIn("print(x)", io.text)

    def test_set_lang_rerenders_immediately(self):
        s, io = session()
        feed(s, "yazdır 1")
        s.handle(":set lang cpp")
        self.assertEqual(s.lang, "cpp")
        self.assertIn('std::cout << 1 << "\\n";', io.text)
        io.lines.clear()
        s.handle(":set lang rust")
        self.assertIn('println!("{}", 1);', io.text)

    def test_same_code_switches_between_languages(self):
        s, io = session()
        feed(s, "yazdır 1")
        outputs = []
        for lang in ("python", "go", "java"):
            io.lines.clear()
            s.handle(f":dil {lang}")
            outputs.append(io.text)
        self.assertEqual(len(set(outputs)), 3)

    def test_unknown_language(self):
        s, io = session()
        s.handle(":set lang cobol")
        self.assertEqual(s.lang, "python")
        self.assertIn("bilinmeyen dil", io.text)

    def test_menu_by_number(self):
        s, io = session(answers=["5"])  # 5) Rust
        s.handle(":menu")
        self.assertEqual(s.lang, "rust")

    def test_menu_by_name(self):
        s, _ = session(answers=["go"])
        s.handle(":menü")
        self.assertEqual(s.lang, "go")

    def test_all_languages(self):
        s, io = session()
        feed(s, "yazdır 1", ":hepsi")
        for title in ("C++", "Python", "Dart", "Java", "Rust", "Go", "JavaScript"):
            self.assertIn(f"=== {title} ===", io.text)

    def test_open_block_waits_for_bitir(self):
        s, io = session()
        feed(s, "eğer doğru ise", "")
        self.assertEqual(io.lines, [])  # blok açıkken boş satır çeviri yapmaz
        self.assertEqual(s.depth, 1)
        self.assertIn("..", s.prompt())
        feed(s, "yazdır 1", "bitir", "")
        self.assertIn("if True:", io.text)

    def test_errors_reported_buffer_kept(self):
        s, io = session()
        feed(s, "yazdır y", "")
        self.assertIn("'y' tanımlanmadan kullanıldı", io.text)
        self.assertEqual(s.buffer, ["yazdır y"])

    def test_undo_and_clear(self):
        s, _ = session()
        feed(s, "x = 1", "x = 2", ":geri")
        self.assertEqual(s.buffer, ["x = 1"])
        s.handle(":temizle")
        self.assertEqual(s.buffer, [])

    def test_quit(self):
        s, _ = session()
        s.handle(":çık")
        self.assertFalse(s.running)

    def test_unknown_command(self):
        s, io = session()
        s.handle(":uç")
        self.assertIn("Bilinmeyen komut", io.text)

    def test_load_and_save(self):
        s, io = session("go")
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "p.tr")
            with open(src, "w", encoding="utf-8") as f:
                f.write("yazdır 42\n")
            s.handle(f":yükle {src}")
            self.assertIn("fmt.Println(42)", io.text)
            s.handle(f":kaydet {os.path.join(d, 'cikti')}")
            with open(os.path.join(d, "cikti.go"), encoding="utf-8") as f:
                self.assertIn("package main", f.read())


if __name__ == "__main__":
    unittest.main()
