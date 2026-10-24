"""Etkileşimli kabuk (REPL).

`ReplSession` G/Ç'den bağımsızdır: çıktıyı `out` fonksiyonuyla verir, girdiyi
`input_fn` ile alır. Böylece testler sahte girdi listesiyle çalıştırabilir.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .. import compile_source
from ..errors import TranspileError
from ..generators import available_languages, resolve
from ..lexer import tokenize

HELP = """\
Türkçe sözde kodu yazın; boş satıra Enter basınca seçili dile çevrilir.

Komutlar:
  :set lang <dil>   Hedef dili değiştir ve kodu hemen yeniden çevir  (kısa: :dil <dil>)
  :menu             Numaralı dil seçim menüsü
  :diller           Desteklenen diller
  :göster           Kodu seçili dilde göster                          (:show)
  :hepsi            Kodu tüm dillerde göster                          (:all)
  :kod              Tampondaki sözde kodu satır numaralarıyla göster  (:code)
  :geri             Son satırı sil                                     (:undo)
  :temizle          Tamponu boşalt                                     (:clear)
  :yükle <dosya>    Sözde kod dosyası yükle                           (:load)
  :kaydet <dosya>   Çıktıyı dosyaya yaz (uzantı yoksa dilinkini ekler) (:save)
  :yardım           Bu yardım                                          (:help)
  :çık              Çıkış                                              (:quit, :q)

Örnek:
  x = 5
  eğer x > 3 ise
      yazdır "büyük"
  bitir
