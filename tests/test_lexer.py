import unittest

from transpiler.errors import LexerError
from transpiler.lexer import tokenize
from transpiler.tokens import TokenType as T


def kinds(src):
    return [(t.type, t.value) for t in tokenize(src)]


class LexerTests(unittest.TestCase):
    def test_assignment(self):
        self.assertEqual(kinds("x = 5"), [
            (T.IDENTIFIER, "x"), (T.OPERATOR, "="), (T.NUMBER, 5),
            (T.NEWLINE, "\n"), (T.EOF, None),
        ])

    def test_keywords_and_turkish_identifiers(self):
        toks = tokenize("eğer sayaç ise")
        self.assertEqual(toks[0].type, T.KEYWORD)
        self.assertEqual(toks[1], toks[1].__class__(T.IDENTIFIER, "sayaç", 1, 6))
        self.assertTrue(toks[2].is_keyword("ise"))

    def test_bool_literals(self):
        toks = tokenize("doğru yanlış")
        self.assertEqual([(t.type, t.value) for t in toks[:2]], [(T.BOOL, True), (T.BOOL, False)])

    def test_numbers(self):
        toks = tokenize("3.14 42")
        self.assertEqual(toks[0].value, 3.14)
        self.assertIsInstance(toks[0].value, float)
        self.assertEqual(toks[1].value, 42)

    def test_two_char_operators_win(self):
        ops = [t.value for t in tokenize("a <= b == c != d >= e") if t.type is T.OPERATOR]
        self.assertEqual(ops, ["<=", "==", "!=", ">="])

    def test_string_with_escapes(self):
        toks = tokenize(r'"a\"b\n"')
        self.assertEqual(toks[0], toks[0].__class__(T.STRING, 'a"b\n', 1, 1))

    def test_comments_and_blank_lines_collapse(self):
        toks = tokenize("x = 1  # yorum\n\n\n# sadece yorum\ny = 2\n")
        newlines = [t for t in toks if t.type is T.NEWLINE]
        self.assertEqual(len(newlines), 2)

    def test_line_and_column_tracking(self):
        toks = tokenize("x = 1\n  y = 2")
        y = [t for t in toks if t.value == "y"][0]
        self.assertEqual((y.line, y.col), (2, 3))

    def test_nfc_normalization(self):
        decomposed = "eğer"  # g + combining breve
        self.assertTrue(tokenize(decomposed)[0].is_keyword("eğer"))

    def test_unterminated_string(self):
        with self.assertRaises(LexerError) as ctx:
            tokenize('yazdır "merhaba')
        self.assertEqual(ctx.exception.line, 1)

    def test_unknown_character(self):
        with self.assertRaises(LexerError) as ctx:
            tokenize("x = 5 @ 2")
        self.assertIn("@", str(ctx.exception))
        self.assertEqual(ctx.exception.col, 7)

    def test_invalid_number(self):
        with self.assertRaises(LexerError):
            tokenize("x = 12abc")


if __name__ == "__main__":
    unittest.main()
