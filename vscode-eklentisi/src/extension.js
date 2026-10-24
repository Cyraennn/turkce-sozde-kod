"use strict";
// trc VS Code eklentisi.
//
//  • Yazarken çeviri: her değişiklikten (gecikmeli) sonra 7 dilin hepsi tek çağrıda üretilir,
//    sonuç belleğe alınır. Hata varsa satır/sütunu kırmızı dalgalı çizgiyle işaretlenir.
//  • Yan panel: "trc-cikti:" şemalı sanal belge. Yolu hedef dilin uzantısıyla bittiği için
//    (ör. ornek.rs) VS Code kendi renklendirmesini uygular.
//  • Çalıştır: Python çevirisi yalıtılmış süreçte çalıştırılır, çıktı "trc" panelinde görünür.

const vscode = require("vscode");
const path = require("path");
const { trcCagir } = require("./kopru");

const DIL_ID = "turkce-sozde-kod";
const SEMA = "trc-cikti";

// Python tarafındaki kayıt defteriyle aynı sıra. vscodeId: VS Code'un dil kimliği.
const DILLER = [
  { ad: "cpp",        gorunen: "C++",        uzanti: ".cpp",  vscodeId: "cpp",        yorum: "//" },
  { ad: "python",     gorunen: "Python",     uzanti: ".py",   vscodeId: "python",     yorum: "#"  },
  { ad: "dart",       gorunen: "Dart",       uzanti: ".dart", vscodeId: "dart",       yorum: "//" },
  { ad: "java",       gorunen: "Java",       uzanti: ".java", vscodeId: "java",       yorum: "//" },
  { ad: "rust",       gorunen: "Rust",       uzanti: ".rs",   vscodeId: "rust",       yorum: "//" },
  { ad: "go",         gorunen: "Go",         uzanti: ".go",   vscodeId: "go",         yorum: "//" },
  { ad: "javascript", gorunen: "JavaScript", uzanti: ".js",   vscodeId: "javascript", yorum: "//" },
];
const dilBilgisi = ad => DILLER.find(d => d.ad === ad) || DILLER[1];

/** kaynak uri → { sonIyi: {dil: kod}|null, hata: object|null } */
const sonuclar = new Map();
const zamanlayicilar = new Map();
const icerikDegisti = new vscode.EventEmitter();
let tanilar, durumCubugu, cikisKanali;
let kopruUyarisiGosterildi = false;

/* ------------------------------------------------------------------ yardımcılar */

function ayar(anahtar) {
  return vscode.workspace.getConfiguration("trc").get(anahtar);
}

function kopruSecenekleri(uri) {
  const klasor = uri && vscode.workspace.getWorkspaceFolder(uri);
  const cwd = klasor ? klasor.uri.fsPath
    : uri && uri.scheme === "file" ? path.dirname(uri.fsPath) : undefined;
  return { python: ayar("python"), ekYol: ayar("transpilerYolu") || undefined, cwd };
}

function kopruHatasiniBildir(e) {
  if (kopruUyarisiGosterildi) return;      // her tuşta aynı uyarıyı göstermeyelim
  kopruUyarisiGosterildi = true;
  vscode.window.showErrorMessage(`trc: ${e.message}`, "Ayarları aç").then(secim => {
    if (secim) vscode.commands.executeCommand("workbench.action.openSettings", "trc.");
  });
}

function trcBelgesiMi(doc) {
  return doc && doc.languageId === DIL_ID;
}

function ciktiUri(kaynakUri, dil) {
  const bilgi = dilBilgisi(dil);
  const ad = path.basename(kaynakUri.path, path.extname(kaynakUri.path)) || "program";
  const query = new URLSearchParams({ kaynak: kaynakUri.toString(), dil }).toString();
  return vscode.Uri.from({ scheme: SEMA, path: "/" + ad + bilgi.uzanti, query });
}

function ciktiParametreleri(uri) {
  const q = new URLSearchParams(uri.query);
  return { kaynak: q.get("kaynak"), dil: q.get("dil") };
}

function acikKaynakBelgesi(kaynakAnahtari) {
  return vscode.workspace.textDocuments.find(d => d.uri.toString() === kaynakAnahtari);
}