"""

_OPENERS = ("eğer", "döngü")


class ReplSession:
    def __init__(self, lang: str = "python", out: Callable[[str], None] = print,
                 input_fn: Callable[[str], str] = input):
        self.lang = resolve(lang).name
        self.out = out
        self.input_fn = input_fn
        self.buffer: list[str] = []
        self.running = True
        self._commands: dict[str, Callable[[str], None]] = {}
        for names, fn in (
            (("set",), self._cmd_set),
            (("dil", "lang"), self._cmd_lang),
            (("menu", "menü"), self._cmd_menu),
            (("diller", "langs"), self._cmd_langs),
            (("göster", "goster", "show"), lambda _: self.show()),
            (("hepsi", "all"), lambda _: self.show_all()),
            (("kod", "code"), self._cmd_code),
            (("geri", "undo"), self._cmd_undo),
            (("temizle", "clear"), self._cmd_clear),
            (("yükle", "yukle", "load"), self._cmd_load),
            (("kaydet", "save"), self._cmd_save),
            (("yardım", "yardim", "help", "h", "?"), lambda _: self.out(HELP)),
            (("çık", "cik", "quit", "exit", "q"), self._cmd_quit),
        ):
            for n in names:
                self._commands[n] = fn

    # --- durum -------------------------------------------------------
    @property
    def display(self) -> str:
        return resolve(self.lang).display

    @property
    def depth(self) -> int:
        """Açık blok sayısı (istem göstergesi için). Hatalı satırlar yok sayılır."""
        depth = 0
        for text in self.buffer:
            try:
                toks = tokenize(text)
            except TranspileError:
                continue
            if toks and toks[0].type.name == "KEYWORD":
                if toks[0].value in _OPENERS:
                    depth += 1
                elif toks[0].value == "bitir":
                    depth = max(0, depth - 1)
        return depth

    def prompt(self) -> str:
        if self.depth:
            return f"[{self.lang}] {'..' * self.depth}  "
        return f"[{self.lang}]>>> "

    # --- girdi işleme ------------------------------------------------
    def handle(self, line: str) -> None:
        stripped = line.strip()
        if stripped.startswith(":"):
            name, _, arg = stripped[1:].partition(" ")
            cmd = self._commands.get(name.lower())
            if cmd is None:
                self.out(f"Bilinmeyen komut: ':{name}'. ':yardım' yazın.")
            else:
                cmd(arg.strip())
        elif stripped == "":
            if self.buffer and self.depth == 0:
                self.show()
        else:
            self.buffer.append(line.rstrip())

    def source(self) -> str:
        return "\n".join(self.buffer) + "\n"

    def render(self, lang: str) -> str:
        return compile_source(self.source()).emit(lang)

    def show(self) -> None:
        if not self.buffer:
            self.out("(tampon boş — önce sözde kod yazın)")
            return
        try:
            code = self.render(self.lang)
        except TranspileError as exc:
            self.out(str(exc))
            return
        self.out(f"--- {self.display} ---")
        self.out(code.rstrip())

    def show_all(self) -> None:
        if not self.buffer:
            self.out("(tampon boş — önce sözde kod yazın)")
            return
        try:
            compiled = compile_source(self.source())
        except TranspileError as exc:
            self.out(str(exc))
            return
        for info in available_languages():
            self.out(f"\n=== {info.display} ===")
            self.out(compiled.emit(info.name).rstrip())

    # --- komutlar ----------------------------------------------------
    def set_language(self, name: str) -> bool:
        try:
            self.lang = resolve(name).name
        except KeyError as exc:
            self.out(str(exc.args[0]))
            return False
        self.out(f"Hedef dil: {self.display}")
        if self.buffer:
            self.show()
        return True

    def _cmd_set(self, arg: str) -> None:
        parts = arg.split()
        if len(parts) == 2 and parts[0].lower() in ("lang", "dil"):
            self.set_language(parts[1])
        else:
            self.out("Kullanım: :set lang <dil>")

    def _cmd_lang(self, arg: str) -> None:
        if arg:
            self.set_language(arg)
        else:
            self.out(f"Şu anki dil: {self.display}")

    def _cmd_langs(self, _: str) -> None:
        for info in available_languages():
            mark = "*" if info.name == self.lang else " "
            aliases = f"  ({', '.join(info.aliases)})" if info.aliases else ""
            self.out(f" {mark} {info.name:<11} {info.display}{aliases}")

    def _cmd_menu(self, _: str) -> None:
        langs = available_languages()
        for i, info in enumerate(langs, 1):
            mark = "*" if info.name == self.lang else " "
            self.out(f" {mark} {i}) {info.display}")
        try:
            choice = self.input_fn("Seçiminiz (numara veya ad): ").strip()
        except EOFError:
            return
        if choice.isdigit() and 1 <= int(choice) <= len(langs):
            self.set_language(langs[int(choice) - 1].name)
        elif choice:
            self.set_language(choice)

    def _cmd_code(self, _: str) -> None:
        if not self.buffer:
            self.out("(tampon boş)")
        for i, text in enumerate(self.buffer, 1):
            self.out(f"{i:>3} | {text}")

    def _cmd_undo(self, _: str) -> None:
        if self.buffer:
            self.out(f"Silindi: {self.buffer.pop()}")

    def _cmd_clear(self, _: str) -> None:
        self.buffer.clear()
        self.out("Tampon temizlendi.")

    def _cmd_load(self, arg: str) -> None:
        if not arg:
            self.out("Kullanım: :yükle <dosya>")
            return
        try:
            text = Path(arg).read_text(encoding="utf-8")
        except OSError as exc:
            self.out(f"Dosya okunamadı: {exc}")
            return
        self.buffer = text.rstrip("\n").split("\n")
        self.out(f"{len(self.buffer)} satır yüklendi.")
        self.show()

    def _cmd_save(self, arg: str) -> None:
        if not arg:
            self.out("Kullanım: :kaydet <dosya>")
            return
        try:
            code = self.render(self.lang)
        except TranspileError as exc:
            self.out(str(exc))
            return
        path = Path(arg)
        if not path.suffix:
            path = path.with_suffix(resolve(self.lang).ext)
        path.write_text(code, encoding="utf-8")
        self.out(f"Kaydedildi: {path}")

    def _cmd_quit(self, _: str) -> None:
        self.running = False


def run_repl(lang: str = "python") -> None:
    session = ReplSession(lang)
    session.out(f"Türkçe Sözde Kod Dönüştürücü — hedef: {session.display}. ':yardım' ile komutlar.")
    while session.running:
        try:
            line = input(session.prompt())
        except (EOFError, KeyboardInterrupt):
            session.out("")
            break
        session.handle(line)
