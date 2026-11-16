"""One-shot read-only VK authorization diagnosis; never emit credentials or raw responses."""
import json
import os
import re
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

METHODS = {'groups.getTokenPermissions', 'account.getAppPermissions', 'photos.getAlbums'}
TOKENS = {value for name in ['VK_TOKEN', 'SOYUZ_VK_PHOTOS_TOKEN'] if (value := os.environ.get(name))}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('redirect_blocked')


def message(value):
    if not isinstance(value, str):
        return 'No public error explanation'
    for token in sorted(TOKENS, key=len, reverse=True):
        value = value.replace(token, '[redacted]')
    value = re.sub(r'https?://\S+|vk1\.[A-Za-z0-9._-]+|(?:access_token|client_secret)\s*[=:]\s*\S+', '[redacted]', value)
    return re.sub(r'\s+', ' ', value)[:240]


def project(payload):
    if isinstance(payload, dict) and isinstance(payload.get('error'), dict):
        error = payload['error']
        return {'ok': False, 'code': error.get('error_code') if isinstance(error.get('error_code'), int) else None,
                'explanation': message(error.get('error_msg'))}
    if not isinstance(payload, dict) or 'response' not in payload:
        return {'ok': False, 'category': 'unexpected_response'}
    response = payload['response']
    if isinstance(response, int):
        return {'ok': True, 'permissionMask': response}
    if isinstance(response, dict) and isinstance(response.get('permissions'), list):
        return {'ok': True, 'permissions': [{'name': p.get('name'), 'setting': p.get('setting')}
                for p in response['permissions'] if isinstance(p, dict) and isinstance(p.get('name'), str)]}
    if isinstance(response, dict) and isinstance(response.get('items'), list):
        return {'ok': True, 'returnedAlbums': len(response['items'])}
    return {'ok': True, 'shape': type(response).__name__}


def request(method, token):
    assert method in METHODS
    if not token:
        return {'ok': False, 'category': 'missing_existing_secret'}
    params = {'access_token': token, 'v': '5.199'}
    if method == 'photos.getAlbums':
        params.update(owner_id=-210007626, count=1, need_system=0, need_covers=0)
    try:
        time.sleep(.36)
        req = Request('https://api.vk.com/method/' + method, data=urlencode(params).encode(), method='POST')
        with build_opener(NoRedirect()).open(req, timeout=20) as response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            return {'ok': False, 'category': 'oversized_response'}
        return project(json.loads(raw))
    except HTTPError as error:
        return {'ok': False, 'category': 'http_error', 'status': error.code}
    except Exception as error:
        return {'ok': False, 'category': type(error).__name__}


def selfcheck():
    TOKENS.add('fixture-secret-value')
    output = json.dumps(project({'error': {'error_code': 1051, 'error_msg': 'Denied fixture-secret-value https://x.test/?access_token=fixture-secret-value', 'request_params': ['fixture-secret-value']}}))
    assert 'fixture-secret-value' not in output and 'x.test' not in output and 'request_params' not in output
    assert project({'response': 4}) == {'ok': True, 'permissionMask': 4}
    assert project({'response': {'count': 20, 'items': [{'private': 'never logged'}]}}) == {'ok': True, 'returnedAlbums': 1}
    TOKENS.remove('fixture-secret-value')
    print('PASS redaction, error projection and response minimization; no network')


if __name__ == '__main__':
    if sys.argv[1:] == ['--selfcheck']:
        selfcheck()
    else:
        jobs = [('VK_TOKEN', 'groups.getTokenPermissions'), ('VK_TOKEN', 'account.getAppPermissions'),
                ('SOYUZ_VK_PHOTOS_TOKEN', 'groups.getTokenPermissions'), ('VK_TOKEN', 'photos.getAlbums')]
        for secret, method in jobs:
            print('SOYUZ_AUTH_DIAGNOSTIC=' + json.dumps({'secretName': secret, 'method': method,
                  'result': request(method, os.environ.get(secret, ''))}, ensure_ascii=False), flush=True)

