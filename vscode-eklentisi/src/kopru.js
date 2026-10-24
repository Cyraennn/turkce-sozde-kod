"use strict";
// Python tarafındaki trc ile konuşan köprü. VS Code'a bağımlı değildir (node --test ile sınanır).
//
// Kaynak kod stdin'den gönderilir, sonuç `python -m transpiler - --json ...` çıktısından okunur.
// Çeviri mantığı tek yerde (Python paketi) kalır; eklenti yalnızca sonucu gösterir.

const { spawn } = require("child_process");
const path = require("path");

class KopruHatasi extends Error {
  /** @param {"python-yok"|"modul-yok"|"zaman-asimi"|"bilinmeyen"} tur */
  constructor(tur, mesaj) {
    super(mesaj);
    this.tur = tur;
  }
}

/**
 * @param {{python?: string, cwd?: string, ekYol?: string, zamanAsimiMs?: number}} secenek
 * @param {string[]} argumanlar  ör. ["--all"], ["-l", "rust"], ["--calistir"]
 * @param {string} kaynak        sözde kod metni
 * @returns {Promise<object>}    trc'nin JSON yanıtı ({kodlar}|{kod}|{cikti…}|{hata})
 */
function trcCagir(secenek, argumanlar, kaynak) {
  const python = secenek.python || "python";
  const env = { ...process.env, PYTHONIOENCODING: "utf-8", PYTHONUTF8: "1" };
  if (secenek.ekYol) {
    env.PYTHONPATH = secenek.ekYol + (env.PYTHONPATH ? path.delimiter + env.PYTHONPATH : "");
  }

  return new Promise((resolve, reject) => {
    let cocuk;
    try {
      cocuk = spawn(python, ["-m", "transpiler", "-", "--json", ...argumanlar], {
        cwd: secenek.cwd || undefined,
        env,
        windowsHide: true,
      });
    } catch (e) {
      reject(new KopruHatasi("python-yok", `Python başlatılamadı ("${python}"): ${e.message}`));
      return;
    }

    const cikti = [], hata = [];
    const zamanlayici = setTimeout(() => {
      cocuk.kill();
      reject(new KopruHatasi("zaman-asimi", "trc zamanında yanıt vermedi."));
    }, secenek.zamanAsimiMs || 20000);

    cocuk.stdout.on("data", d => cikti.push(d));
    cocuk.stderr.on("data", d => hata.push(d));
    cocuk.on("error", e => {
      clearTimeout(zamanlayici);
      reject(e.code === "ENOENT"
        ? new KopruHatasi("python-yok",
            `Python bulunamadı ("${python}"). 'trc.python' ayarına yorumlayıcının yolunu yazın.`)
        : new KopruHatasi("bilinmeyen", e.message));
    });
    cocuk.on("close", kod => {
      clearTimeout(zamanlayici);
      const metin = Buffer.concat(cikti).toString("utf8");
      try {
        resolve(JSON.parse(metin));
      } catch {
        const hataMetni = Buffer.concat(hata).toString("utf8").trim();
        if (/No module named ['"]?transpiler/.test(hataMetni)) {
          reject(new KopruHatasi("modul-yok",
            "Python 'transpiler' paketini bulamadı. Proje klasöründe 'pip install -e .' " +
            "çalıştırın ya da 'trc.transpilerYolu' ayarına proje klasörünü yazın."));
        } else {
          reject(new KopruHatasi("bilinmeyen",
            `trc beklenmedik bir yanıt verdi (çıkış kodu ${kod}). ${hataMetni.slice(-400)}`));
        }
      }
    });

    cocuk.stdin.on("error", () => {});   // süreç erken kapanırsa EPIPE'i yut; 'close' raporlar
    cocuk.stdin.end(kaynak, "utf8");
  });
}

module.exports = { trcCagir, KopruHatasi };
