import unittest

from .common import body_of, gen


class JavaGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.out = gen("java")

    def test_wrapper(self):
        self.assertTrue(self.out.startswith("public class Main {\n    public static void main(String[] args) {"))
        self.assertTrue(self.out.rstrip().endswith("    }\n}"))

    def test_declarations_double_indented(self):
        self.assertIn("\n        int x = 0;", self.out)
        self.assertIn('        String isim = "";', self.out)

    def test_float_division_casts(self):
        self.assertIn("oran = ((double) (x)) / ((double) (y));", self.out)

    def test_print(self):
        self.assertIn('System.out.println(isim + "!");', self.out)

    def test_string_equality_uses_equals(self):
        out = body_of("java", 's = "a"\nb = s == "a"\nc = s != "b"')
        self.assertIn('b = s.equals("a");', out)
        self.assertIn('c = !s.equals("b");', out)

    def test_bool_type(self):
        self.assertIn("boolean b = false;", body_of("java", "b = doğru"))


if __name__ == "__main__":
    unittest.main()
