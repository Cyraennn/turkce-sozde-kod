import unittest

from .common import body_of, gen


class RustGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.out = gen("rust")

    def test_wrapper(self):
        self.assertTrue(self.out.startswith("#![allow(unused)]"))
        self.assertIn("fn main() {", self.out)

    def test_declarations(self):
        self.assertIn("let mut x: i64 = 0;", self.out)
        self.assertIn("let mut oran: f64 = 0.0;", self.out)
        self.assertIn("let mut isim: String = String::new();", self.out)

    def test_casts(self):
        self.assertIn("oran = ((x) as f64) / ((y) as f64);", self.out)

    def test_conditions_without_parens(self):
        self.assertIn("if x > 5 && !(y == 3) {", self.out)
        self.assertIn("while x < 20 {", self.out)

    def test_range_loop_as_while(self):
        out = body_of("rust", "döngü i = 1, 3 için\nyazdır i\nbitir")
        self.assertEqual(out[-6:-1],  # son "}" main'i kapatır
["i = 1;", "while i <= 3 {", 'println!("{}", i);', "i += 1;", "}"])

    def test_print_concat_single_macro(self):
        self.assertIn('println!("{}!", isim);', self.out)

    def test_assign_concat_single_format(self):
        out = body_of("rust", 's = "a"\nn = 2\nt = s + "-" + n + "-" + (n * 2) + "{x}"')
        self.assertIn('t = format!("{}-{}-{}{{x}}", s, n, n * 2);', out)

    def test_number_sum_stays_one_argument(self):
        # 1 + 2 + "!" → (1 + 2) tek argüman, "3!" yazar
        self.assertIn('println!("{}!", 1 + 2);', body_of("rust", 'yazdır 1 + 2 + "!"'))

    def test_print_literal_inline(self):
        self.assertIn('println!("Kaldı {{%}}");', body_of("rust", 'yazdır "Kaldı {%}"'))

    def test_plain_string_variable_cloned(self):
        self.assertIn("t = s.clone();", body_of("rust", 's = "a"\nt = s'))


if __name__ == "__main__":
    unittest.main()
