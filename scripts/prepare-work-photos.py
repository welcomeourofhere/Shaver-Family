"""Rebuild the curated public VK work photos from retained, hash-checked originals."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps, features

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'content/work-photos.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(manifest, root=ROOT):
    assert manifest['source'] == 'vk-public-wall' and manifest['ownerId'] == -210007626
    photos = manifest['photos']
    assert len({photo['photoId'] for photo in photos}) == len(photos), 'Duplicate photo'
    original_roots = {(root / 'artifacts/iteration66/vk-works-api' / folder).resolve()
                      for folder in ['originals', 'additional']}
    target = root / 'public/media/works'
    target.mkdir(parents=True, exist_ok=True)
    for photo in photos:
        source = (root / photo['sourceFile']).resolve()
        assert source.parent in original_roots, 'Original outside the retained photo directories'
        assert sha(source) == photo['sourceSha256'], f"Original changed: {photo['photoId']}"
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert('RGB')
            assert image.size == (photo['sourceWidth'], photo['sourceHeight'])
            photo['variants'] = []
            for width in [360, 720, 1080]:
                assert width <= image.width, 'Upscaling is not allowed'
                size = (width, round(image.height * width / image.width))
                output = target / f"vk-{photo['photoId']}-{width}.webp"
                image.resize(size, Image.Resampling.LANCZOS).save(output, 'WEBP', quality=82, method=6)
                with Image.open(output) as check:
                    assert check.format == 'WEBP' and check.size == size
                    check.load()
                photo['variants'].append({
                    'url': '/' + output.relative_to(root / 'public').as_posix(),
                    'width': size[0], 'height': size[1],
                    'bytes': output.stat().st_size, 'sha256': sha(output),
                })
    manifest['runtime'] = {'format': 'WebP', 'quality': 82, 'method': 6,
                           'resampling': 'Lanczos', 'webpVersion': features.version_module('webp')}
    return manifest


if __name__ == '__main__':
    result = prepare(json.loads(MANIFEST.read_text(encoding='utf-8')))
    MANIFEST.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'photos': len(result['photos']),
                      'masters': len({photo['masterId'] for photo in result['photos']}),
                      'variants': sum(len(photo['variants']) for photo in result['photos']),
                      'bytes': sum(variant['bytes'] for photo in result['photos'] for variant in photo['variants'])}))
