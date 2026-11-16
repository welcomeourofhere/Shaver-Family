import contextlib
import importlib.util
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('vk_public_work_photos',ROOT/'scripts/vk-public-work-photos.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
TOKEN='fixture-only-wall-key'


class Response:
    def __init__(self,value):self.body=json.dumps(value).encode()
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,limit):return self.body[:limit]


def photo(photo_id=20,**extra):
    return {'type':'photo','photo':{'id':photo_id,'owner_id':api.OWNER_ID,'album_id':-7,
            'sizes':[{'url':'https://sun1.userapi.com/a.jpg?sign=public','width':1280,'height':1707}],**extra}}


def post(post_id=10,**extra):
    return {'id':post_id,'owner_id':api.OWNER_ID,'from_id':api.OWNER_ID,'date':123456,
            'text':'Стрижка. Товарищ Соня Кид.','attachments':[photo()],**extra}


class PublicWallPhotos(unittest.TestCase):
    def test_fixed_read_method_post_owner_filter_count_offset_and_spacing(self):
        with patch.object(api,'build_opener')as opener,patch.object(api.time,'sleep')as sleep:
            opener.return_value.open.return_value=Response({'response':{'count':0,'items':[]}})
            self.assertEqual(api.request_page(TOKEN,100),{'count':0,'items':[]})
            request=opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url,'https://api.vk.com/method/wall.get')
            self.assertEqual(parse_qs(request.data.decode()),{'access_token':[TOKEN],'v':['5.199'],'owner_id':[str(api.OWNER_ID)],'filter':['owner'],'count':['100'],'offset':['100']})
            self.assertIsInstance(opener.call_args.args[0],api.NoRedirect)
            sleep.assert_called_once_with(.36)
        with self.assertRaises(api.WallReadError):api.NoRedirect().redirect_request(None,None,None,None,None,'https://other.test')

    def test_bad_offsets_missing_key_and_oversized_or_invalid_responses(self):
        with patch.object(api,'build_opener')as opener:
            for offset in [-100,1,600,True]:
                with self.assertRaises(api.WallReadError):api.request_page(TOKEN,offset)
            with self.assertRaises(api.WallReadError):api.request_page('',0)
            opener.assert_not_called()
        for body in [b'x'*(api.MAX_BYTES+1),b'not JSON']:
            response=Response({});response.body=body
            with patch.object(api,'build_opener')as opener,patch.object(api.time,'sleep'):
                opener.return_value.open.return_value=response
                with self.assertRaises(api.WallReadError):api.request_page(TOKEN,0)

    def test_errors_are_sanitized_without_retry(self):
        for code in [5,6,27,1051]:
            with patch.object(api,'build_opener')as opener,patch.object(api.time,'sleep'):
                opener.return_value.open.return_value=Response({'error':{'error_code':code,'error_msg':TOKEN,'request_params':[TOKEN]}})
                with self.assertRaises(api.WallReadError)as error:api.request_page(TOKEN,0)
                self.assertEqual(error.exception.code,code);self.assertNotIn(TOKEN,str(error.exception))
                self.assertEqual(opener.return_value.open.call_count,1)

    def test_only_valid_community_posts_can_be_candidates(self):
        for item in [None,post(owner_id=1),post(from_id=1),post(id=True),post(date=0),post(text=None),post(text='Просто новый день'),post(text='Новый бренд'),post(attachments=[])]:
            self.assertIsNone(api.candidate(item))

    def test_keywords_and_current_names_select_without_assigning_staff_or_service(self):
        for text in ['Милена Малышевская','Соня Кид','Светлана Дёмина','Любовь Шкляева','Софья Шалагинова','Дарья Мерзлякова','#ТоварищСоня','Детская стрижка','Оформление бороды']:
            value=api.candidate(post(text=text))
            self.assertIsNotNone(value,text)
            self.assertEqual(value['text'],text)
            for forbidden in ['masterId','masterName','service','category','haircut']:self.assertNotIn(forbidden,value)

    def test_all_own_photo_attachments_use_largest_declared_safe_sizes(self):
        large={'url':'https://sun9.vkuserphoto.ru/b.jpg?sign=public-original','width':2560,'height':3413}
        first=photo(sizes=[photo()['photo']['sizes'][0],large])
        value=api.candidate(post(attachments=[None,first,photo(21),photo(22,owner_id=1),{'type':'video','video':{}},first]))
        self.assertEqual([p['id']for p in value['photos']],[20,21])
        self.assertEqual(value['photos'][0]['image'],large)
        self.assertEqual(value['photos'][0]['albumId'],-7)
        self.assertEqual(value['url'],'https://vk.ru/wall-210007626_10')

    def test_unsafe_urls_and_bad_photo_ids_or_dimensions_are_excluded(self):
        for item in [photo(id=0),photo(id=True),photo(owner_id=1),photo(sizes=[None]),photo(sizes=[{'url':'https://localhost/secret','width':2560,'height':3000}]),photo(sizes=[{'url':'https://sun1.userapi.com/a?access_token=private','width':2560,'height':3000}]),photo(sizes=[{'url':'https://sun1.userapi.com/a','width':True,'height':3000}])]:
            self.assertIsNone(api.candidate(post(attachments=[item])))

    def test_six_page_limit_and_explicit_public_wall_source(self):
        pages=[{'count':1000,'items':[post(page*100+i+1,text='Без тематических слов') for i in range(100)]}for page in range(6)]
        with patch.object(api,'request_page',side_effect=pages)as request:
            value=api.collect(TOKEN)
            self.assertEqual(request.call_count,6)
            self.assertEqual([call.args[1]for call in request.call_args_list],[0,100,200,300,400,500])
        self.assertEqual(value['postsScanned'],600);self.assertEqual(value['pagesRead'],6)
        self.assertEqual(value['source'],'vk-public-wall')

    def test_120_candidate_limit_deduplication_and_early_completion(self):
        pages=[{'count':1000,'items':[post(i+1)for i in range(100)]},{'count':1000,'items':[post(1),*[post(i+101)for i in range(99)]]}]
        with patch.object(api,'request_page',side_effect=pages)as request:value=api.collect(TOKEN)
        self.assertEqual(len(value['posts']),120);self.assertEqual(request.call_count,2)
        self.assertEqual(len({p['id']for p in value['posts']}),120);self.assertTrue(value['candidateLimitReached'])
        self.assertEqual(value['postsReceived'],200);self.assertEqual(value['postsScanned'],121)
        with patch.object(api,'request_page',return_value={'count':1,'items':[post()]})as request:
            self.assertEqual(len(api.collect(TOKEN)['posts']),1);request.assert_called_once()

    def test_artifact_and_per_post_logs_are_allowlisted_and_preserve_author_text(self):
        snapshot={'source':'vk-public-wall','pagesRead':1,'postsScanned':1,'postsReceived':1,'posts':[api.candidate(post())]}
        with TemporaryDirectory()as directory,patch.dict(api.os.environ,{'VK_TOKEN':TOKEN}),patch.object(api,'collect',return_value=snapshot),contextlib.redirect_stdout(StringIO())as output:
            path=Path(directory)/'works.json';self.assertEqual(api.main(['--output',str(path)]),0)
            artifact=json.loads(path.read_text(encoding='utf-8'))
        lines=output.getvalue().splitlines();self.assertEqual(len(lines),2)
        self.assertTrue(lines[0].startswith('SOYUZ_PUBLIC_WORK_POST='))
        self.assertIn('Стрижка',lines[0]);self.assertNotIn('userapi',lines[0]);self.assertNotIn(TOKEN,output.getvalue())
        self.assertEqual(artifact['posts'][0]['photos'][0]['image']['width'],1280)

    def test_failure_retains_old_snapshot_and_never_logs_raw_error_or_key(self):
        with TemporaryDirectory()as directory,patch.dict(api.os.environ,{'VK_TOKEN':TOKEN}),patch.object(api,'collect',side_effect=api.WallReadError('api_error',1051)),contextlib.redirect_stdout(StringIO())as output:
            path=Path(directory)/'works.json';path.write_text('previous success')
            self.assertEqual(api.main(['--output',str(path)]),1)
            self.assertEqual(path.read_text(),'previous success')
            self.assertEqual(json.loads(path.with_name('works.error.json').read_text()),{'category':'api_error','code':1051})
        self.assertNotIn(TOKEN,output.getvalue())

    def test_reflected_key_is_blocked_before_artifact_or_log(self):
        with TemporaryDirectory()as directory:
            path=Path(directory)/'works.json'
            with self.assertRaises(api.WallReadError):api.save({'text':TOKEN},path,TOKEN)
            self.assertFalse(path.exists())


if __name__=='__main__':unittest.main()
