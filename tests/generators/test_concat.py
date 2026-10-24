"""Esnek birleştirme politikası: metin + sayı/mantıksal her dilde doğru dönüştürülür."""

import unittest

from transpiler import transpile

SRC = 'n = 5\nf = 2.5\nb = doğru\nyazdır "n=" + n + " f=" + f + " b=" + b\n'

EXPECTED = {
    "python": 'print("n=" + str(n) + " f=" + str(f) + " b=" + str(b).lower())',
    "cpp": 'std::cout << std::string("n=") + std::to_string(n) + std::string(" f=") '
           '+ double_to_str(f) + std::string(" b=") + std::string((b) ? "true" : "false") << "\\n";',
    "java": 'System.out.println("n=" + n + " f=" + f + " b=" + b);',
    "javascript": 'console.log("n=" + n + " f=" + formatFloat(f) + " b=" + b);',
    "dart": 'print("n=" + (n).toString() + " f=" + (f).toString() + " b=" + (b).toString());',
    "go": 'fmt.Println("n=" + fmt.Sprint(n) + " f=" + formatFloat(f) + " b=" + fmt.Sprint(b))',
    "rust": 'println!("n={} f={:?} b={}", n, f, b);',
}


class ConcatTests(unittest.TestCase):
    def test_each_language(self):
        for lang, expected in EXPECTED.items():
            with self.subTest(lang=lang):
                self.assertIn(expected, transpile(SRC, lang))

    def test_cpp_helper_only_when_needed(self):
        self.assertIn("std::string double_to_str(double v)", transpile(SRC, "cpp"))
        self.assertNotIn("double_to_str", transpile('yazdır "a" + 1', "cpp"))
        self.assertNotIn("<charconv>", transpile("yazdır 1", "cpp"))

    def test_go_imports_fmt_for_conversion_without_print(self):
        self.assertIn('import "fmt"', transpile('s = "a" + 1', "go"))

    def test_float_print_formatting(self):
        # Ondalık çıktı her dilde Python gibi: 30.0 → "30.0"
        src = "x = 30.0\nyazdır x"
        expected = {
            "python": "print(x)",
            "java": "System.out.println(x);",
            "dart": "print(x);",
            "javascript": "console.log(formatFloat(x));",
            "go": "fmt.Println(formatFloat(x))",
            "rust": 'println!("{:?}", x);',
            "cpp": 'std::cout << double_to_str(x) << "\\n";',
        }
        for lang, line in expected.items():
            with self.subTest(lang=lang):
                self.assertIn(line, transpile(src, lang))

    def test_float_helpers_only_when_needed(self):
        self.assertNotIn("formatFloat", transpile("yazdır 1", "javascript"))
        go = transpile("yazdır 1.5", "go")
        self.assertIn('import (\n\t"fmt"\n\t"strconv"\n\t"strings"\n)', go)
        self.assertIn("func formatFloat(v float64) string {", go)

    def test_number_sum_before_text(self):
        # 1 + 2 + "!" soldan birleşir → "3!" (her dilde aynı)
        self.assertIn('print(str(1 + 2) + "!")', transpile('yazdır 1 + 2 + "!"', "python"))


if __name__ == "__main__":
    unittest.main()
