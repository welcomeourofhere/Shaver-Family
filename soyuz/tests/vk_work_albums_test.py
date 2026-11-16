import contextlib
import importlib.util
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('vk_work_albums', ROOT/'scripts/vk-work-albums.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
TOKEN = 'fixture-only-server-key'


class Response:
    def __init__(self, value): self.body = json.dumps(value).encode()
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, limit): return self.body[:limit]


def album(album_id=10, **extra):
    return {'id': album_id, 'owner_id': api.OWNER_ID, 'title': 'Мастер Соня Кид',
            'description': 'Подпись из альбома', 'size': 1, **extra}


def photo(photo_id=100, **extra):
    return {'id': photo_id, 'owner_id': api.OWNER_ID, 'album_id': 10, 'text': 'Подпись без изменений',
            'date': 123456, 'sizes': [{'url':'https://sun1.userapi.com/image.jpg?sign=public-fixture',
                                     'width':1200, 'height':1600}], **extra}


class WorkAlbums(unittest.TestCase):
    def test_only_two_read_methods_fixed_owner_and_posted_secret(self):
        with patch.object(api, 'build_opener') as opener, patch.object(api.time, 'sleep'):
            opener.return_value.open.return_value = Response({'response': {'count':0, 'items':[]}})
            api.request_api(TOKEN, 'photos.getAlbums', {'owner_id':1, 'access_token':'override'})
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, 'https://api.vk.com/method/photos.getAlbums')
            fields = parse_qs(request.data.decode())
            self.assertEqual(fields['access_token'], [TOKEN])
            self.assertEqual(fields['owner_id'], [str(api.OWNER_ID)])
            self.assertIsInstance(opener.call_args.args[0], api.NoRedirect)
            with self.assertRaises(api.ReadError): api.request_api(TOKEN, 'photos.delete', {})
            self.assertEqual(opener.return_value.open.call_count, 1)
        with self.assertRaises(api.ReadError): api.NoRedirect().redirect_request(None, None, None, None, None, 'https://other.test')

    def test_api_refusal_never_retains_echoed_request_or_message(self):
        for code in [5, 27]:
            with patch.object(api, 'build_opener') as opener, patch.object(api.time, 'sleep'):
                opener.return_value.open.return_value = Response({'error': {'error_code':code, 'error_msg':TOKEN, 'request_params':[{'value':TOKEN}]}})
                with self.assertRaises(api.ReadError) as error: api.request_api(TOKEN, 'photos.getAlbums', {})
                self.assertEqual(error.exception.code, code)
                self.assertNotIn(TOKEN, str(error.exception))
                self.assertEqual(opener.return_value.open.call_count, 1)

    def test_rate_limit_retry_is_bounded_and_other_errors_are_not_retried(self):
        with patch.object(api, 'build_opener') as opener, patch.object(api.time, 'sleep'):
            opener.return_value.open.side_effect = [Response({'error': {'error_code':6}}), Response({'response': {'count':0, 'items':[]}})]
            self.assertEqual(api.request_api(TOKEN, 'photos.get', {})['count'], 0)
            self.assertEqual(opener.return_value.open.call_count, 2)

    def test_response_size_and_invalid_json_fail_closed(self):
        for body in [b'x' * (api.MAX_RESPONSE_BYTES + 1), b'not JSON']:
            response = Response({}); response.body = body
            with patch.object(api, 'build_opener') as opener, patch.object(api.time, 'sleep'):
                opener.return_value.open.return_value = response
                with self.assertRaises(api.ReadError): api.request_api(TOKEN, 'photos.getAlbums', {})

    def test_pagination_includes_all_pages_and_uses_offsets(self):
        with patch.object(api, 'request_api', side_effect=[{'count':2, 'items':[album(10)]}, {'count':2, 'items':[album(11)]}]) as request:
            self.assertEqual(len(api.read_pages(TOKEN, 'photos.getAlbums', {})), 2)
            self.assertEqual([call.args[2]['offset'] for call in request.call_args_list], [0, 1])

    def test_incomplete_changing_or_unbounded_collection_is_rejected(self):
        for pages in [[{'count':2,'items':[]}], [{'count':2,'items':[album()]},{'count':3,'items':[album(11)]}], [{'count':api.MAX_ITEMS+1,'items':[]}]]:
            with patch.object(api, 'request_api', side_effect=pages), self.assertRaises(api.ReadError): api.read_pages(TOKEN, 'photos.getAlbums', {})

    def test_normalization_keeps_only_community_fields_without_assigning_a_master(self):
        value = api.normalize_albums([None, album(owner_id=1), album(access_token=TOKEN, privacy='private')])
        self.assertEqual(len(value), 1)
        self.assertEqual(value[0]['title'], album()['title'])
        self.assertNotIn(TOKEN, json.dumps(value))
        self.assertNotIn('privacy', value[0]); self.assertNotIn('masterId', value[0])
        with self.assertRaises(api.ReadError): api.normalize_albums([album(), album()])

    def test_photo_caption_ids_and_largest_signed_image_are_preserved(self):
        large = {'url':'https://sun2.vkuserphoto.ru/original.jpg?sign=public', 'width':1440, 'height':2560}
        value = api.normalize_photos([photo(sizes=[photo()['sizes'][0], large])], 10)[0]
        self.assertEqual(value['image'], large)
        self.assertEqual(value['caption'], photo()['text'])
        self.assertEqual(value['url'], 'https://vk.ru/photo-210007626_100')
        self.assertNotIn('masterId', value)

    def test_unsafe_urls_wrong_album_and_invalid_dimensions_are_not_accepted(self):
        for url in ['https://localhost/a', 'https://sun1.userapi.com.evil.test/a', 'https://name:secret@sun1.userapi.com/a', 'http://sun1.userapi.com/a', 'https://sun1.userapi.com/a?access_token=secret', 'https://sun1.userapi.com:444/a']:
            self.assertFalse(api.public_image(url))
        value = api.normalize_photos([photo(sizes=[None, {'url':'https://sun1.userapi.com/a','width':True,'height':20}])], 10)
        self.assertIsNone(value[0]['image'])
        with self.assertRaises(api.ReadError): api.normalize_photos([photo(album_id=11)], 10)
        with self.assertRaises(api.ReadError): api.normalize_photos([photo(), photo()], 10)

    def test_ids_are_explicit_positive_and_bounded(self):
        self.assertEqual(api.parse_album_ids('10, 11,10'), [10, 11])
        self.assertEqual(api.parse_album_ids(''), [])
        for value in ['wall', '-10', '10; rm', '10,', '0', ','.join(map(str, range(1, 22)))]:
            with self.assertRaises(api.ReadError): api.parse_album_ids(value)

    def test_discovery_does_not_fetch_photos_and_selection_is_verified(self):
        with patch.object(api, 'read_pages', return_value=[album()]) as request:
            snapshot = api.collect(TOKEN, [])
            self.assertEqual(request.call_count, 1); self.assertNotIn('photos', snapshot['albums'][0])
            with self.assertRaises(api.ReadError): api.collect(TOKEN, [99])
        with patch.object(api, 'read_pages', side_effect=[[album()], [photo()]]):
            self.assertEqual(api.collect(TOKEN, [10])['albums'][0]['photos'][0]['id'], 100)

    def test_failure_retains_last_snapshot_and_logs_only_safe_code(self):
        with TemporaryDirectory() as directory:
            path=Path(directory)/'snapshot.json';path.write_text('previous successful snapshot')
            output=StringIO()
            with patch.dict(api.os.environ, {'SOYUZ_VK_TOKEN':TOKEN}), patch.object(api, 'collect', side_effect=api.ReadError('api_error', 27)), contextlib.redirect_stdout(output):
                self.assertEqual(api.main(['--output', str(path)]), 1)
            self.assertEqual(path.read_text(), 'previous successful snapshot')
            self.assertNotIn(TOKEN, output.getvalue())
            self.assertEqual(json.loads(path.with_name('snapshot.error.json').read_text())['code'], 27)

    def test_secret_echo_is_rejected_before_file_or_catalog_publication(self):
        with TemporaryDirectory() as directory:
            path=Path(directory)/'snapshot.json'
            with self.assertRaises(api.ReadError): api.save_snapshot({'title':TOKEN}, path, TOKEN)
            self.assertFalse(path.exists())

    def test_catalog_log_contains_metadata_only_and_fallback_secret_is_used(self):
        snapshot={'albums':[{'id':10,'title':'Соня Кид','description':'Описание','size':1,'photos':[{'image':{'url':'https://sun1.userapi.com/private-sized-photo'}}]}], 'requestedAlbumIds':[10]}
        with TemporaryDirectory() as directory, patch.dict(api.os.environ, {'SOYUZ_VK_TOKEN':'','VK_TOKEN':TOKEN}), patch.object(api, 'collect', return_value=snapshot) as collect, contextlib.redirect_stdout(StringIO()) as output:
            self.assertEqual(api.main(['--output',str(Path(directory)/'snapshot.json')]), 0)
            self.assertEqual(collect.call_args.args[0], TOKEN)
            catalog=output.getvalue().splitlines()[0]
            self.assertTrue(catalog.startswith('SOYUZ_ALBUM_CATALOG='))
            for forbidden in ['userapi.com','image','access_token',TOKEN]: self.assertNotIn(forbidden,catalog)


if __name__ == '__main__': unittest.main()
