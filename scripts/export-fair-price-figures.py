"""Encode the two approved imagegen cutouts without changing their artwork."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
manifest = ROOT / 'content/fair-price-artwork.json'
artwork = json.loads(manifest.read_text(encoding='utf-8'))
figures = []
for name in ['svetlana', 'sonya']:
    source = ROOT / f'artifacts/fair-price/{name}-separate-v1.png'
    output = ROOT / f'public/media/fair-price-{name}-v1.webp'
    with Image.open(source) as image:
        assert image.mode == 'RGBA' and image.getextrema()[3][0] == 0
        image.save(output, 'WEBP', quality=88, method=6)
        size = list(image.size)
    figures.append({'id': name, 'source': source.relative_to(ROOT).as_posix(),
                    'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                    'url': '/' + output.relative_to(ROOT / 'public').as_posix(),
                    'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                    'size': size, 'alpha': True})
artwork['separateFigures'] = {'asOf': '2026-11-15', 'generator': 'built-in image_gen',
                              'editTarget': artwork['source'],
                              'prompts': 'artifacts/fair-price/separate-figures-prompts.json',
                              'items': figures}
manifest.write_text(json.dumps(artwork, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Encoded two separate figures; the original duo is preserved.')
