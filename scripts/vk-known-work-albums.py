"""Read six verified work albums by IDs returned on public SOYUZ photos."""
import importlib.util
import json
import os
from pathlib import Path

spec=importlib.util.spec_from_file_location('work_albums',Path(__file__).with_name('vk-work-albums.py'))
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
# Each link is confirmed by a public photo's album_id, staff hashtag and post text.
ALBUMS=[
 {'id':313537350,'masterId':'souz-svetlana','postId':1948,'photoId':457241914},
 {'id':312750596,'masterId':'souz-sonya-kid','postId':1735,'photoId':457241641},
 {'id':311695116,'masterId':'souz-milena','postId':1548,'photoId':457241434},
 {'id':311570476,'masterId':'souz-darya','postId':1498,'photoId':457241378},
 {'id':312351342,'masterId':'souz-sofya-shalaginova','postId':1606,'photoId':457241479},
 {'id':297253623,'masterId':'souz-lyubov','postId':1898,'photoId':457241782},
]

def collect(token):
 albums=[]
 for evidence in ALBUMS:
  album_id=evidence['id']
  photos=api.normalize_photos(api.read_pages(token,'photos.get',{'album_id':album_id,'photo_sizes':1,'extended':0}),album_id)
  albums.append({**evidence,'ownerId':api.OWNER_ID,'photos':photos})
 return {'source':'official-vk-api-known-albums','ownerId':api.OWNER_ID,'albums':albums}

def main():
 token=os.environ.get('VK_TOKEN')
 try:
  if not token:raise api.ReadError('missing_token')
  snapshot=collect(token)
  api.save_snapshot(snapshot,Path('artifacts/vk-known-work-albums.json'),token)
  print('SOYUZ_KNOWN_ALBUMS_RESULT='+json.dumps({'albums':len(snapshot['albums']),'photos':sum(len(a['photos'])for a in snapshot['albums'])}))
  return 0
 except Exception as error:
  safe={'category':error.category if isinstance(error,api.ReadError)else'internal_error'}
  if isinstance(error,api.ReadError)and error.code is not None:safe['code']=error.code
  path=Path('artifacts/vk-known-work-albums.error.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(safe)+'\n',encoding='utf-8')
  print('SOYUZ_KNOWN_ALBUMS_ERROR='+json.dumps(safe))
  return 1

if __name__=='__main__':raise SystemExit(main())
