"""Create an immutable local native-wrapper fixture from one exact release package."""
import argparse,gzip,hashlib,json
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('manifest',type=Path);parser.add_argument('destination',type=Path);args=parser.parse_args()
 dest=args.destination.resolve();assert dest.is_relative_to((ROOT/'tmp').resolve())and not dest.exists(),'Use a new folder under workspace/tmp'
 manifest=json.loads(args.manifest.read_text(encoding='utf-8'));folder=args.manifest.parent
 rows=manifest['files'];paths={r['url']:r.get('sourcePath',r['file'].split('/public-assets/',1)[1])for r in rows}
 def local(text):
  for url,path in paths.items():text=text.replace(url,'/'+path)
  return text
 for row in rows:
  data=(ROOT/row['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256']
  data=gzip.decompress(data)if row['contentEncoding']=='gzip'else data
  if Path(paths[row['url']]).suffix.lower()in ['.css','.js','.mjs','.json','.svg','.txt','.xml']:data=local(data.decode('utf-8')).encode('utf-8')
  target=dest/paths[row['url']];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 native=lambda content:'<div class="r t-rec"><div class="t123"><div class="t-container_100"><div class="t-width t-width_100">'+content+'</div></div></div></div>'
 shared={k:local((folder/v['codeFile']).read_text(encoding='utf-8'))for k,v in manifest.get('shared',{}).items()}
 for row in manifest['pages']:
  head=local((folder/row['headFile']).read_text(encoding='utf-8'));body=local((folder/row['codeFile']).read_text(encoding='utf-8'))
  if shared:body='<div id="t-header" class="t-records">'+native(shared['header'])+'</div>'+native(body)+'<div id="t-footer" class="t-records">'+native(shared['footer'])+'</div>'
  else:body=native(body)
  target=dest/('index.html'if row['route']=='/'else'404.html'if row['route']=='/404'else row['route'].strip('/')+'/index.html');target.parent.mkdir(parents=True,exist_ok=True)
  title=BeautifulSoup('', 'html.parser').new_tag('title');title.string=row['title']
  target.write_text('<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'+str(title)+head+'</head><body><div id="allrecords">'+body+'</div></body></html>',encoding='utf-8')
 (dest.parent/'source.json').write_text(json.dumps({'build':manifest['build'],'manifest':str(args.manifest),'nativeWrappers':True,'tildaThirdPartyScripts':False},indent=2),encoding='utf-8')
 print('PASS native fixture',manifest['build'],len(rows),'assets',len(manifest['pages']),'pages')
if __name__=='__main__':main()
