"""Eklentiyi .vsix olarak paketler (vsce/npm gerektirmez).

    python vscode-eklentisi/paketle.py          # yalnızca paketle
    python vscode-eklentisi/paketle.py --kur    # paketle ve VS Code'a kur

.vsix, içinde [Content_Types].xml, extension.vsixmanifest ve extension/ klasörü bulunan
bir ZIP dosyasıdır; burada aynı düzen elle kurulur.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

KOK = Path(__file__).resolve().parent
DAHIL = ["package.json", "language-configuration.json", "README.md",
         "src", "syntaxes", "snippets", "icons"]

CONTENT_TYPES = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension=".json" ContentType="application/json"/>
  <Default Extension=".js" ContentType="application/javascript"/>
  <Default Extension=".svg" ContentType="image/svg+xml"/>
  <Default Extension=".md" ContentType="text/markdown"/>
  <Default Extension=".vsixmanifest" ContentType="text/xml"/>
</Types>
"""


def manifest(pkg: dict) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011"
                 xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="{pkg['name']}" Version="{pkg['version']}" Publisher="{pkg['publisher']}"/>
    <DisplayName>{escape(pkg['displayName'])}</DisplayName>
    <Description xml:space="preserve">{escape(pkg['description'])}</Description>
    <Categories>{escape(','.join(pkg.get('categories', [])))}</Categories>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{pkg['engines']['vscode']}"/>
      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="workspace"/>
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
  </Assets>
</PackageManifest>
"""


def paketle() -> Path:
    pkg = json.loads((KOK / "package.json").read_text(encoding="utf-8"))
    hedef = KOK / f"{pkg['name']}-{pkg['version']}.vsix"
    with zipfile.ZipFile(hedef, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("extension.vsixmanifest", manifest(pkg))
        for ad in DAHIL:
            yol = KOK / ad
            dosyalar = [yol] if yol.is_file() else sorted(p for p in yol.rglob("*") if p.is_file())
            for dosya in dosyalar:
                z.write(dosya, "extension/" + dosya.relative_to(KOK).as_posix())
    return hedef


def main() -> int:
    vsix = paketle()
    print(f"Paket hazır: {vsix}")
    if "--kur" in sys.argv:
        code = shutil.which("code")
        if not code:
            print("'code' komutu bulunamadı; VS Code'da 'Extensions: Install from VSIX…' ile kurun.")
            return 1
        subprocess.run([code, "--install-extension", str(vsix), "--force"], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
