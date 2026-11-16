"""Restore only the approved public asset graph from its pinned, public release."""
import argparse,gzip,hashlib,json
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
PREFIX='https://storage.yandexcloud.net/shaver/Soyuz/releases/'

def sha(body):return hashlib.sha256(body).hexdigest()
def target_for(root,path):
 target=(root/path).resolve()
 if not target.is_relative_to(root.resolve())or target==root.resolve():raise ValueError('Asset path escapes public directory')
 return target
def decode_source(row,body,urls):
 if not row['url'].startswith(PREFIX)or sha(body)!=row['sha256']:raise ValueError('Untrusted asset URL or transfer hash')
 body=gzip.decompress(body)if row['contentEncoding']=='gzip'else body
 if sha(body)!=row['contentSha256']:raise ValueError('Decoded asset hash mismatch')
 if sha(body)!=row['sourceSha256']:
  text=body.decode('utf-8')
  for url,path in urls.items():text=text.replace(url,'/'+path)
  body=text.encode('utf-8')
 if sha(body)!=row['sourceSha256']:raise ValueError('Source asset hash mismatch: '+row['sourcePath'])
 return body
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',type=Path,default=ROOT/'public');args=parser.parse_args()
 lock=json.loads((ROOT/'deploy/media-lock.json').read_text(encoding='utf-8'));rows=lock['files'];urls={r['url']:r['sourcePath']for r in rows};restored=0
 for row in rows:
  target=target_for(args.destination,row['sourcePath'])
  if target.exists():
   if sha(target.read_bytes())!=row['sourceSha256']:raise ValueError('Existing source differs; refusing to overwrite: '+row['sourcePath'])
   continue
  if not row['url'].startswith(PREFIX):raise ValueError('Untrusted asset URL')
  with urlopen(Request(row['url'],headers={'Accept-Encoding':'identity'}),timeout=60)as response:body=response.read()
  source=decode_source(row,body,urls);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source);restored+=1
 print('PASS',len(rows),'pinned public assets;',restored,'restored')
if __name__=='__main__':main()
