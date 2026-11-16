"""Read candidate work photos from the public SOYUZ wall, never photo albums.

Only wall.get is used. Names and haircut words select candidates for human
curation; they never assign a staff member, service or haircut category.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
from urllib.error import URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

OWNER_ID = -210007626
MAX_BYTES = 4_000_000
PAGE_SIZE = 100
MAX_PAGES = 6
MAX_CANDIDATES = 120
HINTS = re.compile(r'\b(?:стриж\w*|стриг\w*|волос\w*|бород\w*|брить\w*|брит\w*|бре(?:ем|ют|ет|ете|ется|ются)\b|детск\w*|мальчик\w*|школьник\w*|милен\w*|сон[яиюе]\w*|светлан\w*|свет[аеуыой]\b|любов\w*|люб[ауыое]\b|софь\w*|дарь\w*|даш[аеуы]\w*)|#товарищ\w*', re.IGNORECASE)


class WallReadError(Exception):
    def __init__(self, category, code=None):
        self.category, self.code = category, code
        super().__init__(category)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise WallReadError('unexpected_redirect')


def request_page(token, offset):
    if not isinstance(token, str) or not token.strip():
        raise WallReadError('missing_token')
    if type(offset) is not int or offset not in range(0, MAX_PAGES * PAGE_SIZE, PAGE_SIZE):
        raise WallReadError('invalid_offset')
    fields = {'access_token':token, 'v':'5.199', 'owner_id':OWNER_ID,
              'filter':'owner', 'count':PAGE_SIZE, 'offset':offset}
    request = Request('https://api.vk.com/method/wall.get', data=urlencode(fields).encode('utf-8'),
                      headers={'Content-Type':'application/x-www-form-urlencoded',
                               'User-Agent':'SOYUZ-PublicWorkPhotos/1.0'})
    time.sleep(.36)
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            raw = response.read(MAX_BYTES + 1)
    except WallReadError:
        raise
    except (URLError, OSError, TimeoutError):
        raise WallReadError('network_error') from None
    if len(raw) > MAX_BYTES:
        raise WallReadError('response_too_large')
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeError):
        raise WallReadError('invalid_json') from None
    if not isinstance(payload, dict):
        raise WallReadError('invalid_response')
    if 'error' in payload:
        error = payload['error']
        code = error.get('error_code') if isinstance(error, dict) else None
        raise WallReadError('api_error', code if type(code) is int else None)
    response = payload.get('response')
    if (not isinstance(response, dict) or type(response.get('count')) is not int
            or response['count'] < 0 or not isinstance(response.get('items'), list)
            or len(response['items']) > PAGE_SIZE):
        raise WallReadError('invalid_response')
    return response


def positive(value):
    return type(value) is int and value > 0


def public_image(url):
    try:
        parsed = urlparse(url)
        return (parsed.scheme == 'https' and not parsed.username and not parsed.password
                and parsed.port in (None, 443) and not parsed.fragment
                and parsed.hostname.endswith(('.userapi.com', '.vkuserphoto.ru'))
                and not any(key.lower() in {'access_token', 'authorization', 'oauth_token'}
                            for key in parse_qs(parsed.query)))
    except (TypeError, ValueError, AttributeError):
        return False


def candidate(post):
    if (not isinstance(post, dict) or post.get('owner_id') != OWNER_ID
            or post.get('from_id') != OWNER_ID or not positive(post.get('id'))
            or not positive(post.get('date')) or not isinstance(post.get('text'), str)):
        return None
    text = post['text'].strip()
    if not text or not HINTS.search(text.replace('ё', 'е').replace('Ё', 'Е')):
        return None
    attachments = post.get('attachments', [])
    photos, seen = [], set()
    for attachment in attachments if isinstance(attachments, list) else []:
        if not isinstance(attachment, dict) or attachment.get('type') != 'photo':
            continue
        photo = attachment.get('photo')
        if (not isinstance(photo, dict) or photo.get('owner_id') != OWNER_ID
                or not positive(photo.get('id')) or photo['id'] in seen):
            continue
        sizes = photo.get('sizes', [])
        safe = [size for size in sizes if isinstance(size, dict)
                and public_image(size.get('url')) and positive(size.get('width'))
                and positive(size.get('height')) and max(size['width'], size['height']) <= 40000
                and size['width'] * size['height'] <= 100_000_000] if isinstance(sizes, list) else []
        largest = max(safe, key=lambda size:(size['width'] * size['height'], size['width']), default=None)
        if largest is None:
            continue
        seen.add(photo['id'])
        photos.append({'id':photo['id'], 'ownerId':OWNER_ID,
                       'albumId':photo['album_id'] if type(photo.get('album_id')) is int else None,
                       'url':f'https://vk.ru/photo{OWNER_ID}_{photo["id"]}',
                       'image':{key:largest[key] for key in ['url', 'width', 'height']}})
    if not photos:
        return None
    return {'id':post['id'], 'ownerId':OWNER_ID, 'date':post['date'], 'text':text,
            'url':f'https://vk.ru/wall{OWNER_ID}_{post["id"]}', 'photos':photos}


def collect(token):
    posts, seen, scanned, received, pages = [], set(), 0, 0, 0
    for page in range(MAX_PAGES):
        response = request_page(token, page * PAGE_SIZE)
        pages += 1
        received += len(response['items'])
        for post in response['items']:
            scanned += 1
            item = candidate(post)
            if item is not None and item['id'] not in seen:
                posts.append(item); seen.add(item['id'])
                if len(posts) == MAX_CANDIDATES:
                    break
        if len(posts) == MAX_CANDIDATES or not response['items'] or (page + 1) * PAGE_SIZE >= response['count']:
            break
    return {'source':'vk-public-wall', 'ownerId':OWNER_ID,
            'generatedAt':datetime.now(timezone.utc).isoformat(),
            'pagesRead':pages, 'postsScanned':scanned, 'postsReceived':received,
            'candidateLimitReached':len(posts) == MAX_CANDIDATES, 'posts':posts}


def save(snapshot, path, token):
    encoded = json.dumps(snapshot, ensure_ascii=False, indent=2)
    if token and token in encoded:
        raise WallReadError('secret_in_response')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(encoded + '\n', encoding='utf-8')
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('artifacts/vk-public-work-photos.json'))
    args = parser.parse_args(argv)
    token = os.environ.get('VK_TOKEN')
    try:
        if not token:
            raise WallReadError('missing_token')
        snapshot = collect(token)
        save(snapshot, args.output, token)
        for post in snapshot['posts']:
            metadata = {key:post[key] for key in ['id', 'date', 'url', 'text']}
            metadata['photos'] = [{'id':photo['id'], 'albumId':photo['albumId'],
                                   'width':photo['image']['width'], 'height':photo['image']['height']}
                                  for photo in post['photos']]
            print('SOYUZ_PUBLIC_WORK_POST=' + json.dumps(metadata, ensure_ascii=False, separators=(',', ':')))
        print('SOYUZ_PUBLIC_WORK_RESULT=' + json.dumps({
            'source':'vk-public-wall', 'pagesRead':snapshot['pagesRead'], 'postsScanned':snapshot['postsScanned'],
            'postsReceived':snapshot['postsReceived'],
            'candidateCount':len(snapshot['posts']), 'photoCount':sum(len(post['photos']) for post in snapshot['posts'])}))
        return 0
    except Exception as error:
        safe = {'category':error.category if isinstance(error, WallReadError) else 'internal_error'}
        if isinstance(error, WallReadError) and error.code is not None:
            safe['code'] = error.code
        error_path = args.output.with_name(args.output.stem + '.error.json')
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.write_text(json.dumps(safe) + '\n', encoding='utf-8')
        print('SOYUZ_PUBLIC_WORK_ERROR=' + json.dumps(safe, separators=(',', ':')))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
