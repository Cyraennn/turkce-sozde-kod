"""BaseCodeGenerator ortak davranışı ve dil kayıt defteri."""

import unittest

from transpiler import compile_source, transpile
from transpiler.generators import available_languages, register, resolve
from transpiler.generators import registry
from transpiler.generators.base import BaseCodeGenerator


class RegistryTests(unittest.TestCase):
    def test_seven_languages(self):
        names = {info.name for info in available_languages()}
        self.assertEqual(names, {"cpp", "python", "dart", "java", "rust", "go", "javascript"})

    def test_aliases(self):
        self.assertEqual(resolve("C++").name, "cpp")
        self.assertEqual(resolve("js").name, "javascript")
        self.assertEqual(resolve(" PY ").name, "python")

    def test_unknown_language(self):
        with self.assertRaises(KeyError):
            resolve("cobol")

    def test_duplicate_registration_rejected(self):
        with self.assertRaises(ValueError):
            @register("python", ext=".py")
            class Dup(BaseCodeGenerator):
                pass


class NewLanguageTests(unittest.TestCase):
    """Yeni dil eklemenin ne kadar az kod gerektirdiğini gösterir."""

    def setUp(self):
        @register("pseudo-c", ext=".c", display="Sahte C")
        class PseudoC(BaseCodeGenerator):
            BODY_LEVEL = 0

            def stmt_print(self, code, type_):
                return f"out({code});"

        self.addCleanup(self._unregister, "pseudo-c")

    @staticmethod
    def _unregister(name):
        registry._REGISTRY.pop(name, None)
        registry._ALIASES.pop(name, None)

    def test_minimal_generator_works(self):
        out = transpile("x = 1\neğer x > 0 ise\nyazdır x\nbitir", "pseudo-c")
        self.assertIn("int x = 0;", out)
        self.assertIn("if (x > 0) {", out)
        self.assertIn("out(x);", out)


class SharedBehaviourTests(unittest.TestCase):
    def test_turkish_names_transliterated(self):
        out = transpile("sayaç = 1\nöğrenci_sayısı = sayaç", "cpp")
        self.assertIn("int sayac = 0;", out)
        self.assertIn("ogrenci_sayisi = sayac;", out)

    def test_name_collision_resolved(self):
        out = transpile("sayaç = 1\nsayac = 2", "java")
        self.assertIn("int sayac = 0;", out)
        self.assertIn("int sayac_2 = 0;", out)

    def test_reserved_word_escaped(self):
        self.assertIn("int_ = 5", transpile("int = 5", "python"))
        self.assertIn("int int_ = 0;", transpile("int = 5", "cpp"))

    def test_minimal_parentheses(self):
        out = transpile("a = 1\nb = (a + 2) * 3\nc = a + 2 * 3\nd = a - (2 - 1)", "javascript")
        self.assertIn("b = (a + 2) * 3;", out)
        self.assertIn("c = a + 2 * 3;", out)
        self.assertIn("d = a - (2 - 1);", out)

    def test_compiled_program_reused_for_all_languages(self):
        compiled = compile_source("x = 1\nyazdır x")
        outputs = {info.name: compiled.emit(info.name) for info in available_languages()}
        self.assertEqual(len(set(outputs.values())), 7)

    def test_output_ends_with_single_newline(self):
        for info in available_languages():
            with self.subTest(lang=info.name):
                out = transpile("yazdır 1", info.name)
                self.assertTrue(out.endswith("\n") and not out.endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
