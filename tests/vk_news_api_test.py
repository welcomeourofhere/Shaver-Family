import importlib.util
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
api=load('vk_api','scripts/vk-news-api.py')
worker=load('vk_worker','scripts/update-vk-news.py')

class APINews(unittest.TestCase):
    def test_multi_photo_keeps_the_first_attachment_at_its_largest_signed_size(self):
        sizes=[{'width':width,'url':f'https://sun1.userapi.com/first.jpg?size={width}x{width}&sign=fixture'}for width in [97,1280,604]]
        post={'id':12,'owner_id':-worker.GROUP_ID,'date':1794690000,'text':'Новость','attachments':[{'type':'photo','photo':{'sizes':sizes}},{'type':'photo','photo':{'sizes':[{'width':1600,'url':'https://sun1.userapi.com/second.jpg'}]}}]}
        result=api.normalize_posts([None,post,post|{'owner_id':-1}],worker.GROUP_ID,worker.MOSCOW,worker.public_image)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['photo'],sizes[1]['url'])
        self.assertEqual(result[0]['photoSource'],'api')

    def test_post_request_keeps_the_key_out_of_the_url_and_follows_no_redirect(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,limit):return json.dumps({'response':{'items':[]}}).encode()
        with patch.object(api,'build_opener')as opener:
            opener.return_value.open.return_value=Response()
            self.assertEqual(api.fetch_posts('fixture-only-key',worker.GROUP_ID,worker.MOSCOW,worker.public_image),[])
            request=opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url,'https://api.vk.com/method/wall.get')
            self.assertEqual(parse_qs(request.data.decode())['access_token'],['fixture-only-key'])
            self.assertIsInstance(opener.call_args.args[0],api.NoRedirect)
        with self.assertRaises(ValueError):api.NoRedirect().redirect_request(None,None,None,None,None,'https://example.com')

    def test_api_signed_url_is_used_verbatim_and_the_output_never_enlarges_it(self):
        image=BytesIO();Image.new('RGB',(800,1200),'#cd2a25').save(image,'JPEG')
        post={'id':'12','photo':'https://sun1.userapi.com/a.jpg?as=97x146,1600x2400&cs=800x0&sign=fixture','photoSource':'api'}
        with TemporaryDirectory()as directory,patch.object(worker,'read',return_value=image.getvalue())as read:
            result=worker.export_photo(post,Path(directory))
            self.assertEqual(read.call_args.args[0],post['photo'])
            self.assertEqual([v['width']for v in result['variants']],[640,800])
            self.assertNotIn('sign=',json.dumps(result))
            self.assertNotIn('userapi',json.dumps(result))

    def test_malformed_sizes_and_unsafe_photo_urls_are_not_published(self):
        post={'id':1,'owner_id':-worker.GROUP_ID,'date':1794690000,'text':'Новость','attachments':[None,{'type':'photo','photo':{'sizes':[None,{'width':1600,'url':'https://localhost/secret'},{'width':'1600','url':'https://sun1.userapi.com/a.jpg'}]}}]}
        result=api.normalize_posts([post],worker.GROUP_ID,worker.MOSCOW,worker.public_image)
        self.assertIsNone(result[0]['photo'])

if __name__=='__main__':unittest.main()
