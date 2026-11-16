"""Export the eight selected brand photos, two unchanged logos and four fonts."""
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageOps


PROJECT = Path(__file__).resolve().parents[1]
SOURCE = Path("J:/Brandbooks/brand book СОЮЗ Барбершоп 2025").resolve(strict=True)
PHOTOS = "07_Фотографии/Фотосет 2025 №1"
PHOTO_FILES = {
    "hero-light": "170A1142.jpg",
    "hero-poster": "170A1624.jpg",
    "team": "170A1587.jpg",
    "hero-dark": "170A0736.jpg",
    "work-texture": "170A0240.jpg",
    "work-fade": "170A1068.jpg",
    "work-classic": "170A1840.jpg",
    "work-back": "170A1937.jpg",
}
COPIES = {
    "brand/logo-light.svg": "01_Логотип/Векторные файлы/Варианты логотипов/Логотип белый (прозрачный).svg",
    "brand/logo-dark.svg": "01_Логотип/Векторные файлы/Варианты логотипов/Логотип черный (прозрачный).svg",
    "fonts/Manrope-Regular.woff2": "02_Шрифты/Manrope Static/Manrope-Regular.woff2",
    "fonts/Manrope-Medium.woff2": "02_Шрифты/Manrope Static/Manrope-Medium.woff2",
    "fonts/Manrope-SemiBold.woff2": "02_Шрифты/Manrope Static/Manrope-Semibold.woff2",
    "fonts/Molot.ttf": "02_Шрифты/Molot/Molot.ttf",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_file(relative):
    path = (SOURCE / relative).resolve(strict=True)
    if not path.is_relative_to(SOURCE) or not path.is_file():
        raise ValueError(f"Invalid source file: {relative}")
    return path


def destination(relative):
    path = (PROJECT / "public" / relative).resolve()
    permitted = [(PROJECT / "public" / name).resolve() for name in ("media", "brand", "fonts")]
    if not any(path.is_relative_to(directory) for directory in permitted):
        raise ValueError(f"Invalid output path: {relative}")
    if not path.is_relative_to(PROJECT):
        raise ValueError(f"Output escapes project: {relative}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def file_record(path):
    return {"url": "/" + path.relative_to(PROJECT / "public").as_posix(),
            "bytes": path.stat().st_size, "sha256": digest(path)}


def main():
    # Check the complete fixed allowlist before writing any asset.
    for name in PHOTO_FILES.values():
        source_file(f"{PHOTOS}/{name}")
    for relative in COPIES.values():
        source_file(relative)

    manifest = {"sourceRoot": str(SOURCE), "images": {}, "logos": {}, "fonts": {}}
    for asset_id, name in PHOTO_FILES.items():
        relative = f"{PHOTOS}/{name}"
        original = source_file(relative)
        with Image.open(original) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
            width, height = image.size
            entry = {"source": relative, "sourceSha256": digest(original),
                     "sourceWidth": width, "sourceHeight": height, "variants": []}
            for requested_width in (640, 1440):
                size = (min(requested_width, width), round(height * min(requested_width, width) / width))
                output = destination(f"media/{asset_id}-{requested_width}.webp")
                image.resize(size, Image.Resampling.LANCZOS).save(output, "WEBP", quality=85, method=6)
                with Image.open(output) as verified:
                    assert verified.format == "WEBP" and verified.size == size
                entry["variants"].append({**file_record(output), "width": size[0], "height": size[1]})
            assert digest(original) == entry["sourceSha256"]
            manifest["images"][asset_id] = entry

    for relative, source_relative in COPIES.items():
        original = source_file(source_relative)
        output = destination(relative)
        shutil.copyfile(original, output)
        assert digest(original) == digest(output)
        kind = "logos" if relative.startswith("brand/") else "fonts"
        manifest[kind][output.stem] = {"source": source_relative, "sourceSha256": digest(original), **file_record(output)}

    assert len(manifest["images"]) == 8
    assert sum(len(entry["variants"]) for entry in manifest["images"].values()) == 16
    # The sole metadata output is fixed and remains inside the project.
    manifest_path = (PROJECT / "content/assets.json").resolve()
    if not manifest_path.is_relative_to(PROJECT):
        raise ValueError("Manifest escapes project")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Verified: 16 WebP exports, 2 unchanged SVG logos, 4 unchanged WOFF2 fonts; content/assets.json written.")


if __name__ == "__main__":
    main()
