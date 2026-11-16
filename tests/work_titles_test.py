"""Each gallery frame has one reviewed bilingual family without losing lineage."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / 'content' / name).read_text(encoding='utf-8'))


class WorkTitles(unittest.TestCase):
    def test_review_covers_all_frames_and_only_catalog_identities(self):
        data = read('work-photo-titles.json')
        wall, owner = read('work-photos.json'), read('work-photos-owner.json')
        expected = {p['id'] for p in wall['photos'] + owner['photos']}
        rows = data['photos']
        self.assertEqual(data['schemaVersion'], 1)
        self.assertEqual(data['source'], 'shaver-family-lookbook-visual-review')
        self.assertEqual(len(rows), len(expected))
        self.assertEqual({r['id'] for r in rows}, expected)
        self.assertRegex(data['catalogSource']['sourceSha256'], r'^[0-9a-f]{64}$')
        catalog = {c['id']: c for c in data['catalog']}
        self.assertEqual(len(catalog), len(data['catalog']))
        used = set()
        for row in rows:
            with self.subTest(photo=row['id']):
                primary = catalog[row['primaryId']]
                self.assertIn(primary['type'], ['hair', 'beard'])
                self.assertRegex(primary['en'], r'^[A-Za-z][A-Za-z /-]+$')
                self.assertTrue(primary.get('displayRu', primary['ru']).strip())
                self.assertIn(row['confidence'], ['high', 'medium', 'low'])
                self.assertEqual(row['status'], 'closest-family' if row['confidence'] == 'low' else 'catalog-fit')
                self.assertTrue(row['basis'].strip())
                self.assertIsInstance(row['viewLimits'], list)
                self.assertEqual(len(set(row['secondaryIds'])), len(row['secondaryIds']))
                used.add(row['primaryId'])
                for key in row['secondaryIds']:
                    self.assertIn(key, catalog)
                    used.add(key)
        self.assertEqual(set(catalog), used)

    def test_original_captions_remain_and_limited_views_are_estimates(self):
        rows = {r['id']: r for r in read('work-photo-titles.json')['photos']}
        wall = {p['id']: p for p in read('work-photos.json')['photos']}
        self.assertEqual(rows['vk-457241782']['primaryId'], 'lookbook-curly-mod-cut')
        self.assertIn('Edgar', wall['vk-457241782']['title'])
        self.assertIn('Эдгар', wall['vk-457241782']['captionEvidence'])
        self.assertEqual(rows['owner-a3295cd3223db81a']['confidence'], 'low')
        self.assertTrue(rows['owner-a3295cd3223db81a']['viewLimits'])
        self.assertEqual(rows['vk-457241816']['status'], 'closest-family')
        self.assertNotIn('vk-457241410', rows)
        self.assertNotIn('vk-457241453', rows)


if __name__ == '__main__':
    unittest.main()
