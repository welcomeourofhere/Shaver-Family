"""Prepare retained construction artwork revisions without upscaling."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps, features

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'public/media/gifts'
JOBS = {
    'poster': {
        'artifact': 'construction-poster', 'stem': 'construction-poster',
        'alt': 'Строители возводят барбершоп: леса, подъёмный кран и отделка нового зала.',
        'palette': {'red': '#c42f2a', 'blue': '#52658c', 'yellow': '#ffcc29',
                    'paper': '#f6e8d3', 'ink': '#4b4b4d'},
    },
    'worker2': {
        'artifact': 'construction-worker2', 'stem': 'construction-worker',
        'alt': 'Рабочий с малярным валиком, минималистичный рисунок в серых тонах.',
        'palette': {'background': 'neutral light gray', 'figure': 'medium and dark gray'},
    },
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=JOBS, default='worker2')
    args = parser.parse_args()
    job = JOBS[args.variant]
    ART = ROOT / 'artifacts/iteration66' / job['artifact']
    SOURCE = ART / 'original.png'
    assert SOURCE.is_file(), 'Save the selected built-in image_gen output as original.png first.'
    TARGET.mkdir(parents=True, exist_ok=True)
    with Image.open(SOURCE) as opened:
        image = ImageOps.exif_transpose(opened).convert('RGB')
        assert image.width * 2 == image.height * 3, image.size
        assert image.width >= 1440, 'The requested runtime variants must not upscale the source.'
        entry = {
            'generator': 'Built-in image_gen',
            'revision': args.variant,
            'asOf': '2026-11-16',
            'source': SOURCE.relative_to(ROOT).as_posix(),
            'sourceSha256': sha(SOURCE),
            'sourceWidth': image.width,
            'sourceHeight': image.height,
            'sourceBytes': SOURCE.stat().st_size,
            'prompt': (ART / 'prompt.txt').relative_to(ROOT).as_posix(),
            'alt': job['alt'],
            'decorative': True,
            'runtime': {'format': 'WebP', 'quality': 82, 'method': 6,
                        'resampling': 'Lanczos', 'webpVersion': features.version_module('webp')},
            'variants': [],
        }
        for width in [480, 960, 1440]:
            size = (width, round(image.height * width / image.width))
            assert size[0] <= image.width and size[1] <= image.height
            output = TARGET / f"{job['stem']}-{width}.webp"
            image.resize(size, Image.Resampling.LANCZOS).save(output, 'WEBP', quality=82, method=6)
            with Image.open(output) as check:
                assert check.size == size and check.format == 'WEBP', output
                check.load()
            entry['variants'].append({
                'url': '/' + output.relative_to(ROOT / 'public').as_posix(),
                'width': size[0], 'height': size[1],
                'bytes': output.stat().st_size, 'sha256': sha(output),
            })
    manifest = ROOT / 'content/construction-poster.json' if args.variant == 'worker2' else ART / 'runtime-manifest.json'
    manifest.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    metadata = ART / ('metadata.json' if args.variant == 'worker2' else 'metadata-rebuilt.json')
    metadata.write_text(json.dumps({
        'generator': entry['generator'], 'mode': 'built-in generation',
        'inputImages': [], 'transparentBackground': False,
        'palette': job['palette'],
        'original': entry['source'], 'originalSha256': entry['sourceSha256'],
        'originalSize': [entry['sourceWidth'], entry['sourceHeight']],
        'prompt': entry['prompt'], 'manifest': manifest.relative_to(ROOT).as_posix(),
        'prepare': f'python -X utf8 scripts/prepare-construction-poster.py --variant {args.variant}',
        'productIntegration': 'Root owns Gifts markup and CSS; this script only prepares assets.',
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'manifest': str(manifest), 'sourceSize': image.size,
                      'variants': entry['variants']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
