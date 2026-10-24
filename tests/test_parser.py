import unittest

from transpiler import ast_nodes as a
from transpiler.errors import ParseError
from transpiler.lexer import tokenize
from transpiler.parser import parse


def p(src):
    return parse(tokenize(src)).body


def lit(v):
    kind = {bool: "bool", int: "int", float: "float", str: "str"}[type(v)]
    return a.Literal(v, kind)


class ExpressionTests(unittest.TestCase):
    def expr(self, src):
        return p(f"x = {src}")[0].value

    def test_precedence_mul_over_add(self):
        self.assertEqual(self.expr("1 + 2 * 3"),
                         a.BinaryOp("+", lit(1), a.BinaryOp("*", lit(2), lit(3))))

    def test_left_associativity(self):
        self.assertEqual(self.expr("8 - 4 - 2"),
                         a.BinaryOp("-", a.BinaryOp("-", lit(8), lit(4)), lit(2)))

    def test_parentheses(self):
        self.assertEqual(self.expr("(1 + 2) * 3"),
                         a.BinaryOp("*", a.BinaryOp("+", lit(1), lit(2)), lit(3)))

    def test_logic_precedence(self):
        # a veya b ve değil c  →  a veya (b ve (değil c))
        e = self.expr("a veya b ve değil c")
        self.assertEqual(e, a.BinaryOp("veya", a.Identifier("a"),
                                       a.BinaryOp("ve", a.Identifier("b"),
                                                  a.UnaryOp("değil", a.Identifier("c")))))

    def test_unary_minus(self):
        self.assertEqual(self.expr("-x * 2"),
                         a.BinaryOp("*", a.UnaryOp("-", a.Identifier("x")), lit(2)))

    def test_comparison_chain_rejected(self):
        with self.assertRaises(ParseError):
            self.expr("1 < 2 < 3")


class StatementTests(unittest.TestCase):
    def test_print(self):
        self.assertEqual(p('yazdır "selam"'), [a.Print(lit("selam"))])

    def test_if_elif_else(self):
        src = """
eğer x > 1 ise
    yazdır 1
değilse eğer x > 0 ise
    yazdır 2
değilse
    yazdır 3
bitir
"""
        node = p(src)[0]
        self.assertIsInstance(node, a.If)
        self.assertEqual(len(node.branches), 2)
        self.assertEqual(node.else_body, [a.Print(lit(3))])

    def test_for_range(self):
        node = p("döngü i = 1, 10 için\n yazdır i\nbitir")[0]
        self.assertEqual(node, a.ForRange("i", lit(1), lit(10), [a.Print(a.Identifier("i"))]))

    def test_while(self):
        node = p("döngü x < 3 için\n x = x + 1\nbitir")[0]
        self.assertIsInstance(node, a.While)
        self.assertEqual(node.cond, a.BinaryOp("<", a.Identifier("x"), lit(3)))

    def test_nested_blocks(self):
        node = p("döngü i = 1, 3 için\n eğer i == 2 ise\n yazdır i\n bitir\nbitir")[0]
        self.assertIsInstance(node.body[0], a.If)

    def test_empty_block_allowed(self):
        node = p("eğer doğru ise\nbitir")[0]
        self.assertEqual(node.branches[0][1], [])

    def test_line_numbers_recorded(self):
        body = p("x = 1\n\nyazdır x")
        self.assertEqual([s.line for s in body], [1, 3])


class ErrorTests(unittest.TestCase):
    def assertParseError(self, src, fragment, line=None):
        with self.assertRaises(ParseError) as ctx:
            p(src)
        self.assertIn(fragment, str(ctx.exception))
        if line is not None:
            self.assertEqual(ctx.exception.line, line)

    def test_missing_ise(self):
        self.assertParseError("eğer x > 1\nyazdır x\nbitir", "'ise' bekleniyordu", 1)

    def test_missing_bitir(self):
        self.assertParseError("eğer doğru ise\nyazdır 1\n", "'bitir' bekleniyordu")

    def test_stray_bitir(self):
        self.assertParseError("bitir", "açık bir blok yok")

    def test_missing_icin(self):
        self.assertParseError("döngü i = 1, 3\nbitir", "'için' bekleniyordu")

    def test_double_else(self):
        self.assertParseError("eğer doğru ise\ndeğilse\ndeğilse\nbitir", "başka 'değilse'")

    def test_garbage_after_statement(self):
        self.assertParseError("x = 1 2", "satır sonu bekleniyordu")


if __name__ == "__main__":
    unittest.main()
