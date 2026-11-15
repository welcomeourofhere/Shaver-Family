"""Public SOYUZ wall/photo reads, using the same server-side API boundary as SF."""
from datetime import datetime
import json
from urllib.parse import urlencode
from urllib.request import Request,build_opener,HTTPRedirectHandler

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ValueError('Unexpected VK API redirect')

def fetch_posts(token,group_id,timezone,public_image):
    request=Request('https://api.vk.com/method/wall.get',data=urlencode({'access_token':token,'v':'5.199','owner_id':-group_id,'count':100,'filter':'owner'}).encode('ascii'),headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'SOYUZ-PublicNews/1.0'})
    with build_opener(NoRedirect()).open(request,timeout=20)as response:
        raw=response.read(4_000_001)
    if len(raw)>4_000_000:raise ValueError('VK response exceeds size budget')
    payload=json.loads(raw)
    if payload.get('error'):raise ValueError('VK API declined the public wall read')
    return normalize_posts(payload.get('response',{}).get('items',[]),group_id,timezone,public_image)

def normalize_posts(posts,group_id,timezone,public_image):
    if not isinstance(posts,list):raise ValueError('Unexpected VK posts shape')
    result=[]
    for post in posts:
        if not isinstance(post,dict)or post.get('owner_id')!=-group_id or not isinstance(post.get('text'),str)or not post['text'].strip():continue
        if type(post.get('id'))is not int or post['id']<1 or type(post.get('date'))is not int:continue
        attachments=post.get('attachments',[])
        if not isinstance(attachments,list):attachments=[]
        photos=[a['photo']for a in attachments if isinstance(a,dict)and a.get('type')=='photo'and isinstance(a.get('photo'),dict)]
        available=photos[0].get('sizes',[])if photos else[]
        if not isinstance(available,list):available=[]
        sizes=[s for s in available if isinstance(s,dict)and public_image(s.get('url'))and type(s.get('width'))is int and 0<s['width']<=40000]
        largest=max(sizes,key=lambda s:s['width'],default=None)
        result.append({'id':str(post['id']),'publishedAt':datetime.fromtimestamp(post['date'],timezone).isoformat(),'text':post['text'].strip(),'url':f'https://vk.ru/wall-{group_id}_{post["id"]}','photo':largest['url']if largest else None,'photoSource':'api'})
    return result