/* ------------------------------------------------------------------ çeviri + tanılar */

function cevirmeyiPlanla(doc, hemen = false) {
  if (!trcBelgesiMi(doc)) return;
  const anahtar = doc.uri.toString();
  clearTimeout(zamanlayicilar.get(anahtar));
  zamanlayicilar.set(anahtar, setTimeout(() => cevir(doc), hemen ? 0 : ayar("gecikme")));
}

async function cevir(doc) {
  const anahtar = doc.uri.toString();
  const surum = doc.version;
  let yanit;
  try {
    yanit = await trcCagir(kopruSecenekleri(doc.uri), ["--all"], doc.getText());
  } catch (e) {
    kopruHatasiniBildir(e);
    return;
  }
  kopruUyarisiGosterildi = false;
  if (doc.isClosed || doc.version !== surum) return;   // bu arada yeni bir çeviri planlandı

  const onceki = sonuclar.get(anahtar);
  if (yanit.hata) {
    sonuclar.set(anahtar, { sonIyi: onceki ? onceki.sonIyi : null, hata: yanit.hata });
    tanilar.set(doc.uri, ayar("canliKontrol") ? [taniOlustur(doc, yanit.hata)] : []);
  } else {
    sonuclar.set(anahtar, { sonIyi: yanit.kodlar, hata: null });
    tanilar.delete(doc.uri);
  }
  // Bu kaynağa ait açık önizlemeleri yenile.
  for (const d of vscode.workspace.textDocuments) {
    if (d.uri.scheme === SEMA && ciktiParametreleri(d.uri).kaynak === anahtar) icerikDegisti.fire(d.uri);
  }
}

function taniOlustur(doc, hata) {
  const satir = Math.min(Math.max((hata.satir || 1) - 1, 0), doc.lineCount - 1);
  const satirMetni = doc.lineAt(satir);
  let aralik;
  if (hata.sutun) {
    // trc sütunları 1 tabanlıdır; satır sonunu işaret edebilir (ör. "'ise' bekleniyordu").
    const uzunluk = satirMetni.text.length;
    const sutun = Math.min(hata.sutun - 1, uzunluk);
    const kelime = doc.getWordRangeAtPosition(new vscode.Position(satir, sutun));
    aralik = kelime || (sutun < uzunluk
      ? new vscode.Range(satir, sutun, satir, sutun + 1)
      : new vscode.Range(satir, Math.max(uzunluk - 1, 0), satir, uzunluk));
  } else {
    aralik = new vscode.Range(satir, satirMetni.firstNonWhitespaceCharacterIndex, satir, satirMetni.text.length);
  }
  const tani = new vscode.Diagnostic(aralik, hata.mesaj || hata.metin, vscode.DiagnosticSeverity.Error);
  tani.source = "trc";
  if (hata.tur) tani.code = hata.tur;
  return tani;
}

/* ------------------------------------------------------------------ yan panel (sanal belge) */

const icerikSaglayici = {
  onDidChange: icerikDegisti.event,
  provideTextDocumentContent(uri) {
    const { kaynak, dil } = ciktiParametreleri(uri);
    const bilgi = dilBilgisi(dil);
    const sonuc = sonuclar.get(kaynak);
    if (!sonuc) {
      const doc = acikKaynakBelgesi(kaynak);
      if (doc) cevirmeyiPlanla(doc, true);
      return `${bilgi.yorum} Çevriliyor…\n`;
    }
    if (!sonuc.sonIyi) return `${bilgi.yorum} ${sonuc.hata.metin}\n`;
    const kod = sonuc.sonIyi[dil] || "";
    return sonuc.hata
      ? `${bilgi.yorum} ⚠ ${sonuc.hata.metin}\n${bilgi.yorum} (son geçerli çeviri gösteriliyor)\n\n${kod}`
      : kod;
  },
};

async function onizlemeAc(kaynakUri, dil, viewColumn = vscode.ViewColumn.Beside) {
  const doc = await vscode.workspace.openTextDocument(ciktiUri(kaynakUri, dil));
  const hedef = dilBilgisi(dil).vscodeId;
  if (doc.languageId !== hedef && (await vscode.languages.getLanguages()).includes(hedef)) {
    await vscode.languages.setTextDocumentLanguage(doc, hedef);
  }
  await vscode.window.showTextDocument(doc, { viewColumn, preserveFocus: true, preview: false });
}

