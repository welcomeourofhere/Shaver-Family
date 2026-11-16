"""Export selected photographs and certificate artwork; SVG icons use vector-export-gifts.py."""
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BRAND = Path("J:/Brandbooks/brand book СОЮЗ Барбершоп 2025")
GIFTS = Path("C:/Users/Lenovo/AppData/Local/Temp/codex-clipboard-68de5f2a-58f5-4130-8853-b247d0e1949d.png")
PDF = BRAND / "05_Базовая палиграфия/Подарочные карты и сертификаты/Подарочные карты (Только для просмотра).pdf"
PIONEER = ROOT / "archive/legacy/assets/images/decor/pioneer.webp"
HERO = ROOT / "archive/legacy/assets/images/interior/170A0800.jpg"
OUT = (ROOT / "public/reference").resolve()


def certificate_1000(page):
    """Reuse the source's outlined zero; the archived PDF currently says1500."""
    svg = ET.fromstring(page.get_svg_image())
    paths = list(svg.iter("{http://www.w3.org/2000/svg}path"))
    zero = next(p for p in paths if p.get("d", "").startswith("M90.0037 142.5166"))
    five = next(p for p in paths if p.get("d", "").startswith("M47.3797 150.9647"))
    assert zero.get("fill") == five.get("fill") == "#c11718"
    five.set("d", zero.get("d"))
    five.set("transform", "matrix(1,0,0,-1,-29.4239,255.1181)")
    vector = ET.tostring(svg, encoding="utf-8")
    native = ROOT / "artifacts/certificates/certificate-1000.svg"
    native.parent.mkdir(parents=True, exist_ok=True)
    native.write_bytes(vector)
    with fitz.open(stream=vector, filetype="svg") as document:
        p = document[0]
        pix = p.get_pixmap(matrix=fitz.Matrix(900 / p.rect.width, 900 / p.rect.width), alpha=False)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for source in (GIFTS, PDF, PIONEER, HERO):
        if not source.is_file():
            raise FileNotFoundError(source)
    if not OUT.is_relative_to(ROOT):
        raise ValueError("Output escapes project")
    OUT.mkdir(parents=True, exist_ok=True)
    path = ROOT / "content/reference-assets.json"
    archived_manifest = ROOT / "archive/reference-old/reference-assets-before-grid-2026-11-04.json"
    if path.is_file() and not archived_manifest.exists():
        archived_manifest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, archived_manifest)
    manifest = {"status": "local-template-reference-assets", "giftPhotoIds": [4], "images": {}, "gaps": [
        "Gift photos 1,2,3,5,6 are unavailable. Preserve their illustrations on interaction; do not substitute unrelated products.",
        "Gift photo4 is a 188x188 exact crop of the latest owner reference. The original independent photograph was not found.",
        "Pioneer is an unchanged legacy transparent asset. The same artwork is visible in the source CDR bitmap, but the legacy background-removal process is undocumented.",
        "Printed certificate contacts and denominations are historical artwork, not verification of current business conditions.",
        "Hero exact original matches the owner's current screenshot2 choice. The same filename is filed under the brandbook's older 'Не исопльзовать' directory. The owner's latest explicit selection overrides that older folder label for this scoped local template."
    ]}

    def record(asset_id, source, operation):
        target = OUT / f"{asset_id}.webp"
        with Image.open(target) as image:
            manifest["images"][asset_id] = {"url": f"/reference/{target.name}", "source": str(source.resolve()), "sourceSha256": sha(source), "operation": operation, "width": image.width, "height": image.height, "bytes": target.stat().st_size, "sha256": sha(target)}

    with Image.open(GIFTS) as screenshot:
        box = (222,483,410,671)
        screenshot.crop(box).convert("RGB").save(OUT / "gift-photo-4.webp", "WEBP", lossless=True)
        record("gift-photo-4", GIFTS, {"type": "latest-owner-reference-photo-crop", "box": box, "nativeResolution": True})
    with fitz.open(PDF) as document:
        for asset_id, page_number in (("certificate-front",0),("certificate-1000",1),("certificate-back",2),("certificate-3000",3)):
            page = document[page_number]
            if asset_id == "certificate-1000":
                image = certificate_1000(page)
            else:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(900 / page.rect.width, 900 / page.rect.width), alpha=False)
                image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            image.save(OUT / f"{asset_id}.webp", "WEBP", quality=92, method=6)
            record(asset_id, PDF, {"type": "pdf-page-render", "page": page_number + 1, "renderWidth": 900, "historicalPrintedContent": True})
            if asset_id == "certificate-1000":
                manifest["images"][asset_id]["operation"].update(type="native-vector-denomination-adaptation", fromAmount=1500, toAmount=1000, glyphSource="Zero outline from the same PDF page, replacing only the five outline", editable="artifacts/certificates/certificate-1000.svg")
    shutil.copyfile(PIONEER, OUT / "pioneer.webp")
    record("pioneer", PIONEER, {"type": "unchanged-legacy-artwork", "alphaPreserved": True, "lineage": "Visual artwork match to Soviet pioneer poster embedded in brandbook CDR site; legacy extraction process undocumented."})
    assert sha(OUT / "pioneer.webp") == sha(PIONEER)
    with Image.open(HERO) as image:
        image = image.convert("RGB")
        image.thumbnail((1440,1920), Image.Resampling.LANCZOS)
        image.save(OUT / "hero.webp", "WEBP", quality=88, method=6)
    record("hero", HERO, {"type": "resize-exact-owner-selected-photo", "exactReferenceMatch": "Owner screenshot2, hand at lips, burgundy hair, blue shirt, red cabinet and carpet", "brandbookSource": str(BRAND / "07_Фотографии/Фотосет 2025 №1/Не исопльзовать/170A0800.jpg"), "archivalFolderFlag": "Не исопльзовать", "currentSelection": "Owner explicitly selected this exact photograph in screenshot2; latest explicit selection overrides the old unused-folder label for this scoped local template", "brandbookAndLegacyByteIdenticalVerified": True})
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(manifest['images'])} selected reference assets; documented gaps in {path}")


if __name__ == "__main__":
    main()
