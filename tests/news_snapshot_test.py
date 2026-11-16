import hashlib
import importlib.util
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from PIL import Image

spec=importlib.util.spec_from_file_location('news_sync',Path(__file__).resolve().parents[1]/'scripts/sync-vk-news-snapshot.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class PublicSnapshot(unittest.TestCase):
    def test_preview_sync_and_runtime_read_the_same_verified_feed(self):
        site=json.loads((module.ROOT/'content/site.json').read_text(encoding='utf-8'))
        self.assertEqual(site['newsFeedUrl'],module.SOURCE)
        for path in ['content/news.json','public/data/news.json']:
            payload=json.loads((module.ROOT/path).read_text(encoding='utf-8'))
            self.assertEqual(payload['source'],'official-vk-api',path)
            self.assertEqual(payload['groupId'],-210007626,path)
    def fixture(self):
        image=BytesIO();Image.new('RGB',(640,800),'red').save(image,'WEBP');data=image.getvalue()
        photo={'variants':[{'url':'../media/news/1-abcdef-640.webp','width':640,'height':800,'sha256':hashlib.sha256(data).hexdigest()}]}
        feed={'version':1,'groupId':-210007626,'source':'official-vk-api','generatedAt':'2026-11-15T12:00:00+03:00','items':[{'id':str(i),'url':f'https://vk.ru/wall-210007626_{i}','text':'Публичная новость','image':photo if i==1 else None}for i in range(1,11)]}
        return feed,data
    def test_sync_preserves_hashes_and_public_only_does_not_change_the_canonical_snapshot(self):
        feed,image=self.fixture()
        with TemporaryDirectory()as directory:
            root=Path(directory);canonical=root/'content/news.json';canonical.parent.mkdir();canonical.write_text('canonical')
            with patch.object(module,'ROOT',root),patch.object(module,'read',side_effect=[json.dumps(feed).encode(),image]):module.sync(public_only=True)
            self.assertEqual(canonical.read_text(),'canonical')
            self.assertEqual((root/'public/media/news/1-abcdef-640.webp').read_bytes(),image)
            self.assertEqual(json.loads((root/'public/data/news.json').read_text())['items'],feed['items'])
    def test_untrusted_path_or_corrupt_photo_retains_the_previous_snapshot(self):
        for corruption in ['path','hash']:
            feed,image=self.fixture()
            if corruption=='path':feed['items'][0]['image']['variants'][0]['url']='https://example.com/private'
            else:image=b'corrupt bytes'
            with TemporaryDirectory()as directory:
                root=Path(directory);path=root/'public/data/news.json';path.parent.mkdir(parents=True);path.write_text('previous')
                with patch.object(module,'ROOT',root),patch.object(module,'read',side_effect=[json.dumps(feed).encode(),image]):
                    with self.assertRaises(ValueError):module.sync()
                self.assertEqual(path.read_text(),'previous')
    def test_excluded_remote_post_does_not_replace_the_successful_local_feed(self):
        for excluded in ['1950','1941']:
            feed,_=self.fixture();feed['items'][0].update(id=excluded,url=f'https://vk.ru/wall-210007626_{excluded}')
            with TemporaryDirectory()as directory:
                root=Path(directory);path=root/'public/data/news.json';path.parent.mkdir(parents=True);path.write_text('previous')
                with patch.object(module,'ROOT',root),patch.object(module,'read',return_value=json.dumps(feed).encode()):
                    with self.assertRaises(ValueError):module.sync()
                self.assertEqual(path.read_text(),'previous')
if __name__=='__main__':unittest.main()
