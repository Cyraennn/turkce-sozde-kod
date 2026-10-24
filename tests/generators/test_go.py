import unittest

from .common import gen


class GoGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.out = gen("go")

    def test_wrapper(self):
        self.assertTrue(self.out.startswith("package main\n\nimport (\n"))
        self.assertIn("func main() {", self.out)
        self.assertTrue(gen("go", "yazdır 1").startswith('package main\n\nimport "fmt"\n\nfunc main() {'))

    def test_no_fmt_import_without_print(self):
        self.assertNotIn("import", gen("go", "x = 1"))

    def test_declarations_and_unused_guard(self):
        self.assertIn("\tvar x int", self.out)
        self.assertIn("\tvar oran float64", self.out)
        self.assertIn("\t_ = isim", self.out)

    def test_loops(self):
        self.assertIn("for i = 1; i <= 3; i++ {", self.out)
        self.assertIn("for x < 20 {", self.out)

    def test_casts_and_print(self):
        self.assertIn("oran = float64(x) / float64(y)", self.out)
        self.assertIn('fmt.Println(isim + "!")', self.out)

    def test_no_semicolons(self):
        self.assertNotIn(";\n", self.out.replace("i++ {", ""))


if __name__ == "__main__":
    unittest.main()
