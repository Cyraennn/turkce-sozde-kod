# trc — Türkçe Sözde Kod (VS Code eklentisi)

`.tr` dosyalarında Türkçe sözde kod yazın; eklenti çevirmeyi ve çalıştırmayı üstlenir.

| Özellik | Nasıl |
|---|---|
| Renklendirme, otomatik girinti, katlama | `.tr` dosyası açınca kendiliğinden |
| Hataları anında gösterme | Yazarken kırmızı dalgalı çizgi + Sorunlar paneli |
| Canlı çeviri yan panelde | Başlıktaki önizleme düğmesi ya da **Ctrl+K V** |
| Hedef dili değiştirme | Sağ alttaki **trc → Python** yazısına tıklayın |
| Çalıştırma | Başlıktaki ▶ ya da **Ctrl+Enter** (çıktı "trc" panelinde) |
| 7 dili dosyalara kaydetme | Komut paleti → *trc: 7 dile çevirip dosyalara kaydet* |
| Tarayıcı arayüzü | Komut paleti → *trc: Tarayıcı arayüzünü aç* |
| Kod kalıpları | `eğer`, `eğerd`, `eğerz`, `döngü`, `döngük`, `yazdır` (ASCII: `eger`, `dongu`, `yazdir`) |

## Gereksinim
Python 3.10+ ve trc paketi: proje klasöründe `pip install -e .`
Kurulu değilse **trc.transpilerYolu** ayarına proje klasörünü yazmanız yeterli.

## Ayarlar
`trc.hedefDil`, `trc.python`, `trc.transpilerYolu`, `trc.canliKontrol`, `trc.gecikme`

## Geliştirme
```bash
node --test vscode-eklentisi/test/kopru.test.js   # köprü testleri
python vscode-eklentisi/paketle.py --kur   # .vsix üret ve VS Code'a kur
```
