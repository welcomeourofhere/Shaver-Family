"""Preserve the owner's originals and derive responsive review photos; no creative edits."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('C:/Users/Lenovo/AppData/Local/Temp')
GROUPS = [
    ['ae4b574f-ed6f-477f-86e5-728c68dc0762', 'e8d749f6-3c02-49e3-aa30-873cb3169b22'],
    ['f221ccba-9e53-4ffe-8168-d8e4b7ea01a7'],
    ['5bc69d58-2920-4e4d-915e-61e312c31eb9', '1558113f-3e95-47b0-97df-b16da057c079'],
    ['b800bdfc-9e37-46df-b8d8-4e85ff913ac2', '0d4782bf-46f2-4035-a8aa-10b619ec416b'],
    ['0dd7ff45-fa5b-4519-b06a-a61d0ece38a1', '5fa63036-821d-4d33-8963-c3d139fae6bb'],
    ['d1a1d4fa-d933-4b30-82ca-0a5c188db8d7'],
    ['e6bf80a6-7d59-4295-a620-a17ceef4f4ef'],
    ['494e545e-5a02-41da-8659-75ee47a10c17'],
]
manifest_file=ROOT/'content/review-media.json'
manifest = json.loads(manifest_file.read_text('utf-8')) if manifest_file.exists() else {'source': 'Owner attachments; association confirmed in chat', 'reviews': []}
out = ROOT / 'public/media/reviews'
out.mkdir(parents=True, exist_ok=True)
for number, group in enumerate(GROUPS, 1):
    if any(item['id']==f'review-{number:02}'for item in manifest['reviews']):continue
    date='2026-11-15'if number==8 else'2026-11-09'
    originals=ROOT/f'archive/owner-media/{date}/reviews';originals.mkdir(parents=True,exist_ok=True)
    photos = []
    for index, identifier in enumerate(group, 1):
        source = SOURCE / f'codex-clipboard-{identifier}.png'
        data = source.read_bytes()
        (originals / source.name).write_bytes(data)
        photo = ImageOps.exif_transpose(Image.open(source)).convert('RGB')
        variants = []
        for width in [480, 960]:
            image = photo.copy()
            image.thumbnail((width, 2000), Image.Resampling.LANCZOS)
            filename = f'review-{number:02}-{index}-{width}.webp'
            image.save(out / filename, 'WEBP', quality=85, method=6)
            variants.append({'url': f'/media/reviews/{filename}', 'width': image.width, 'height': image.height})
        photos.append({'source': source.name, 'sha256': hashlib.sha256(data).hexdigest(), 'variants': variants, 'original':str((originals/source.name).relative_to(ROOT).as_posix())})
        if number==8:photos[-1]['alt']='Барбер Любовь и гость СОЮЗа после стрижки перед зеркалом'
    manifest['reviews'].append({'id': f'review-{number:02}', 'photos': photos})
assert len(manifest['reviews']) == len(GROUPS) and sum(len(r['photos']) for r in manifest['reviews']) == sum(map(len,GROUPS))
(ROOT / 'content/review-media.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Preserved original media; responsive assets ready for {len(GROUPS)} owner reviews.')
