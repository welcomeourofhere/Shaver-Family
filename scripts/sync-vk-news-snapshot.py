"""Sync the verified public GitHub feed and its hashed images into the local fallback."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.parse import urljoin
from urllib.request import Request,build_opener,HTTPRedirectHandler
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED_POST_IDS=frozenset(json.loads((ROOT/'content/news-policy.json').read_text(encoding='utf-8'))['excludedPostIds'])
SOURCE='https://raw.githubusercontent.com/welcomeourofhere/Shaver-Family/main/soyuz/public/data/news.json'
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('Unexpected feed redirect')
def read(url,limit):
    with build_opener(NoRedirect()).open(Request(url,headers={'User-Agent':'SOYUZ-PublicNews/1.0'}),timeout=30)as response:data=response.read(limit+1)
    if len(data)>limit:raise ValueError('Public feed resource exceeds size budget')
    return data
def sync(public_only=False):
    payload=json.loads(read(SOURCE,200000))
    if payload.get('version')!=1 or payload.get('groupId')!=-210007626 or payload.get('source')!='official-vk-api':raise ValueError('Unexpected public feed')
    items=payload.get('items')
    if not isinstance(items,list)or len(items)!=10 or len({item.get('id')for item in items})!=10:raise ValueError('Unexpected posts')
    if any(item['id']in EXCLUDED_POST_IDS for item in items):raise ValueError('Excluded post in public feed')
    media=[]
    for item in items:
        if not re.fullmatch(r'\d+',item['id'])or item.get('url')!=f'https://vk.ru/wall-210007626_{item["id"]}'or not isinstance(item.get('text'),str)or not item['text'].strip():raise ValueError('Unexpected public post')
        if item.get('image')is None:continue
        variants=item['image'].get('variants',[])
        if not 1<=len(variants)<=3:raise ValueError('Unexpected photo variants')
        previous=0
        for variant in variants:
            if not re.fullmatch(r'\.\./media/news/[\da-f-]+\.webp',variant.get('url',''))or not re.fullmatch(r'[a-f0-9]{64}',variant.get('sha256','')):raise ValueError('Unexpected photo path')
            if type(variant.get('width'))is not int or not previous<variant['width']<=1600:raise ValueError('Unexpected photo size')
            previous=variant['width']
            target=ROOT/'public/media/news'/Path(variant['url']).name
            data=target.read_bytes()if target.exists()else read(urljoin(SOURCE,variant['url']),5000000)
            if hashlib.sha256(data).hexdigest()!=variant['sha256']:raise ValueError('Photo integrity mismatch')
            with Image.open(BytesIO(data))as image:
                if image.size!=(variant['width'],variant.get('height'))or image.width*image.height>40000000:raise ValueError('Photo geometry mismatch')
            media.append((target,data))
    for target,data in media:
        if target.exists():continue
        target.parent.mkdir(parents=True,exist_ok=True);temporary=target.with_suffix('.webp.tmp');temporary.write_bytes(data);temporary.replace(target)
    text=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
    for path in [ROOT/'public/data/news.json']if public_only else[ROOT/'content/news.json',ROOT/'public/data/news.json']:
        path.parent.mkdir(parents=True,exist_ok=True);temporary=path.with_suffix('.json.tmp');temporary.write_text(text,encoding='utf-8');temporary.replace(path)
    print(f'Synced ten API posts and {len(media)} verified photo variants.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--public-only',action='store_true')
    try:sync(parser.parse_args().public_only)
    except Exception as error:raise SystemExit(f'Public snapshot sync failed ({type(error).__name__}); previous snapshot retained.')from None
