"use strict";
// Çalıştırma: node --test vscode-eklentisi/test/kopru.test.js   (Python ve trc gerekli)

const test = require("node:test");
const assert = require("node:assert");
const path = require("path");
const { trcCagir, KopruHatasi } = require("../src/kopru");

const KOK = path.resolve(__dirname, "..", "..");   // transpiler paketini içeren klasör
const secenek = { python: process.env.TRC_PYTHON || "python", cwd: KOK };

test("tüm dillere çevirir ve Türkçe karakterleri korur", async () => {
  const r = await trcCagir(secenek, ["--all"], 'şehir = "İzmir"\nyazdır "Gün: " + şehir\n');
  assert.deepStrictEqual(Object.keys(r.kodlar).sort(),
    ["cpp", "dart", "go", "java", "javascript", "python", "rust"]);
  assert.match(r.kodlar.python, /sehir = "İzmir"/);
});

test("hatayı satır ve sütunla döndürür", async () => {
  const r = await trcCagir(secenek, ["--all"], "x = 5\neğer x > 3\nbitir\n");
  assert.strictEqual(r.hata.satir, 2);
  assert.ok(r.hata.sutun > 0);
  assert.match(r.hata.metin, /'ise' bekleniyordu/);
});

test("programı çalıştırır", async () => {
  const r = await trcCagir(secenek, ["--calistir"], 'yazdır "çıktı " + (7 / 2)\n');
  assert.strictEqual(r.cikti.trim(), "çıktı 3.5");
  assert.strictEqual(r.zaman_asimi, false);
});

test("Python yoksa anlaşılır hata verir", async () => {
  await assert.rejects(
    trcCagir({ python: "olmayan-python-xyz", cwd: KOK }, ["--all"], "x = 1"),
    e => e instanceof KopruHatasi && e.tur === "python-yok");
});
