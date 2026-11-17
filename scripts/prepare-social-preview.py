"""Bind the native square logo as the default preview; retain legacy artwork and favicon."""
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sha = lambda data: hashlib.sha256(data).hexdigest()


def main():
    manifest_path = ROOT / 'content/seo-assets.json'
    previous = json.loads(manifest_path.read_text(encoding='utf-8'))
    protected = [previous['favicon']['svg'], *previous['favicon']['rasters']]
    legacy = previous.get('legacySocial')
    if legacy is None:
        legacy = {key: previous[key] for key in [
            'method', 'browserVersion', 'composition', 'designInputs', 'textGeometry'
        ]} | {
            **previous['social'], 'sourceSnapshot': previous['sources'],
            'rendererSha256': previous['generatorSha256'],
        }
    protected.append(legacy)
    for asset in protected:
        assert sha((ROOT / asset['path']).read_bytes()) == asset['sha256'], asset['path']
    square = runpy.run_path(str(ROOT / 'scripts/prepare-square-logo.py'))['prepare_square_assets']()
    by_path = {row['path']: row for row in square['files']}
    social = by_path['public/media/og/soyuz-square.png']
    logo = by_path['public/brand/logo-square-512.png']
    seo = json.loads((ROOT / 'content/seo.json').read_text(encoding='utf-8'))
    assert seo['image'] == '/' + social['path'].removeprefix('public/')
    assert seo['logo'] == '/' + logo['path'].removeprefix('public/')
    assert [seo['imageWidth'], seo['imageHeight'], seo['imageType']] == [1000, 1000, 'image/png']
    assert [seo['logoWidth'], seo['logoHeight'], seo['logoType']] == [512, 512, 'image/png']
    for asset in protected:
        assert sha((ROOT / asset['path']).read_bytes()) == asset['sha256'], asset['path']
    manifest = {
        'version': 2, 'generator': 'scripts/prepare-social-preview.py',
        'generatorSha256': sha(Path(__file__).read_bytes()),
        'method': 'Native ready-made square PNG unchanged; ready SVG with off-canvas export preview removed',
        'sources': [{'path': path, 'sha256': sha((ROOT / path).read_bytes())}
                    for path in ['content/seo.json', 'public/brand/favicon-red.svg']],
        'social': social, 'logo': logo, 'squareLogo': square,
        'favicon': previous['favicon'], 'legacySocial': legacy,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'prepared', 'socialBytes': social['bytes'],
                      'socialSha256': social['sha256'], 'logo': logo['path'],
                      'circularFaviconAndLegacyPreviewUnchanged': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
