"""Export only photographs used by a master article; preserve supplied originals."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def export_article(slug, article, sources, destination=ROOT):
    destination=Path(destination).resolve()
    if not destination.is_relative_to(ROOT):
        raise ValueError('Export must stay inside the workspace')
    used = {article['cover']}
    for section in article['sections']:
        for block in section['blocks']:
            if block['kind'] == 'photos':
                used.update(block['images'])
    output = destination / 'public/media/articles' / slug
    output.mkdir(parents=True, exist_ok=True)
    media = {}
    for entry in sources['images']:
        if entry['id'] not in used:
            continue
        source = ROOT / entry['source']
        if digest(source) != entry['sha256']:
            raise ValueError('Original changed: ' + entry['id'])
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert('RGB')
            variants = []
            for width in sorted({min(640, image.width), min(1080, image.width)}):
                height = round(image.height * width / image.width)
                target = output / f"{entry['id']}-{width}.webp"
                image.resize((width, height), Image.Resampling.LANCZOS).save(target, 'WEBP', quality=88, method=6)
                variants.append({'url': '/' + target.relative_to(destination / 'public').as_posix(), 'width': width, 'height': height, 'sha256': digest(target)})
            media[entry['id']] = {'alt': entry['alt'], 'source': entry['source'], 'sourceSha256': entry['sha256'], 'variants': variants}
    if set(media) != used:
        raise ValueError('Article refers to an unknown photograph')
    catalogue=destination/'content/master-articles';catalogue.mkdir(parents=True,exist_ok=True)
    (catalogue / (slug + '.media.json')).write_text(json.dumps(media, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Exported {len(media)} photographs for {slug}')
    return media


def main():
    parser = argparse.ArgumentParser();parser.add_argument('slug');slug=parser.parse_args().slug
    article_path = (ROOT / 'content/master-articles' / (slug + '.json')).resolve()
    if not article_path.is_relative_to(ROOT / 'content/master-articles'):
        raise ValueError('Article must be inside the local catalogue')
    article = json.loads(article_path.read_text(encoding='utf-8'))
    sources = json.loads((ROOT / 'artifacts/master-articles' / slug / 'media-sources.json').read_text(encoding='utf-8'))
    export_article(slug,article,sources)

if __name__ == '__main__':
    main()