/** Hedef dil değişince açık önizlemeleri yeni dilin belgesiyle değiştir. */
async function onizlemeleriYenile() {
  const dil = ayar("hedefDil");
  for (const grup of vscode.window.tabGroups.all) {
    for (const sekme of grup.tabs) {
      const uri = sekme.input && sekme.input.uri;
      if (!uri || uri.scheme !== SEMA) continue;
      const p = ciktiParametreleri(uri);
      if (p.dil === dil) continue;
      await vscode.window.tabGroups.close(sekme, true);
      await onizlemeAc(vscode.Uri.parse(p.kaynak), dil, grup.viewColumn);
    }
  }
}

/* ------------------------------------------------------------------ komutlar */

function etkinTrcBelgesi() {
  const doc = vscode.window.activeTextEditor && vscode.window.activeTextEditor.document;
  if (trcBelgesiMi(doc)) return doc;
  vscode.window.showWarningMessage("trc: Önce bir Türkçe sözde kod (.tr) dosyası açın.");
  return null;
}

async function komutOnizle() {
  const doc = etkinTrcBelgesi();
  if (doc) await onizlemeAc(doc.uri, ayar("hedefDil"));
}

async function komutDilSec() {
  const simdiki = ayar("hedefDil");
  const secim = await vscode.window.showQuickPick(
    DILLER.map(d => ({
      label: d.gorunen,
      description: d.ad === simdiki ? "şu anki" : d.uzanti,
      ad: d.ad,
    })),
    { placeHolder: "Sözde kod hangi dile çevrilsin?" });
  if (!secim || secim.ad === simdiki) return;
  await vscode.workspace.getConfiguration("trc").update("hedefDil", secim.ad, vscode.ConfigurationTarget.Global);
}

async function komutCalistir() {
  const doc = etkinTrcBelgesi();
  if (!doc) return;
  cikisKanali.clear();
  cikisKanali.show(true);
  cikisKanali.appendLine(`▶ ${path.basename(doc.uri.path)} — Python çevirisiyle çalıştırılıyor…`);
  let r;
  try {
    r = await trcCagir(kopruSecenekleri(doc.uri), ["--calistir"], doc.getText());
  } catch (e) {
    cikisKanali.appendLine(`✖ ${e.message}`);
    return;
  }
  if (r.hata) {
    cikisKanali.appendLine(`✖ ${r.hata.metin}`);
    return;
  }
  cikisKanali.appendLine("");
  if (r.cikti) cikisKanali.append(r.cikti);
  if (r.hata_cikti) cikisKanali.append(r.hata_cikti);
  if (!r.cikti && !r.hata_cikti) cikisKanali.appendLine("(program bir şey yazdırmadı)");
  cikisKanali.appendLine("");
  cikisKanali.appendLine(r.zaman_asimi
    ? "⏱ 5 saniye sınırı aşıldı; sonsuz döngü olabilir."
    : `✔ Bitti (${r.sure_ms} ms)`);
}

async function komutHepsiniKaydet() {
  const doc = etkinTrcBelgesi();
  if (!doc) return;
  if (doc.uri.scheme !== "file") {
    vscode.window.showWarningMessage("trc: Önce dosyayı diske kaydedin.");
    return;
  }
  let r;
  try {
    r = await trcCagir(kopruSecenekleri(doc.uri), ["--all"], doc.getText());
  } catch (e) {
    vscode.window.showErrorMessage(`trc: ${e.message}`);
    return;
  }
  if (r.hata) {
    vscode.window.showErrorMessage(`trc: ${r.hata.metin}`);
    return;
  }
  const ad = path.basename(doc.uri.fsPath, path.extname(doc.uri.fsPath));
  const klasor = vscode.Uri.joinPath(vscode.Uri.file(path.dirname(doc.uri.fsPath)), `${ad}_cikti`);
  await vscode.workspace.fs.createDirectory(klasor);
  for (const d of DILLER) {
    if (!(d.ad in r.kodlar)) continue;
    // Java'da genel sınıf adı dosya adıyla aynı olmalı.
    const dosya = d.ad === "java" ? "Main.java" : ad + d.uzanti;
    await vscode.workspace.fs.writeFile(vscode.Uri.joinPath(klasor, dosya), Buffer.from(r.kodlar[d.ad], "utf8"));
  }
  const secim = await vscode.window.showInformationMessage(
    `trc: ${Object.keys(r.kodlar).length} dosya yazıldı → ${ad}_cikti`, "Klasörü göster");
  if (secim) vscode.commands.executeCommand("revealInExplorer", klasor);
}

