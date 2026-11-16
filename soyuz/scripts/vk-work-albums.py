"""Read public SOYUZ photo albums through the official server-side VK API.

Discovery reads album metadata only. An explicit album-ID list enables photos.get.
No browser requests, account writes, media downloads or staff-name guesses.
"""
from __future__ import annotations
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
API_VERSION = '5.199'
MAX_RESPONSE_BYTES = 4_000_000
MAX_ITEMS = 10_000
PAGE_SIZE = 100
METHODS = frozenset({'photos.getAlbums', 'photos.get'})


class ReadError(Exception):
    def __init__(self, category, code=None):
        self.category, self.code = category, code
        super().__init__(category + (f' ({code})' if code is not None else ''))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ReadError('unexpected_redirect')


def request_api(token, method, parameters):
    if method not in METHODS:
        raise ReadError('invalid_method')
    if not isinstance(token, str) or not token.strip():
        raise ReadError('missing_token')
    # The community and credential can never be overridden by caller parameters.
    fields = {**parameters, 'owner_id': OWNER_ID, 'access_token': token, 'v': API_VERSION}
    request = Request('https://api.vk.com/method/' + method,
                      data=urlencode(fields).encode('utf-8'),
                      headers={'Content-Type': 'application/x-www-form-urlencoded',
                               'User-Agent': 'SOYUZ-WorkAlbums/1.0'})
    for attempt in range(3):
        time.sleep(.36 if attempt == 0 else attempt)
        try:
            with build_opener(NoRedirect()).open(request, timeout=20) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except ReadError:
            raise
        except (URLError, OSError, TimeoutError):
            raise ReadError('network_error') from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ReadError('response_too_large')
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            raise ReadError('invalid_json') from None
        if not isinstance(payload, dict):
            raise ReadError('invalid_response')
        if 'error' in payload:
            error = payload['error']
            code = error.get('error_code') if isinstance(error, dict) else None
            code = code if type(code) is int else None
            if code == 6 and attempt < 2:
                continue
            # VK error_msg/request_params may echo credentials; never retain them.
            raise ReadError('api_error', code)
        response = payload.get('response')
        if not isinstance(response, dict):
            raise ReadError('invalid_response')
        return response
    raise ReadError('api_error', 6)


def read_pages(token, method, parameters):
    items, expected = [], None
    while expected is None or len(items) < expected:
        response = request_api(token, method, {**parameters, 'offset': len(items), 'count': PAGE_SIZE})
        count, page = response.get('count'), response.get('items')
        if type(count) is not int or not 0 <= count <= MAX_ITEMS or not isinstance(page, list):
            raise ReadError('invalid_page')
        if expected is not None and count != expected:
            raise ReadError('collection_changed')
        expected = count
        if len(items) + len(page) > expected or len(page) > PAGE_SIZE:
            raise ReadError('invalid_page')
        if not page and len(items) < expected:
            raise ReadError('incomplete_collection')
        items.extend(page)
    return items


def positive_integer(value):
    return type(value) is int and value > 0


def caption(value):
    if not isinstance(value, str):
        raise ReadError('invalid_caption')
    return value


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


def normalize_albums(items):
    albums, seen = [], set()
    for item in items:
        if not isinstance(item, dict) or item.get('owner_id') != OWNER_ID:
            continue
        album_id, size = item.get('id'), item.get('size')
        if not positive_integer(album_id) or type(size) is not int or size < 0:
            raise ReadError('invalid_album')
        if album_id in seen:
            raise ReadError('duplicate_album')
        seen.add(album_id)
        albums.append({'id': album_id, 'ownerId': OWNER_ID,
                       'url': f'https://vk.ru/album{OWNER_ID}_{album_id}',
                       'title': caption(item.get('title')),
                       'description': caption(item.get('description', '')),
                       'size': size})
    return albums


