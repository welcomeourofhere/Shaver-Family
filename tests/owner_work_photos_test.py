"""Owner credits, frame deduplication and public WebP checks without private originals."""
import copy
import hashlib
import json
import runpy
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'content/work-photos-owner.json').read_text(encoding='utf-8'))
WALL = json.loads((ROOT / 'content/work-photos.json').read_text(encoding='utf-8'))
PREPARE = runpy.run_path(str(ROOT / 'scripts/prepare-owner-work-photos.py'))['prepare']


class OwnerWorkPhotos(unittest.TestCase):
    def test_all_owner_groups_preserved_and_eight_confirmed_frames_reused(self):
        self.assertEqual(DATA['source'], 'owner-supplied')
        self.assertTrue(DATA['ownerCreditAuthority'])
        rows = DATA['photos'] + DATA['duplicates']
        self.assertEqual(len(rows), DATA['suppliedCount'])
        self.assertEqual(len(rows), 31)
        self.assertEqual(len(DATA['photos']), 23)
        self.assertEqual(len(DATA['duplicates']), 8)
        self.assertEqual(len({r['id'] for r in rows}), 31)
        self.assertEqual(len({r['pixelSha256'] for r in rows}), 31)
        expected = {1: ('souz-lyubov', 2), 2: ('souz-sonya-kid', 13),
                    3: ('souz-sofya-shalaginova', 6), 4: ('souz-milena', 5),
                    5: ('souz-lyubov', 2), 6: ('souz-darya', 3)}
        for group, (master, count) in expected.items():
            subset = [r for r in rows if r['ownerGroup'] == group]
            self.assertEqual(len(subset), count)
            self.assertEqual({r['masterId'] for r in subset}, {master})
        wall = {r['id']: r for r in WALL['photos']}
        for row in rows:
            self.assertRegex(row['sourceSha256'], r'^[0-9a-f]{64}$')
            self.assertEqual(row['id'], 'owner-' + row['sourceSha256'][:16])
            self.assertEqual(row['evidence']['filename'], row['ownerFilename'])
            self.assertEqual(row['evidence']['masterId'], row['masterId'])
        for row in DATA['duplicates']:
            original = wall[row['duplicateOf']]
            self.assertEqual(original['masterId'], row['masterId'])
            self.assertEqual(row['variants'], [])
            self.assertEqual(row['decision'], 'reuse-existing-runtime')
            self.assertTrue(any(m['vkId'] == row['duplicateOf'] and m['confirmed']
                                and m['currentRuntime'] for m in row['frameMatches']))
        self.assertEqual(DATA['overrides'], [])
        sonya_frame = next(r for r in rows if r['ownerFilename'].startswith('codex-clipboard-f5648c6b-'))
        self.assertEqual(sonya_frame['masterId'], 'souz-sonya-kid')
        self.assertEqual(sonya_frame['frameMatches'][0]['vkId'], 'vk-457241566')
        self.assertNotIn('duplicateOf', sonya_frame)

    def test_all_runtime_variants_match_real_dimensions_hashes_and_no_upscale(self):
        for photo in DATA['photos']:
            self.assertEqual([v['width'] for v in photo['variants']], [360, 720, 1080])
            for variant in photo['variants']:
                with self.subTest(photo=photo['id'], width=variant['width']):
                    self.assertEqual(variant['url'], f"/media/works/{photo['id']}-{variant['width']}.webp")
                    path = (ROOT / 'public' / variant['url'].lstrip('/')).resolve()
                    self.assertEqual(path.parent, (ROOT / 'public/media/works').resolve())
                    body = path.read_bytes()
                    self.assertEqual(len(body), variant['bytes'])
                    self.assertEqual(hashlib.sha256(body).hexdigest(), variant['sha256'])
                    self.assertLessEqual(variant['width'], photo['sourceWidth'])
                    self.assertEqual(variant['height'], round(photo['sourceHeight'] * variant['width'] / photo['sourceWidth']))
                    with Image.open(path) as image:
                        image.load()
                        self.assertEqual(image.format, 'WEBP')
                        self.assertEqual(image.size, (variant['width'], variant['height']))

    def fixture(self, root, width=1080):
        path = root / 'artifacts/iteration66/owner-work-photos/originals/test.png'
        path.parent.mkdir(parents=True)
        image = Image.new('RGB', (width, 1440), (90, 110, 130))
        image.save(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        row = {'id': 'owner-' + digest[:16], 'sourceSha256': digest,
               'sourceFile': path.relative_to(root).as_posix(), 'sourceWidth': width,
               'sourceHeight': 1440, 'pixelSha256': hashlib.sha256(image.tobytes()).hexdigest()}
        return {'schemaVersion': 1, 'source': 'owner-supplied', 'photos': [row], 'duplicates': []}

    def test_generator_rejects_path_identity_hash_dimensions_and_upscale(self):
        mutations = [lambda p: p.update(sourceFile='outside.png'),
                     lambda p: p.update(id='owner-../../outside'),
                     lambda p: p.update(sourceSha256='0' * 64, id='owner-' + '0' * 16),
                     lambda p: p.update(sourceWidth=999),
                     lambda p: p.update(pixelSha256='0' * 64)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.fixture(root)
            for mutate in mutations:
                invalid = copy.deepcopy(manifest)
                mutate(invalid['photos'][0])
                with self.assertRaises(ValueError):
                    PREPARE(invalid, root)
            self.assertFalse((root / 'public').exists())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.fixture(root, width=100)
            with self.assertRaisesRegex(ValueError, 'Upscaling'):
                PREPARE(manifest, root)
            self.assertEqual(list((root / 'public').rglob('*.webp')), [])

    def test_generator_is_reproducible_and_preserves_its_input_and_original(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.fixture(root)
            original = copy.deepcopy(manifest)
            first = PREPARE(manifest, root)
            second = PREPARE(manifest, root)
            self.assertEqual(first, second)
            self.assertEqual(manifest, original)
            path = root / manifest['photos'][0]['sourceFile']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), manifest['photos'][0]['sourceSha256'])


if __name__ == '__main__':
    unittest.main()
