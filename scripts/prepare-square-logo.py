"""Prepare the authentic square badge without changing the approved circular favicon."""
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BRAND = Path('J:/Brandbooks/brand book СОЮЗ Барбершоп 2025/01_Логотип')
VECTOR = BRAND / 'Векторные файлы/Варианты логотипов/Логотип красный (квадрат).svg'
RASTER = BRAND / 'Растровые файлы/Логотип красный (квадрат).png'
CIRCLE = BRAND / 'Растровые файлы/Логотип красный (круг).png'
OUT = ROOT / 'artifacts/iteration66/seo-square-candidate'
NS = '{http://www.w3.org/2000/svg}'
RED = (196, 47, 42)
sha = lambda data: hashlib.sha256(data).hexdigest()
PROTECTED = ['content/seo-assets.json', 'content/seo.json', 'src/layouts/Document.astro',
             'public/brand/favicon-standard.svg', 'public/brand/favicon-red.svg',
             'public/brand/favicon-48.png', 'public/brand/favicon-96.png',
             'public/brand/favicon-180.png', 'public/media/og/soyuz-home.png',
             'scripts/prepare-social-preview.py']


def prepare_candidate():
    before = {path: sha((ROOT / path).read_bytes()) for path in PROTECTED}
    vector = VECTOR.read_bytes()
    raster = RASTER.read_bytes()
    circle = CIRCLE.read_bytes()
    assert sha(vector) == '6efb3830e369b37d0d34c4c86a39df4441ce7af9b5d17198532cfbe676843941'
    assert sha(raster) == '48906358d132f81940749497ff81a03b17cc4c62a2b0ef4bd2b89144f5c5e738'
    assert sha(circle) == 'fc706affe04c6c2a9c5ce15604245b6a589e9981dfaac9c4a3d2ecebf5d9e05e'
    root = ET.fromstring(vector)
    assert root.get('viewBox') == '0 0 1000 1000'
    parents = {child: parent for parent in root.iter() for child in parent}
    images = list(root.iter(NS + 'image'))
    assert len(images) == 1
    assert parents[images[0]].get('style') == 'clip-path:url(#id1)'
    assert float(images[0].get('x')) + float(images[0].get('width')) < 0
    assert len(root.find('.//' + NS + 'clipPath[@id="id1"]')) == 0
    clean, image_count = re.subn(rb'<image\b[^>]*?/>', b'', vector, flags=re.S)
    clean, doctype_count = re.subn(rb'<!DOCTYPE[^>]*>', b'', clean)
    assert image_count == 1 and doctype_count == 1
    parsed = ET.fromstring(clean)
    assert not any(list(parsed.iter(NS + tag)) for tag in ['image', 'text', 'script', 'foreignObject'])
    assert all(value.startswith('#') for node in parsed.iter() for name, value in node.attrib.items()
               if name.rsplit('}', 1)[-1] == 'href')
    # Removing hidden export metadata must not alter the native background or any logo contour.
    retained = ET.fromstring(vector)
    retained_parent = {child: parent for parent in retained.iter() for child in parent}
    for node in list(retained.iter(NS + 'image')):
        retained_parent[node].remove(node)
    # Corel marks inter-element indentation as xml:space="preserve"; ignore only that whitespace.
    elements = lambda tree: [(n.tag, sorted(n.attrib.items()), (n.text or '').strip(),
                              (n.tail or '').strip()) for n in tree.iter()]
    assert elements(retained) == elements(parsed)
    with Image.open(RASTER) as source, Image.open(CIRCLE) as original_circle:
        assert source.size == original_circle.size == (1000, 1000)
        image = source.convert('RGBA')
        assert image.getchannel('A').getextrema() == (255, 255)
        assert all(image.getpixel(point) == RED + (255,) for point in [(0, 0), (999, 0), (0, 999), (999, 999)])
        circle_on_red = Image.new('RGBA', (1000, 1000), RED + (255,))
        circle_on_red.alpha_composite(original_circle.convert('RGBA'))
        difference = ImageChops.difference(circle_on_red.convert('RGB'), image.convert('RGB'))
        assert difference.crop((100, 300, 900, 760)).getbbox() is None
        assert max(high for low, high in difference.getextrema()) <= 1
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'logo-square.svg').write_bytes(clean)
        shutil.copyfile(RASTER, OUT / 'logo-square-1000.png')
        outputs = []
        for size in [512, 192]:
            target = OUT / f'logo-square-{size}.png'
            image.convert('RGB').resize((size, size), Image.Resampling.LANCZOS).save(target, optimize=True)
            with Image.open(target) as check:
                check.load()
                assert check.format == 'PNG' and check.size == (size, size)
                assert all(check.getpixel(point) == RED for point in [(0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)])
            outputs.append(target)
        board = Image.new('RGB', (1120, 650), (255, 252, 247))
        draw = ImageDraw.Draw(board)
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
        draw.text((24, 18), 'Круг: действующий favicon', font=font, fill=(75, 75, 77))
        draw.text((584, 18), 'Квадрат: оригинал для бейджа', font=font, fill=(75, 75, 77))
        for x, picture in [(24, original_circle.convert('RGBA')), (584, image)]:
            picture = picture.resize((512, 512), Image.Resampling.LANCZOS)
            board.paste(picture, (x, 64), picture)
        draw.text((24, 600), 'Контуры, положение и цвета логотипа сохранены.', font=font, fill=(75, 75, 77))
        board.save(OUT / 'preview-board.png', optimize=True)
    files = [OUT / 'logo-square.svg', OUT / 'logo-square-1000.png', *outputs]
    assert sha((OUT / 'logo-square-1000.png').read_bytes()) == sha(raster)
    assert before == {path: sha((ROOT / path).read_bytes()) for path in PROTECTED}
    manifest = {
        'schemaVersion': 1, 'status': 'verified-original-square',
        'generator': 'scripts/prepare-square-logo.py', 'generatorSha256': sha(Path(__file__).read_bytes()),
        'sources': [{'path': p.as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
                    for p in [VECTOR, RASTER, CIRCLE]],
        'method': 'Native brandbook square SVG/PNG; no AI, drawing, font replacement, geometry change or circular crop',
        'svgCleanup': {'removedImages': image_count, 'removedExternalDoctype': doctype_count,
                       'imageReason': 'Off-canvas Corel preview under empty clipPath id1',
                       'allRemainingXmlIdentical': True, 'fontDependencies': 0},
        'raster': {'native1000BytesUnchanged': True, 'logoROIIdenticalToApprovedCircleOnRed': [100, 300, 900, 760],
                   'circleComparisonMaxChannelDelta': 1, 'opaqueSquareRedCorners': True,
                   'derivatives': 'Pillow Lanczos downscale; no colour grading or sharpening'},
        'files': [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
                   'sha256': sha(p.read_bytes()), 'width': 1000 if p.suffix == '.svg' else int(p.stem.rsplit('-', 1)[1]),
                   'height': 1000 if p.suffix == '.svg' else int(p.stem.rsplit('-', 1)[1])} for p in files],
        'protectedProductionFilesUnchanged': before,
    }
    (OUT / 'provenance.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def prepare_square_assets():
    manifest = prepare_candidate()
    destinations = {
        'logo-square.svg': 'public/brand/logo-square.svg',
        'logo-square-1000.png': 'public/media/og/soyuz-square.png',
        'logo-square-512.png': 'public/brand/logo-square-512.png',
        'logo-square-192.png': 'public/brand/logo-square-192.png',
    }
    files = []
    for row in manifest['files']:
        target = ROOT / destinations[Path(row['path']).name]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / row['path'], target)
        assert sha(target.read_bytes()) == row['sha256']
        files.append({**row, 'path': target.relative_to(ROOT).as_posix()})
    assert manifest['protectedProductionFilesUnchanged'] == {
        path: sha((ROOT / path).read_bytes()) for path in PROTECTED
    }
    return {key: value for key, value in manifest.items()
            if key not in ['status', 'files', 'protectedProductionFilesUnchanged']} | {'files': files}


if __name__ == '__main__':
    result = prepare_square_assets()
    print(json.dumps({'status': 'prepared', 'files': result['files'],
                      'circularFaviconAndLegacyPreviewUnchanged': True}, ensure_ascii=False))
