"""Read the official VK API or public widget; retain ten latest SOYUZ posts.

Same delivery boundary as SF: worker -> public snapshot/local images -> website.
The optional server token is sent only to wall.get; public output contains no token.
No private messages or account mutations are used.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
from html.parser import HTMLParser
from io import BytesIO
import json
import importlib.util
import os
from pathlib import Path
import re
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
GROUP_ID = 210007626
LIMIT = 10
EXCLUDED_POST_IDS = frozenset(json.loads((ROOT / 'content/news-policy.json').read_text(encoding='utf-8'))['excludedPostIds'])
MOSCOW = timezone(timedelta(hours=3))
WIDGET = 'https://vk.ru/widget_community.php'
MONTHS = ['янв', 'фев', 'мар', 'апр', 'ма', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


def public_image(url):
    try:
        p = urlparse(url)
        return p.scheme == 'https' and not p.username and not p.password and p.hostname.endswith(('.userapi.com', '.vkuserphoto.ru'))
    except (ValueError, AttributeError):
        return False


def read(url, data=None, image=False):
    if image and not public_image(url):
        raise ValueError('Unexpected image host')
    req = Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0', 'Referer': WIDGET, 'X-Requested-With': 'XMLHttpRequest'})
    def permitted(value):
        return public_image(value) if image else urlparse(value).scheme == 'https' and urlparse(value).hostname == 'vk.ru'
    class Redirect(HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            if not permitted(newurl): raise ValueError('Unexpected source redirect')
            return super().redirect_request(request, fp, code, msg, headers, newurl)
    with build_opener(Redirect()).open(req, timeout=20) as response:
        if not permitted(response.url):
            raise ValueError('Unexpected source redirect')
        cap = 12_000_000 if image else 4_000_000
        body = response.read(cap + 1)
        if len(body) > cap:
            raise ValueError('Source exceeds size budget')
        return body


def date_from_label(label, now):
    value = re.sub(r'\s+', ' ', label).strip().lower()
    clock = re.search(r'(\d{1,2}):(\d{2})', value)
    hour, minute = map(int, clock.groups()) if clock else (0, 0)
    if 'сегодня' in value or 'вчера' in value:
        return (now - timedelta(days=int('вчера' in value))).replace(hour=hour, minute=minute, second=0, microsecond=0)
    match = re.search(r'(\d{1,2})\s+([а-яё]+)(?:\s+(\d{4}))?', value)
    if not match:
        raise ValueError('Unrecognized public post date')
    day, month, year = match.groups()
    month_number = next((i + 1 for i, prefix in enumerate(MONTHS) if month.startswith(prefix)), None)
    if not month_number:
        raise ValueError('Unrecognized month')
    stamp = datetime(int(year or now.year), month_number, int(day), hour, minute, tzinfo=MOSCOW)
    if not year and stamp > now:
        stamp = stamp.replace(year=now.year - 1)
    return stamp


class Posts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.items = [], []
        self.post = None
        self.root_depth = self.text_depth = self.date_depth = self.ignore_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get('class', '').split())
        if tag not in VOID:
            self.stack.append(tag)
        depth = len(self.stack)
        if 'wcommunity_post' in classes:
            self.post = {'text': [], 'date': [], 'photos': [], 'fallback': []}
            self.root_depth = depth
        if self.post is None:
            return
        if not self.ignore_depth and any(name.startswith('PostTextMore') for name in classes):
            self.ignore_depth = depth
        if 'wcommunity_post_date' in classes:
            match = re.fullmatch(r'/wall-' + str(GROUP_ID) + r'_(\d+)', attrs.get('href', ''))
            if match:
                self.post['id'] = int(match[1])
                self.date_depth = depth
        if 'wall_post_text' in classes:
            self.text_depth = depth
        if tag == 'br' and self.text_depth:
            self.post['text'].append('\n')
        click = attrs.get('onclick', '')
        if 'showPhoto(' in click:
            match = re.search(r'"temp"\s*:\s*', click)
            if match:
                try:
                    temp, _ = json.JSONDecoder().raw_decode(click[match.end():])
                    for key in ['w', 'z', 'y', 'x']:
                        value = temp.get(key)
                        url = next(iter(value), None) if isinstance(value, list) else value
                        if public_image(url):
                            self.post['photos'].append(url)
                            break
                except (ValueError, AttributeError, TypeError):
                    pass
        candidates = [attrs.get('src', '')] + re.findall(r'url\([\s\'"]*(https:[^\)\s\'"]+)', attrs.get('style', ''))
        self.post['fallback'].extend(url for url in candidates if public_image(url))

    def handle_data(self, value):
        if self.post is not None:
            if self.text_depth and not self.ignore_depth:
                self.post['text'].append(value)
            if self.date_depth:
                self.post['date'].append(value)

    def handle_endtag(self, tag):
        if tag in self.stack:
            self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]
        depth = len(self.stack)
        if self.post is None:
            return
        if self.text_depth and depth < self.text_depth:
            self.text_depth = 0
        if self.date_depth and depth < self.date_depth:
            self.date_depth = 0
        if self.ignore_depth and depth < self.ignore_depth:
            self.ignore_depth = 0
        if depth < self.root_depth:
            if 'id' in self.post:
                self.items.append(self.post)
            self.post = None


def normalize(html, now):
    parser = Posts()
    parser.feed(html)
    items = []
    for post in parser.items:
        text = ''.join(post['text']).replace('\xa0', ' ')
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        if not text:
            continue
        stamp = date_from_label(''.join(post['date']), now)
        photos = list(dict.fromkeys(post['photos'] or post['fallback']))
        if not post['photos']:
            photos.sort(key=photo_width, reverse=True)
        items.append({'id': str(post['id']), 'publishedAt': stamp.isoformat(), 'text': text,
                      'url': f'https://vk.ru/wall-{GROUP_ID}_{post["id"]}',
                      'photo': next(iter(photos), None)})
    return items


def photo_width(url):
    params = parse_qs(urlparse(url).query)
    available = [int(w) for w in re.findall(r'(\d+)x\d+', params.get('as', [''])[0])]
    if available:
        return max(available)
    size = re.match(r'(\d+)x\d+', params.get('size', params.get('cs', ['0x0']))[0])
    return int(size[1]) if size else 0


def photo_key(url):
    # VK's immutable CDN path identifies the attachment; signed size parameters do not.
    return hashlib.sha256(urlparse(url).path.encode('utf-8')).hexdigest() if url else None


def export_photo(post, directory):
    if not post['photo']:
        return None
    url = urlparse(post['photo'])
    params = parse_qs(url.query)
    available = [int(width) for width in re.findall(r'(\d+)x\d+', params.get('as', [''])[0])]
    if available and post.get('photoSource')!='api':
        params['cs'] = [f'{min(1600, max(available))}x0']
        url = url._replace(query=urlencode(params, doseq=True))
    source = read(urlunparse(url), image=True)
    with Image.open(BytesIO(source)) as opened:
        original = ImageOps.exif_transpose(opened).convert('RGB')
        if min(original.size) < 120:
            return None
        if original.width * original.height > 40_000_000:
            raise ValueError('Unexpected photo dimensions')
        variants = []
        for requested in [640, 1280, 1600]:
            width = min(requested, original.width)
            if any(v['width'] == width for v in variants):
                continue
            height = round(original.height * width / original.width)
            encoded = BytesIO()
            original.resize((width, height), Image.Resampling.LANCZOS).save(encoded, 'WEBP', quality=88, method=6)
            delivered = encoded.getvalue()
            digest = hashlib.sha256(delivered).hexdigest()
            path = directory / f'{post["id"]}-{digest[:12]}-{width}.webp'
            path.write_bytes(delivered)
            variants.append({'url': '../media/news/' + path.name, 'width': width, 'height': height, 'sha256': digest})
    return {'variants': variants, 'sourceSha256': hashlib.sha256(source).hexdigest(), 'sourceKey': photo_key(post['photo']), 'sourceWidth': original.width, 'sourceHeight': original.height}


def update(public_only=False):
    now = datetime.now(MOSCOW)
    token=os.environ.get('SOYUZ_VK_TOKEN')or os.environ.get('VK_TOKEN')
    if not token:
        for path in [ROOT/'content/news.json',ROOT/'public/data/news.json']:
            try: previous_source=json.loads(path.read_text(encoding='utf-8')).get('source')
            except (OSError,ValueError):continue
            if previous_source=='official-vk-api':
                print('Official API snapshot retained; the public widget cannot replace it.')
                return
    if token:
        spec=importlib.util.spec_from_file_location('vk_news_api',Path(__file__).with_name('vk-news-api.py'));api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
        posts=api.fetch_posts(token,GROUP_ID,MOSCOW,public_image)
    else:
        widget_url = WIDGET + '?' + urlencode({'app': 0, 'width': '500px', 'gid': GROUP_ID, 'mode': 4, 'height': 800})
        initial = read(widget_url).decode('windows-1251')
        posts = normalize(initial, now)
        more = read(WIDGET, urlencode({'act': 'load_more', 'offset': 10, 'oid': -GROUP_ID, 'wide': 0, 'width': 474, 'mode': 1, 'al': 1}).encode('ascii'))
        response = json.loads(more.decode('windows-1251').removeprefix('<!--'))
        if response.get('payload', [1])[0] != 0:
            raise ValueError('Public widget did not return posts')
        posts.extend(normalize(response['payload'][1][0], now))
    unique = {p['id']: p for p in posts if p['id'] not in EXCLUDED_POST_IDS}
    latest = sorted(unique.values(), key=lambda p: (p['publishedAt'], int(p['id'])), reverse=True)[:LIMIT]
    if len(latest) != LIMIT:
        raise ValueError('Fewer than ten public posts; retaining previous snapshot')
    directory = ROOT / 'public/media/news'
    directory.mkdir(parents=True, exist_ok=True)
    items = []
    previous_path = ROOT / 'public/data/news.json'
    previous = json.loads(previous_path.read_text(encoding='utf-8')) if previous_path.exists() else {}
    prior_images = {item['id']: item.get('image') for item in previous.get('items', [])}
    for post in latest:
        image = export_photo(post, directory)
        prior = prior_images.get(post['id'])
        current_width = max((v['width'] for v in image['variants']), default=0) if image else 0
        same_photo = post['photo'] and prior and (prior.get('sourceKey') == photo_key(post['photo']) or image and prior.get('sourceSha256') and prior['sourceSha256'] == image.get('sourceSha256'))
        if same_photo and max(v['width'] for v in prior['variants']) > current_width:
            image = prior
        items.append({k:post[k]for k in ['id','publishedAt','text','url']} | {'image': image})
    payload = {'version': 1, 'groupId': -GROUP_ID, 'groupUrl': 'https://vk.ru/soyuz_kirov',
               'generatedAt': now.isoformat(), 'source': 'official-vk-api'if token else'official-public-community-widget', 'items': items}
    data = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
    outputs = [ROOT / 'public/data/news.json'] if public_only else [ROOT / 'content/news.json', ROOT / 'public/data/news.json']
    for output in outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix('.json.tmp')
        temporary.write_text(data, encoding='utf-8')
        temporary.replace(output)
    print('Updated ten latest SOYUZ posts and their local responsive covers; older pinned posts sorted by publication date.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-only', action='store_true', help='Refresh the runtime feed without restarting the local page through content HMR.')
    args = parser.parse_args()
    try:
        update(public_only=args.public_only)
    except Exception as error:
        # Avoid logging signed source URLs or provider responses.
        raise SystemExit(f'News update failed ({type(error).__name__}); previous snapshot retained.') from None
