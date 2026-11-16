"""Export selected original poster art into responsive WebP assets."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'artifacts/posters/individual'
JOBS = json.loads((SOURCE / 'prompts.json').read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    for job in JOBS:
        assert (SOURCE / (job['id'] + '.png')).is_file(), job['id']
    entries = []
    target = ROOT / 'public/media/offers'
    target.mkdir(parents=True, exist_ok=True)
    for job in JOBS:
        path = SOURCE / (job['id'] + '.png')
        with Image.open(path) as opened:
            image = ImageOps.exif_transpose(opened).convert('RGB')
            entry = {**job, 'source': path.relative_to(ROOT).as_posix(),
                     'sourceSha256': sha(path), 'sourceSize': list(image.size), 'variants': []}
            for width in [640, 1200]:
                size = (width, round(image.height * width / image.width))
                output = target / f"{job['id']}-{width}.webp"
                image.resize(size, Image.Resampling.LANCZOS).save(output, 'WEBP', quality=85 if width == 640 else 78, method=6)
                entry['variants'].append({'url': '/' + output.relative_to(ROOT / 'public').as_posix(),
                    'width': size[0], 'height': size[1], 'bytes': output.stat().st_size,
                    'sha256': sha(output)})
            entries.append(entry)
    manifest = {'generator': 'Built-in image_gen', 'asOf': '2026-11-05',
                'brief': 'Individual painterly Soviet-style compositions; no text, barbershop interiors or barber poles. Honest-price poster is a local design candidate.',
                'promptSet': 'artifacts/posters/individual/prompts.json', 'images': entries}
    (ROOT / 'content/offer-poster-sources.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Exported {len(entries)} posters / {len(entries) * 2} responsive WebP assets.')

if __name__ == '__main__':
    main()