function komutArayuz() {
  const doc = vscode.window.activeTextEditor && vscode.window.activeTextEditor.document;
  const secenek = kopruSecenekleri(doc && doc.uri);
  const env = secenek.ekYol ? { PYTHONPATH: secenek.ekYol } : undefined;
  // Kabuk yerine Python'u doğrudan başlat: yol tırnaklama sorunları olmaz.
  const terminal = vscode.window.createTerminal({
    name: "trc arayüz",
    shellPath: secenek.python,
    shellArgs: ["-m", "transpiler", "--arayuz"],
    cwd: secenek.cwd,
    env,
  });
  terminal.show(true);
}

/* ------------------------------------------------------------------ durum çubuğu */

function durumCubugunuGuncelle() {
  const doc = vscode.window.activeTextEditor && vscode.window.activeTextEditor.document;
  const gorunsun = trcBelgesiMi(doc) || (doc && doc.uri.scheme === SEMA);
  if (!gorunsun) {
    durumCubugu.hide();
    return;
  }
  durumCubugu.text = `$(arrow-swap) trc → ${dilBilgisi(ayar("hedefDil")).gorunen}`;
  durumCubugu.show();
}

/* ------------------------------------------------------------------ yaşam döngüsü */

function activate(context) {
  tanilar = vscode.languages.createDiagnosticCollection("trc");
  cikisKanali = vscode.window.createOutputChannel("trc");
  durumCubugu = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  durumCubugu.command = "trc.dilSec";
  durumCubugu.tooltip = "trc hedef dili — değiştirmek için tıklayın";

  context.subscriptions.push(
    tanilar, cikisKanali, durumCubugu, icerikDegisti,
    vscode.workspace.registerTextDocumentContentProvider(SEMA, icerikSaglayici),
    vscode.commands.registerCommand("trc.onizle", komutOnizle),
    vscode.commands.registerCommand("trc.dilSec", komutDilSec),
    vscode.commands.registerCommand("trc.calistir", komutCalistir),
    vscode.commands.registerCommand("trc.hepsiniKaydet", komutHepsiniKaydet),
    vscode.commands.registerCommand("trc.arayuz", komutArayuz),

    vscode.workspace.onDidOpenTextDocument(doc => cevirmeyiPlanla(doc, true)),
    vscode.workspace.onDidChangeTextDocument(e => cevirmeyiPlanla(e.document)),
    vscode.workspace.onDidCloseTextDocument(doc => {
      if (!trcBelgesiMi(doc)) return;
      const anahtar = doc.uri.toString();
      clearTimeout(zamanlayicilar.get(anahtar));
      zamanlayicilar.delete(anahtar);
      tanilar.delete(doc.uri);
      // Önbelleği bırakıyoruz: önizleme açık kalırsa son çeviri görünmeye devam etsin.
    }),
    vscode.window.onDidChangeActiveTextEditor(durumCubugunuGuncelle),
    vscode.workspace.onDidChangeConfiguration(e => {
      if (e.affectsConfiguration("trc.hedefDil")) {
        durumCubugunuGuncelle();
        onizlemeleriYenile();
      }
      if (e.affectsConfiguration("trc.python") || e.affectsConfiguration("trc.transpilerYolu") ||
          e.affectsConfiguration("trc.canliKontrol")) {
        kopruUyarisiGosterildi = false;
        vscode.workspace.textDocuments.forEach(d => cevirmeyiPlanla(d, true));
      }
    }),
  );

  vscode.workspace.textDocuments.forEach(d => cevirmeyiPlanla(d, true));
  durumCubugunuGuncelle();
}

function deactivate() {
  for (const z of zamanlayicilar.values()) clearTimeout(z);
}

module.exports = { activate, deactivate };
