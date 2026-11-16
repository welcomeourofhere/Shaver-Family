"""Rebuild owner-supplied work photographs without changing the retained originals."""
import copy
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageOps, features

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'content/work-photos-owner.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(manifest, root=ROOT):
    manifest = copy.deepcopy(manifest)
    if manifest.get('source') != 'owner-supplied' or manifest.get('schemaVersion') != 1:
        raise ValueError('Expected the owner-supplied photograph manifest')
    original_root = (root / 'artifacts/iteration66/owner-work-photos/originals').resolve()
    target = (root / 'public/media/works').resolve()
    if not target.is_relative_to((root / 'public').resolve()):
        raise ValueError('Runtime photo directory escapes public')
    rows = manifest['photos'] + manifest['duplicates']
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate owner photograph ID')
    for photo in rows:
        digest = photo['sourceSha256']
        if not re.fullmatch(r'[0-9a-f]{64}', digest) or photo['id'] != 'owner-' + digest[:16]:
            raise ValueError('Invalid owner photograph identity')
        source = (root / photo['sourceFile']).resolve()
        if source.parent != original_root or not source.is_file():
            raise ValueError('Original outside the retained owner photograph directory')
        if sha(source) != digest:
            raise ValueError('Owner original changed: ' + photo['id'])
        with Image.open(source) as opened:
            # Clipboard originals are RGB without an embedded colour profile.
            if opened.mode != 'RGB' or opened.info.get('icc_profile'):
                raise ValueError('Review an unexpected source colour profile before conversion')
            image = ImageOps.exif_transpose(opened)
            if image.size != (photo['sourceWidth'], photo['sourceHeight']):
                raise ValueError('Owner original dimensions changed')
            if hashlib.sha256(image.tobytes()).hexdigest() != photo['pixelSha256']:
                raise ValueError('Owner original pixels changed')
    target.mkdir(parents=True, exist_ok=True)
    for photo in manifest['photos']:
        with Image.open(root / photo['sourceFile']) as opened:
            image = ImageOps.exif_transpose(opened).convert('RGB')
            variants = []
            for width in (360, 720, 1080):
                if width > image.width:
                    raise ValueError('Upscaling is not allowed')
                size = (width, round(image.height * width / image.width))
                output = target / f"{photo['id']}-{width}.webp"
                if output.resolve().parent != target:
                    raise ValueError('Runtime photo path escapes its directory')
                temporary = output.with_suffix('.tmp.webp')
                image.resize(size, Image.Resampling.LANCZOS).save(temporary, 'WEBP', quality=82, method=6)
                with Image.open(temporary) as check:
                    check.load()
                    if check.format != 'WEBP' or check.size != size:
                        raise ValueError('Invalid generated WebP')
                temporary.replace(output)
                variants.append({'url': '/' + output.relative_to(root / 'public').as_posix(),
                                 'width': size[0], 'height': size[1],
                                 'bytes': output.stat().st_size, 'sha256': sha(output)})
            photo['variants'] = variants
    manifest['runtime'] = {'format': 'WebP', 'quality': 82, 'method': 6,
                           'resampling': 'Lanczos', 'webpVersion': features.version_module('webp'),
                           'colourPolicy': 'Unmodified RGB source; no grading, crop or sharpening'}
    return manifest


if __name__ == '__main__':
    result = prepare(json.loads(MANIFEST.read_text(encoding='utf-8')))
    temporary = MANIFEST.with_suffix('.tmp.json')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(MANIFEST)
    print(json.dumps({'photos': len(result['photos']), 'duplicates': len(result['duplicates']),
                      'overrides': len(result['overrides']),
                      'variants': sum(len(p['variants']) for p in result['photos']),
                      'bytes': sum(v['bytes'] for p in result['photos'] for v in p['variants'])}))