def normalize_photos(items, album_id):
    photos, seen = [], set()
    for item in items:
        if not isinstance(item, dict) or item.get('owner_id') != OWNER_ID:
            continue
        photo_id = item.get('id')
        if not positive_integer(photo_id) or item.get('album_id') != album_id:
            raise ReadError('invalid_photo')
        if photo_id in seen:
            raise ReadError('duplicate_photo')
        seen.add(photo_id)
        sizes = item.get('sizes', [])
        if not isinstance(sizes, list):
            raise ReadError('invalid_sizes')
        available = [size for size in sizes if isinstance(size, dict)
                     and public_image(size.get('url'))
                     and positive_integer(size.get('width')) and positive_integer(size.get('height'))
                     and max(size['width'], size['height']) <= 40000
                     and size['width'] * size['height'] <= 100_000_000]
        largest = max(available, key=lambda size: (size['width'] * size['height'], size['width']), default=None)
        photos.append({'id': photo_id, 'ownerId': OWNER_ID, 'albumId': album_id,
                       'url': f'https://vk.ru/photo{OWNER_ID}_{photo_id}',
                       'caption': caption(item.get('text', '')),
                       'date': item['date'] if type(item.get('date')) is int else None,
                       'image': {key: largest[key] for key in ['url', 'width', 'height']} if largest else None})
    return photos


def parse_album_ids(value):
    if not value.strip():
        return []
    if not re.fullmatch(r'[1-9]\d*(?:\s*,\s*[1-9]\d*)*', value.strip()):
        raise ReadError('invalid_album_ids')
    ids = list(dict.fromkeys(int(item.strip()) for item in value.split(',')))
    if len(ids) > 20:
        raise ReadError('too_many_albums')
    return ids


def collect(token, album_ids):
    albums = normalize_albums(read_pages(token, 'photos.getAlbums', {'need_system': 0, 'need_covers': 0}))
    by_id = {album['id']: album for album in albums}
    if any(album_id not in by_id for album_id in album_ids):
        raise ReadError('unknown_album_id')
    for album_id in album_ids:
        photos = normalize_photos(read_pages(token, 'photos.get', {'album_id': album_id, 'photo_sizes': 1, 'extended': 0}), album_id)
        by_id[album_id]['photos'] = photos
    return {'source': 'official-vk-api', 'ownerId': OWNER_ID,
            'generatedAt': datetime.now(timezone.utc).isoformat(),
            'requestedAlbumIds': album_ids, 'albums': albums}


def save_snapshot(snapshot, path, token):
    serialized = json.dumps(snapshot, ensure_ascii=False, indent=2)
    if token and token in serialized:
        raise ReadError('secret_in_response')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(serialized + '\n', encoding='utf-8')
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--album-ids', default='', help='Explicit positive IDs from the discovery catalog, comma-separated')
    parser.add_argument('--output', type=Path, default=Path('artifacts/vk-works.json'))
    args = parser.parse_args(argv)
    token = os.environ.get('SOYUZ_VK_TOKEN') or os.environ.get('VK_TOKEN')
    try:
        if not token:
            raise ReadError('missing_token')
        snapshot = collect(token, parse_album_ids(args.album_ids))
        save_snapshot(snapshot, args.output, token)
        catalog = [{key: album[key] for key in ['id', 'title', 'size']} |
                   {'descriptionPreview': album['description'][:400]} for album in snapshot['albums']]
        print('SOYUZ_ALBUM_CATALOG=' + json.dumps(catalog, ensure_ascii=False, separators=(',', ':')))
        print('SOYUZ_WORKS_RESULT=' + json.dumps({'albumCount': len(catalog),
              'requestedAlbumCount': len(snapshot['requestedAlbumIds']),
              'photoCount': sum(len(album.get('photos', [])) for album in snapshot['albums'])}))
        return 0
    except Exception as error:
        safe = {'status': 'error', 'category': error.category if isinstance(error, ReadError) else 'internal_error'}
        if isinstance(error, ReadError) and error.code is not None:
            safe['code'] = error.code
        # Keep an existing successful snapshot intact; retain only a safe diagnostic.
        error_path = args.output.with_name(args.output.stem + '.error.json')
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.write_text(json.dumps(safe) + '\n', encoding='utf-8')
        print('SOYUZ_WORKS_ERROR=' + json.dumps(safe))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
