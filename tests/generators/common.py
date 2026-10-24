"""Jeneratör testlerinin ortak yardımcıları."""

from transpiler import transpile

# Tüm dil özelliklerini kapsayan örnek program.
FULL_PROGRAM = """\
x = 7
y = 2
oran = x / y
isim = "Ali"
eğer x > 5 ve değil (y == 3) ise
    yazdır "büyük"
değilse eğer x == 5 ise
    yazdır isim
değilse
    yazdır oran
bitir
döngü i = 1, 3 için
    yazdır i
bitir
döngü x < 20 için
    x = x * 2
bitir
yazdır isim + "!"
"""


def gen(lang, src=FULL_PROGRAM):
    return transpile(src, lang)


def body_of(lang, src):
    """Sarmalayıcı satırlar olmadan, sadece anlamlı satırları döndürür."""
    return [ln.strip() for ln in gen(lang, src).splitlines() if ln.strip()]
