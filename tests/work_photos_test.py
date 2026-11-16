"""The published work gallery must retain factual credits and exact runtime bytes."""
import hashlib
import json
from pathlib import Path
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'content/work-photos.json').read_text(encoding='utf-8'))
TEAM = json.loads((ROOT / 'content/team.json').read_text(encoding='utf-8'))


class WorkPhotos(unittest.TestCase):
    def test_public_community_lineage_and_all_current_masters(self):
        self.assertEqual(DATA['source'], 'vk-public-wall')
        self.assertEqual(DATA['ownerId'], -210007626)
        self.assertEqual(DATA['apiRun'], 43873941766)
        self.assertEqual(len(DATA['sourceSnapshotSha256']), 64)
        photos = DATA['photos']
        self.assertGreaterEqual(len(photos), 19)
        self.assertNotIn(457241410, {p['photoId'] for p in photos})
        self.assertNotIn(457241453, {p['photoId'] for p in photos})
        self.assertEqual(len({p['id'] for p in photos}), len(photos))
        self.assertEqual({p['masterId'] for p in photos}, {p['id'] for p in TEAM['masters']})
        self.assertTrue({'haircuts', 'beards'}.issubset({c for p in photos for c in p['categories']}))
        tags = {'souz-darya': 'Дарья', 'souz-svetlana': 'Светлана', 'souz-sonya-kid': 'Соня',
                'souz-milena': 'Милена', 'souz-sofya-shalaginova': 'Софья', 'souz-lyubov': 'Любовь'}
        for photo in photos:
            with self.subTest(photo=photo['id']):
                self.assertEqual(photo['id'], 'vk-' + str(photo['photoId']))
                self.assertEqual(photo['postUrl'], f"https://vk.ru/wall-210007626_{photo['postId']}")
                self.assertEqual(photo['photoUrl'], f"https://vk.ru/photo-210007626_{photo['photoId']}")
                self.assertEqual(photo['creditEvidence'], '#Товарищ' + tags[photo['masterId']] + '@soyuz_kirov')
                self.assertTrue(photo['captionEvidence'].strip())
                self.assertTrue(photo['title'].strip())
                self.assertRegex(photo['title'], r'^[A-Za-z][A-Za-z -]+ \([А-Яа-яЁё -]+\)')
                self.assertEqual(len(photo['sourceTextSha256']), 64)
                self.assertEqual(len(photo['sourceSha256']), 64)
        self.assertEqual([p for p in photos if p['photoId'] == 457242038][0]['categories'], ['haircuts', 'beards'])

    def test_runtime_variants_match_bytes_hashes_and_original_aspect_without_upscaling(self):
        for photo in DATA['photos']:
            self.assertEqual([v['width'] for v in photo['variants']], [360, 720, 1080])
            for variant in photo['variants']:
                with self.subTest(photo=photo['id'], width=variant['width']):
                    expected = f"/media/works/vk-{photo['photoId']}-{variant['width']}.webp"
                    self.assertEqual(variant['url'], expected)
                    path = ROOT / 'public' / variant['url'].lstrip('/')
                    body = path.read_bytes()
                    self.assertEqual(body[:4], b'RIFF')
                    self.assertEqual(body[8:12], b'WEBP')
                    self.assertEqual(len(body), variant['bytes'])
                    self.assertEqual(hashlib.sha256(body).hexdigest(), variant['sha256'])
                    with Image.open(path) as image:
                        image.load()
                        self.assertEqual(image.format, 'WEBP')
                        self.assertEqual(image.size, (variant['width'], variant['height']))
                    self.assertLessEqual(variant['width'], photo['sourceWidth'])
                    self.assertEqual(variant['height'], round(photo['sourceHeight'] * variant['width'] / photo['sourceWidth']))


if __name__ == '__main__':
    unittest.main()
