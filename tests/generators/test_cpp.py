import unittest

from .common import body_of, gen


class CppGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.out = gen("cpp")

    def test_wrapper(self):
        self.assertTrue(self.out.startswith("#include <iostream>\n#include <string>"))
        self.assertIn("int main() {", self.out)
        self.assertIn("return 0;", self.out)
        self.assertIn("std::cout << std::boolalpha;", self.out)

    def test_declarations(self):
        for decl in ("int x = 0;", "double oran = 0.0;", 'std::string isim = "";', "int i = 0;"):
            self.assertIn(decl, self.out)

    def test_float_division_casts(self):
        self.assertIn("oran = static_cast<double>(x) / static_cast<double>(y);", self.out)

    def test_control_flow(self):
        self.assertIn("if (x > 5 && !(y == 3)) {", self.out)
        self.assertIn("} else if (x == 5) {", self.out)
        self.assertIn("for (i = 1; i <= 3; i++) {", self.out)
        self.assertIn("while (x < 20) {", self.out)

    def test_strings_are_std_string(self):
        self.assertIn('std::cout << isim + std::string("!") << "\\n";', self.out)

    def test_bool_print_parenthesized(self):
        self.assertIn('std::cout << (1 < 2) << "\\n";', body_of("cpp", "yazdır 1 < 2"))


if __name__ == "__main__":
    unittest.main()
