"""Export owner-supplied staff art without changing or replacing the originals."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / 'artifacts/owner-posters/2026-11-05/index.json'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    catalog = json.loads(JOBS.read_text(encoding='utf-8'))
    target = ROOT / 'public/media/editorial'
    target.mkdir(parents=True, exist_ok=True)
    entries = []
    for job in catalog['images']:
        source = ROOT / job['source']
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert('RGB')
            entry = {**job, 'sourceSha256': digest(source), 'sourceSize': list(image.size), 'variants': []}
            for width in [640, min(1440, image.width)]:
                height = round(image.height * width / image.width)
                output = target / f"{job['id']}-{width}.webp"
                image.resize((width, height), Image.Resampling.LANCZOS).save(output, 'WEBP', quality=86, method=6)
                entry['variants'].append({'url': '/' + output.relative_to(ROOT / 'public').as_posix(), 'width': width, 'height': height, 'bytes': output.stat().st_size, 'sha256': digest(output)})
            entries.append(entry)
    (ROOT / 'content/editorial-images.json').write_text(json.dumps({'source': catalog['source'], 'images': entries}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Exported {len(entries)} owner images in two responsive sizes each.')

if __name__ == '__main__':
    main()
