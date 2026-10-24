import unittest

from .common import body_of, gen


class PythonGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.out = gen("python")

    def test_no_declarations_or_wrapper(self):
        self.assertTrue(self.out.startswith("x = 7\n"))
        self.assertNotIn("def main", self.out)

    def test_operators(self):
        self.assertIn("oran = x / y", self.out)
        self.assertIn("if x > 5 and not (y == 3):", self.out)
        self.assertIn("elif x == 5:", self.out)
        self.assertIn("else:", self.out)

    def test_range_loop_inclusive(self):
        self.assertIn("for i in range(1, 4):", self.out)
        self.assertIn("for k in range(1, n + 1):", body_of("python", "n = 3\ndöngü k = 1, n için\nbitir"))

    def test_while(self):
        self.assertIn("while x < 20:", self.out)

    def test_indentation(self):
        self.assertIn('\n    print("büyük")\n', self.out)

    def test_empty_block_gets_pass(self):
        self.assertEqual(body_of("python", "eğer doğru ise\nbitir"), ["if True:", "pass"])

    def test_bool_print_lowercase(self):
        self.assertEqual(body_of("python", "yazdır doğru"), ["print(str(True).lower())"])

    def test_comparison_not_chained(self):
        # (a < b) == c  Python'da zincir olmamalı
        out = body_of("python", "a = 1\nb = 2\nc = (a < b) == doğru")
        self.assertIn("c = (a < b) == True", out)

    def test_generated_code_runs(self):
        namespace = {}
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exec(self.out, namespace)  # noqa: S102 - kendi ürettiğimiz kod
        self.assertEqual(buf.getvalue().split(), ["büyük", "1", "2", "3", "Ali!"])


if __name__ == "__main__":
    unittest.main()
