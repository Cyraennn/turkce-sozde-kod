import unittest

from .common import gen


class JavaScriptGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.out = gen("javascript")

    def test_let_declarations(self):
        # Program ondalık yazdırdığı için dosya formatFloat yardımcısıyla başlar.
        self.assertTrue(self.out.startswith("function formatFloat(v) {"))
        self.assertIn("\nlet x = 0;\n", self.out)
        self.assertTrue(gen("javascript", "x = 1").startswith("let x = 0;\n"))
        self.assertIn('let isim = "";', self.out)

    def test_strict_equality(self):
        self.assertIn("if (x > 5 && !(y === 3)) {", self.out)
        self.assertIn("} else if (x === 5) {", self.out)

    def test_console_log(self):
        self.assertIn('console.log(isim + "!");', self.out)

    def test_division_needs_no_cast(self):
        self.assertIn("oran = x / y;", self.out)


if __name__ == "__main__":
    unittest.main()
