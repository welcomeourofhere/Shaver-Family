import contextlib
import importlib.util
from io import StringIO
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('vk_app_metadata', ROOT/'scripts/vk-app-metadata.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
TOKEN = 'fixture-only-app-key'
APP = {'id':123456, 'title':'Shaver Family', 'type':'standalone'}


class Response:
    def __init__(self, value): self.body=json.dumps(value).encode()
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, limit): return self.body[:limit]


class AppMetadata(unittest.TestCase):
    def test_one_fixed_read_method_no_app_id_posted_key_no_redirect(self):
        with patch.object(api, 'build_opener') as opener:
            opener.return_value.open.return_value=Response({'response':{'count':1,'items':[APP]}})
            self.assertEqual(api.read_app_metadata(TOKEN), APP)
            request=opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, 'https://api.vk.com/method/apps.get')
            self.assertEqual(parse_qs(request.data.decode()), {'access_token':[TOKEN],'v':['5.199']})
            self.assertEqual(request.get_method(), 'POST')
            self.assertIsInstance(opener.call_args.args[0], api.NoRedirect)
            self.assertEqual(opener.return_value.open.call_count, 1)
        with self.assertRaises(api.MetadataError): api.NoRedirect().redirect_request(None,None,None,None,None,'https://other.test')

    def test_result_is_an_allowlist_without_urls_credentials_or_other_data(self):
        app={**APP,'icon_75':'https://cdn.test/icon','author_url':'https://test','access_token':TOKEN,'secret':TOKEN}
        with patch.object(api,'build_opener') as opener:
            opener.return_value.open.return_value=Response({'response':{'count':1,'items':[app],'request_params':[TOKEN]}})
            result=api.read_app_metadata(TOKEN)
        self.assertEqual(result, APP)
        for forbidden in [TOKEN,'https://','request_params','secret']: self.assertNotIn(forbidden,json.dumps(result))

    def test_refusals_including_rate_limit_are_not_retried_or_echoed(self):
        for code in [5,6,27,1051]:
            with patch.object(api,'build_opener') as opener:
                opener.return_value.open.return_value=Response({'error':{'error_code':code,'error_msg':TOKEN,'request_params':[TOKEN]}})
                with self.assertRaises(api.MetadataError) as error: api.read_app_metadata(TOKEN)
                self.assertEqual(error.exception.code,code)
                self.assertNotIn(TOKEN,str(error.exception))
                self.assertEqual(opener.return_value.open.call_count,1)

    def test_512kb_budget_invalid_json_and_missing_token(self):
        for body in [b'x'*(api.LIMIT+1),b'not JSON']:
            response=Response({});response.body=body
            with patch.object(api,'build_opener') as opener:
                opener.return_value.open.return_value=response
                with self.assertRaises(api.MetadataError): api.read_app_metadata(TOKEN)
        with patch.object(api,'build_opener') as opener:
            with self.assertRaises(api.MetadataError): api.read_app_metadata('')
            opener.assert_not_called()

    def test_no_guessing_when_empty_multiple_or_inconsistent_apps(self):
        for response in [{'count':0,'items':[]},{'count':2,'items':[APP,APP]},{'count':2,'items':[APP]}, {'items':None}]:
            with patch.object(api,'build_opener') as opener:
                opener.return_value.open.return_value=Response({'response':response})
                with self.assertRaises(api.MetadataError): api.read_app_metadata(TOKEN)

    def test_invalid_ids_types_or_reflected_key_are_rejected(self):
        for app in [{**APP,'id':True},{**APP,'id':0},{**APP,'type':'https://test'}, {**APP,'title':TOKEN}]:
            with patch.object(api,'build_opener') as opener:
                opener.return_value.open.return_value=Response({'response':{'items':[app]}})
                with self.assertRaises(api.MetadataError): api.read_app_metadata(TOKEN)

    def test_network_error_is_not_logged_with_its_url_or_key(self):
        with patch.object(api,'build_opener') as opener:
            opener.return_value.open.side_effect=URLError('https://example.test/?access_token='+TOKEN)
            with self.assertRaises(api.MetadataError) as error: api.read_app_metadata(TOKEN)
            self.assertEqual(error.exception.category,'network_error')
            self.assertNotIn(TOKEN,str(error.exception))

    def test_cli_uses_only_vk_token_and_logs_only_allowlisted_metadata(self):
        with patch.dict(api.os.environ,{'VK_TOKEN':TOKEN,'SOYUZ_VK_TOKEN':'unused-photo-key'}), patch.object(api,'read_app_metadata',return_value=APP) as read, contextlib.redirect_stdout(StringIO()) as output:
            self.assertEqual(api.main(),0)
            read.assert_called_once_with(TOKEN)
        self.assertEqual(output.getvalue().strip(), 'SOYUZ_VK_APP_METADATA='+json.dumps(APP,separators=(',',':')))
        with patch.object(api,'read_app_metadata',side_effect=api.MetadataError('api_error',1051)), contextlib.redirect_stdout(StringIO()) as output:
            self.assertEqual(api.main(),1)
        self.assertEqual(output.getvalue().strip(),'SOYUZ_VK_APP_ERROR={"category":"api_error","code":1051}')


if __name__ == '__main__': unittest.main()
