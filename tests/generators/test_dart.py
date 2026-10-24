import unittest

from .common import body_of, gen


class DartGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.out = gen("dart")

    def test_wrapper(self):
        self.assertTrue(self.out.startswith("void main() {"))
        self.assertTrue(self.out.rstrip().endswith("}"))

    def test_declarations(self):
        for decl in ("int x = 0;", "double oran = 0.0;", 'String isim = "";'):
            self.assertIn(decl, self.out)

    def test_statements(self):
        self.assertIn("print(isim + \"!\");", self.out)
        self.assertIn("if (x > 5 && !(y == 3)) {", self.out)
        self.assertIn("for (i = 1; i <= 3; i++) {", self.out)

    def test_int_to_double_assignment(self):
        out = body_of("dart", "d = 1.5\nn = 2\nd = n")
        self.assertIn("d = (n).toDouble();", out)

    def test_dollar_escaped(self):
        self.assertIn('print("fiyat \\$5");', body_of("dart", 'yazdır "fiyat $5"'))


if __name__ == "__main__":
    unittest.main()
