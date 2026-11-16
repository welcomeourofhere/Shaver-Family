"""Read only public id/title/type for the app associated with an existing key.

apps.get is called without app_id/app_ids. Accept one unambiguous app only;
the caller verifies the returned identity before any separate access setup.
"""
import json
import os
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

LIMIT = 512 * 1024
APP_TYPES = frozenset({'app', 'game', 'site', 'standalone', 'vk_app',
                       'community_app', 'html5_game', 'mini_app'})


class MetadataError(Exception):
    def __init__(self, category, code=None):
        self.category, self.code = category, code
        super().__init__(category)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise MetadataError('unexpected_redirect')


def read_app_metadata(token):
    if not isinstance(token, str) or not token.strip():
        raise MetadataError('missing_token')
    request = Request('https://api.vk.com/method/apps.get',
                      data=urlencode({'access_token':token, 'v':'5.199'}).encode('utf-8'),
                      headers={'Content-Type':'application/x-www-form-urlencoded',
                               'User-Agent':'SOYUZ-AppMetadata/1.0'})
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            raw = response.read(LIMIT + 1)
    except MetadataError:
        raise
    except (URLError, OSError, TimeoutError):
        raise MetadataError('network_error') from None
    if len(raw) > LIMIT:
        raise MetadataError('response_too_large')
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeError):
        raise MetadataError('invalid_json') from None
    if not isinstance(payload, dict):
        raise MetadataError('invalid_response')
    if 'error' in payload:
        error = payload['error']
        code = error.get('error_code') if isinstance(error, dict) else None
        raise MetadataError('api_error', code if type(code) is int else None)
    response = payload.get('response')
    items = response.get('items') if isinstance(response, dict) else None
    if not isinstance(items, list) or len(items) != 1:
        raise MetadataError('ambiguous_app_metadata')
    count = response.get('count', 1)
    if type(count) is not int or count != 1:
        raise MetadataError('ambiguous_app_metadata')
    app = items[0]
    if (not isinstance(app, dict) or type(app.get('id')) is not int or app['id'] <= 0
            or not isinstance(app.get('title'), str) or not app['title'].strip()
            or len(app['title']) > 512 or app.get('type') not in APP_TYPES):
        raise MetadataError('invalid_app_metadata')
    result = {key:app[key] for key in ['id', 'title', 'type']}
    if token in json.dumps(result, ensure_ascii=False):
        raise MetadataError('secret_in_response')
    return result


def main():
    try:
        metadata = read_app_metadata(os.environ.get('VK_TOKEN'))
        print('SOYUZ_VK_APP_METADATA=' + json.dumps(metadata, ensure_ascii=False, separators=(',', ':')))
        return 0
    except Exception as error:
        safe = {'category':error.category if isinstance(error, MetadataError) else 'internal_error'}
        if isinstance(error, MetadataError) and error.code is not None:
            safe['code'] = error.code
        print('SOYUZ_VK_APP_ERROR=' + json.dumps(safe, separators=(',', ':')))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
