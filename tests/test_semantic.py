import unittest

from transpiler.errors import SemanticError
from transpiler.lexer import tokenize
from transpiler.parser import parse
from transpiler.semantic import analyze, binary_result_type


def symbols(src):
    return analyze(parse(tokenize(src)))


class TypeInferenceTests(unittest.TestCase):
    def test_basic_types(self):
        self.assertEqual(symbols('a = 1\nb = 2.5\nc = "x"\nd = doğru'),
                         {"a": "int", "b": "float", "c": "str", "d": "bool"})

    def test_division_is_float(self):
        self.assertEqual(symbols("x = 7 / 2")["x"], "float")

    def test_int_float_mix(self):
        self.assertEqual(symbols("x = 1 + 2.0")["x"], "float")

    def test_widening_fixpoint(self):
        # y önce x'ten int alır; x sonradan float'a genişleyince y de genişlemeli.
        s = symbols("x = 1\ny = x\nx = 2.5")
        self.assertEqual(s, {"x": "float", "y": "float"})

    def test_comparison_is_bool(self):
        self.assertEqual(symbols("b = 1 < 2 ve doğru")["b"], "bool")

    def test_loop_var_is_int(self):
        self.assertEqual(symbols("döngü i = 1, 3 için\nbitir")["i"], "int")

    def test_string_concat(self):
        self.assertEqual(symbols('s = "a" + "b"')["s"], "str")

    def test_flexible_concat_policy(self):
        # Esnek politika: metin + sayı/ondalık/mantıksal → metin (her iki yönde)
        s = symbols('a = "P: " + 5\nb = 2.5 + "x"\nc = "d: " + doğru\nd = 1 + 2 + "!"')
        self.assertEqual(s, {"a": "str", "b": "str", "c": "str", "d": "str"})

    def test_insertion_order_kept(self):
        self.assertEqual(list(symbols("b = 1\na = 2")), ["b", "a"])


class SemanticErrorTests(unittest.TestCase):
    def assertSemError(self, src, fragment):
        with self.assertRaises(SemanticError) as ctx:
            symbols(src)
        self.assertIn(fragment, str(ctx.exception))

    def test_undefined_variable(self):
        self.assertSemError("yazdır y", "'y' tanımlanmadan kullanıldı")

    def test_type_change(self):
        self.assertSemError('x = 1\nx = "a"', "atanamaz")

    def test_condition_must_be_bool(self):
        self.assertSemError("eğer 5 ise\nbitir", "mantıksal")

    def test_while_condition_must_be_bool(self):
        self.assertSemError("döngü 1 için\nbitir", "mantıksal")

    def test_modulo_requires_ints(self):
        self.assertSemError("x = 5.5 % 2", "tam sayı")

    def test_string_ordering(self):
        self.assertSemError('b = "a" < "b"', "sayılarla")

    def test_logical_on_ints(self):
        self.assertSemError("b = 1 ve 2", "mantıksal")

    def test_range_bounds_int(self):
        self.assertSemError("döngü i = 1.5, 3 için\nbitir", "tam sayı")

    def test_not_on_number(self):
        self.assertSemError("b = değil 3", "'değil'")

    def test_error_has_line(self):
        with self.assertRaises(SemanticError) as ctx:
            symbols("x = 1\n\nyazdır z")
        self.assertEqual(ctx.exception.line, 3)


class BinaryResultTypeTests(unittest.TestCase):
    def test_table(self):
        cases = [
            ("+", "int", "int", "int"),
            ("*", "int", "float", "float"),
            ("/", "int", "int", "float"),
            ("%", "int", "int", "int"),
            ("==", "str", "str", "bool"),
            ("==", "int", "float", "bool"),
            ("ve", "bool", "bool", "bool"),
            ("+", "str", "int", "str"),
            ("+", "bool", "str", "str"),
        ]
        for op, l, r, expected in cases:
            with self.subTest(op=op, l=l, r=r):
                self.assertEqual(binary_result_type(op, l, r), expected)

    def test_bool_arithmetic_rejected(self):
        with self.assertRaises(SemanticError):
            binary_result_type("+", "bool", "int")

    def test_string_minus_rejected(self):
        # Esneklik sadece "+" için; "metin" - 1 hâlâ hata
        with self.assertRaises(SemanticError):
            binary_result_type("-", "str", "int")


if __name__ == "__main__":
    unittest.main()
