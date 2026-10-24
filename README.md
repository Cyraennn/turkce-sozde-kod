# trc — Türkçe Sözde Kod Dönüştürücü

Türkçe sözde kodu **C++, Python, Dart, Java, Rust, Go ve JavaScript**'e çeviren,
yapay zeka kullanmayan, tamamen kural tabanlı bir transpiler. Yalnızca Python
standart kütüphanesi kullanır.

```
Kaynak ─► Lexer ─► Token'lar ─► Parser ─► AST ─► Anlamsal analiz ─► Generator ─► Hedef kod
```

## Kurulum ve çalıştırma
```bash
python -m transpiler                        # etkileşimli kabuk
python -m transpiler examples/dongu.tr -l rust
python -m transpiler examples/kosul.tr --all
python -m transpiler examples/kosul.tr --all -o cikti/   # her dil ayrı dosya
pip install -e .   # sonrasında: trc ...
```

## Dil
```
# yorum
x = 5
isim = "Ali"
eğer x > 3 ve değil (isim == "Veli") ise
    yazdır "büyük"
değilse eğer x == 3 ise
    yazdır "eşit"
değilse
    yazdır x
bitir
döngü i = 1, 10 için        # 1'den 10'a (dahil)
    yazdır i
bitir
döngü x < 100 için          # koşul döngüsü
    x = x * 2
bitir
```
| Öğe | Sözdizimi |
|---|---|
| Tipler | tam sayı, ondalık, `"metin"`, `doğru`/`yanlış` |
| Aritmetik | `+ - * / %` (`/` her zaman ondalık sonuç verir) |
| Karşılaştırma | `== != < > <= >=` |
| Mantık | `ve`, `veya`, `değil` |

## Etkileşimli kabuk
Satırları yazın, **boş satıra Enter** basınca seçili dile çevrilir.

| Komut | İş |
|---|---|
| `:set lang cpp` / `:dil rust` | Dili değiştir, kodu hemen yeniden çevir |
| `:menu` | Numaralı dil menüsü |
| `:hepsi` | 7 dilin hepsinde göster |
| `:göster`, `:kod`, `:geri`, `:temizle` | Göster / tamponu listele / son satırı sil / temizle |
| `:yükle dosya.tr`, `:kaydet cikti` | Dosyadan oku / çıktıyı yaz |
| `:yardım`, `:çık` | |

## Yeni dil eklemek
`transpiler/generators/kotlin.py`:
```python
from .base import BaseCodeGenerator
from .registry import register

@register("kotlin", aliases=["kt"], ext=".kt", display="Kotlin")
class KotlinGenerator(BaseCodeGenerator):
    END = ""
    TYPE_NAMES = {"int": "Int", "float": "Double", "str": "String", "bool": "Boolean"}

    def header(self):  return ["fun main() {"]
    def footer(self):  return ["}"]
    def declaration(self, name, t): return f"var {name}: {self.TYPE_NAMES[t]} = {self.DEFAULT_VALUES[t]}"
    def stmt_print(self, code, t):  return f"println({code})"
    def coerce_to_float(self, code): return f"({code}).toDouble()"
```
Ardından `generators/__init__.py` içindeki `LANGUAGE_MODULES` listesine `"kotlin"` ekleyin.
CLI ve kabuk dili otomatik olarak tanır. Gezinme, girinti, parantezleme, Türkçe harf
dönüşümü (`sayaç → sayac`) ve tip dönüşümleri `BaseCodeGenerator`'da hazır gelir.

## Testler
```bash
python -m unittest discover -s tests -t . -v
```
`tests/test_compile_integration.py`, PATH'te bulunan derleyicilerle (g++, javac/java,
rustc, go, dart, node) üretilen kodu gerçekten çalıştırır ve 7 dilin aynı çıktıyı
verdiğini doğrular. Bulunmayan derleyicinin testi atlanır.

## Klasör yapısı
```
transpiler/
  tokens.py lexer.py        # sözcük analizi
  ast_nodes.py parser.py    # sözdizimi analizi
  semantic.py               # tip çıkarımı
  generators/               # base.py + dil başına bir dosya + registry.py
  cli/                      # main.py (argparse), repl.py (ReplSession)
tests/                      # lexer, parser, semantic, repl, generators/*, entegrasyon
examples/                   # örnek .tr dosyaları
```
