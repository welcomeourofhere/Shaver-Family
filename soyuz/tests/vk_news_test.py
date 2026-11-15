import importlib.util
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory

spec = importlib.util.spec_from_file_location('vk_news', Path(__file__).resolve().parents[1] / 'scripts/update-vk-news.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PublicNews(unittest.TestCase):
    def test_multi_photo_cover_prefers_available_full_resolution_over_first_thumbnail(self):
        html = '''<div class="wcommunity_post"><a class="wcommunity_post_date" href="/wall-210007626_5">3 ноя 2026</a><div class="wall_post_text">Новость</div><img src="https://sun1.userapi.com/first.jpg?size=97x130"><img src="https://sun2.userapi.com/second.jpg?as=160x213,640x853,1280x1707&amp;cs=160x0"></div>'''
        post = module.normalize(html, datetime(2026, 11, 5, tzinfo=module.MOSCOW))[0]
        self.assertIn('second.jpg', post['photo'])
        self.assertEqual(module.photo_width(post['photo']), 1280)

    def test_viewer_original_is_preferred_even_without_dimensions_in_its_url(self):
        html = '''<div class="wcommunity_post"><a class="wcommunity_post_date" href="/wall-210007626_5">3 ноя 2026</a><div class="wall_post_text">Новость</div><a onclick='showPhoto("5", "wall", {"temp":{"w":"https://sun1.userapi.com/original.jpg"}})' style="background-image:url(https://sun2.userapi.com/thumb.jpg?size=604x604)"></a></div>'''
        post = module.normalize(html, datetime(2026, 11, 5, tzinfo=module.MOSCOW))[0]
        self.assertEqual(post['photo'], 'https://sun1.userapi.com/original.jpg')

    def test_runtime_refresh_does_not_rewrite_the_canonical_ssr_snapshot(self):
        workspace = Path(__file__).resolve().parents[1]
        temporary_base = (workspace / 'tmp/vk-news-tests').resolve()
        temporary_base.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=temporary_base) as directory:
            root = Path(directory)
            self.assertTrue(root.resolve().is_relative_to(temporary_base))
            canonical = root / 'content/news.json'
            canonical.parent.mkdir(parents=True)
            canonical.write_text('canonical snapshot', encoding='utf-8')
            posts = [{'id': str(i), 'publishedAt': f'2026-11-{i:02}T10:00:00+03:00', 'text': f'Post {i}', 'url': f'https://vk.ru/wall-210007626_{i}', 'photo': None} for i in range(1, 11)]
            response = json.dumps({'payload': [0, ['']]}).encode('ascii')
            with patch.object(module, 'ROOT', root), patch.object(module, 'read', side_effect=[b'', response]), patch.object(module, 'normalize', return_value=posts), patch.object(module, 'export_photo', return_value=None):
                module.update(public_only=True)
            self.assertEqual(canonical.read_text(encoding='utf-8'), 'canonical snapshot')
            live = json.loads((root / 'public/data/news.json').read_text(encoding='utf-8'))
            self.assertEqual(len(live['items']), 10)
            self.assertEqual(live['items'][0]['id'], '10')

    def test_localized_dates(self):
        now = datetime(2026, 11, 5, 1, 0, tzinfo=module.MOSCOW)
        self.assertEqual(module.date_from_label('3 ноя 2026 в 20:19', now).isoformat(), '2026-11-03T20:19:00+03:00')
        self.assertEqual(module.date_from_label('вчера в 12:00', now).day, 4)
        with self.assertRaises(ValueError): module.date_from_label('Неизвестная дата', now)

    def test_omitted_year_never_moves_a_december_post_into_the_future(self):
        now = datetime(2027, 1, 5, tzinfo=module.MOSCOW)
        self.assertEqual(module.date_from_label('31 дек в 20:19', now).year, 2026)
        self.assertEqual(module.date_from_label('31 дек 2025 в 20:19', now).year, 2025)

    def test_empty_viewer_size_uses_the_next_available_original(self):
        html = '''<div class="wcommunity_post"><a class="wcommunity_post_date" href="/wall-210007626_5">3 ноя 2026</a><div class="wall_post_text">Новость</div><a onclick='showPhoto("5", "wall", {"temp":{"w":[],"z":["https://sun1.userapi.com/original.jpg",1280,1600]}})'></a></div>'''
        self.assertEqual(module.normalize(html, datetime(2026,11,5,tzinfo=module.MOSCOW))[0]['photo'], 'https://sun1.userapi.com/original.jpg')

    def test_removed_or_replaced_cover_does_not_keep_an_unrelated_old_image(self):
        workspace = Path(__file__).resolve().parents[1]
        temporary_base = workspace / 'tmp/vk-news-tests'
        temporary_base.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=temporary_base) as directory:
            root = Path(directory)
            prior = {'variants':[{'url':'../media/news/1-abc-1600.webp','width':1600,'height':1600}],'sourceSha256':'old'}
            live = root/'public/data/news.json';live.parent.mkdir(parents=True)
            live.write_text(json.dumps({'items':[{'id':'1','image':prior},{'id':'2','image':prior}]}), encoding='utf-8')
            posts = [{'id':str(i),'publishedAt':f'2026-11-{i:02}T10:00:00+03:00','text':f'Post {i}','url':f'https://vk.ru/wall-210007626_{i}','photo':None if i!=2 else 'https://sun1.userapi.com/new.jpg'} for i in range(1,11)]
            replacement = {'variants':[{'url':'../media/news/2-def-640.webp','width':640,'height':640}],'sourceSha256':'new'}
            with patch.object(module,'ROOT',root), patch.object(module,'read',side_effect=[b'',json.dumps({'payload':[0,['']]}).encode()]), patch.object(module,'normalize',return_value=posts), patch.object(module,'export_photo',side_effect=lambda post,directory: replacement if post['photo'] else None):
                module.update(public_only=True)
            items = {item['id']:item for item in json.loads(live.read_text(encoding='utf-8'))['items']}
            self.assertIsNone(items['1']['image'])
            self.assertEqual(items['2']['image']['sourceSha256'],'new')

    def test_matching_cover_keeps_the_larger_original_despite_signed_size_changes(self):
        workspace = Path(__file__).resolve().parents[1]
        temporary_base = workspace/'tmp/vk-news-tests';temporary_base.mkdir(parents=True,exist_ok=True)
        photo = 'https://sun1.userapi.com/same.jpg?size=640x640&sign=new'
        key = module.photo_key('https://sun2.userapi.com/same.jpg?size=1600x1600&sign=old')
        self.assertEqual(key,module.photo_key(photo))
        self.assertNotEqual(key,module.photo_key('https://sun1.userapi.com/different.jpg'))
        with TemporaryDirectory(dir=temporary_base) as directory:
            root = Path(directory);live = root/'public/data/news.json';live.parent.mkdir(parents=True)
            prior = {'variants':[{'url':'../media/news/1-abc-1600.webp','width':1600,'height':1600}],'sourceKey':key,'sourceSha256':'old'}
            live.write_text(json.dumps({'items':[{'id':'1','image':prior}]}),encoding='utf-8')
            posts = [{'id':str(i),'publishedAt':f'2026-11-{i:02}T10:00:00+03:00','text':f'Post {i}','url':f'https://vk.ru/wall-210007626_{i}','photo':photo if i==1 else None} for i in range(1,11)]
            small = {'variants':[{'url':'../media/news/1-def-640.webp','width':640,'height':640}],'sourceKey':key,'sourceSha256':'new'}
            with patch.object(module,'ROOT',root),patch.object(module,'read',side_effect=[b'',json.dumps({'payload':[0,['']]}).encode()]),patch.object(module,'normalize',return_value=posts),patch.object(module,'export_photo',side_effect=lambda post,directory:small if post['photo'] else None):
                module.update(public_only=True)
            item = next(item for item in json.loads(live.read_text(encoding='utf-8'))['items'] if item['id']=='1')
            self.assertEqual(item['image']['variants'][0]['width'],1600)

    def test_safe_public_photo_hosts(self):
        self.assertTrue(module.public_image('https://sun9-12.userapi.com/photo.jpg'))
        self.assertTrue(module.public_image('https://sun9-12.vkuserphoto.ru/photo.jpg'))
        for value in ['http://sun.userapi.com/a', 'https://userapi.com.evil.test/a', 'https://name:password@sun.userapi.com/a', None]:
            self.assertFalse(module.public_image(value))

    def test_post_structure_preserves_lines_and_excludes_foreign_wall(self):
        html = '''<div class="wcommunity_post"><div><a class="wcommunity_post_date" href="/wall-210007626_5">3 ноя 2026 в 20:19</a></div><div class="wall_post_text">Заголовок<br><br>Текст <a href="https://example.com">ссылки</a></div><img src="https://sun1.userapi.com/a.jpg"></div><div class="wcommunity_post"><a class="wcommunity_post_date" href="/wall-1_5">3 ноя 2026</a><div class="wall_post_text">Чужая стена</div></div>'''
        items = module.normalize(html, datetime(2026, 11, 5, tzinfo=module.MOSCOW))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['text'], 'Заголовок\n\nТекст ссылки')
        self.assertEqual(items[0]['url'], 'https://vk.ru/wall-210007626_5')
        self.assertEqual(items[0]['photo'], 'https://sun1.userapi.com/a.jpg')

    def test_expand_label_is_excluded_without_joining_words(self):
        html = '''<div class="wcommunity_post"><a class="wcommunity_post_date" href="/wall-210007626_5">3 ноя 2026</a><div class="wall_post_text">Большой<button><span class="PostTextMore__content">Показать ещё</span></button><span style="display:none"> профессиональный путь</span></div></div>'''
        item = module.normalize(html, datetime(2026, 11, 5, tzinfo=module.MOSCOW))[0]
        self.assertEqual(item['text'], 'Большой профессиональный путь')

    def test_source_failure_retains_both_successful_snapshots(self):
        workspace = Path(__file__).resolve().parents[1]
        temporary_base = (workspace / 'tmp/vk-news-tests').resolve()
        self.assertTrue(temporary_base.is_relative_to(workspace))
        temporary_base.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=temporary_base) as directory:
            root = Path(directory)
            self.assertTrue(root.resolve().is_relative_to(temporary_base))
            paths = [root/'content/news.json', root/'public/data/news.json']
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'previous successful snapshot')
            with patch.object(module, 'ROOT', root), patch.object(module, 'read', side_effect=OSError('offline')):
                with self.assertRaises(OSError): module.update()
            for path in paths: self.assertEqual(path.read_bytes(), b'previous successful snapshot')

if __name__ == '__main__': unittest.main()
