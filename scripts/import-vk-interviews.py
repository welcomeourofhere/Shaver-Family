"""Import the owner's four public VK articles from archived DOM; preserve every carousel frame."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from PIL import Image, ImageOps, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'tmp/planning/iteration62/interviews-staged'
PEOPLE={
 'milena-malyshevskaya':('souz-milena','Милена Малышевская','Интервью с Миленой Малышевской, барбером СОЮЗа в Кирове. О танцах, переездах, обучении мужским стрижкам и работе с гостями.'),
 'sonya-kid':('souz-sonya-kid','Соня Кид','Интервью с Соней Кид, барбером СОЮЗа в Кирове. О музыке, танцах, работе на мероприятиях и пути от администратора к мужским стрижкам.'),
 'svetlana-demina':('souz-svetlana','Светлана Дёмина','Интервью со Светланой Дёминой, барбером СОЮЗа в Кирове. О биологии, смене профессии, первых стрижках и жизни вне работы.'),
 'lyubov-shklyaeva':('souz-lyubov','Любовь Шкляева','Интервью с Любовью Шкляевой, барбером СОЮЗа в Кирове. Об обучении, удлинённых мужских стрижках, укладке и профессиональном конгрессе.'),
}
spec=importlib.util.spec_from_file_location('article_images',ROOT/'scripts/prepare-master-article-images.py');exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
digest=lambda data:hashlib.sha256(data).hexdigest()
def save(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def public_image(url):
 p=urlparse(url)
 return p.scheme=='https' and not p.username and not p.password and p.port is None and (p.hostname or'').endswith(('.vkuserphoto.ru','.userapi.com'))
class ImageRedirect(HTTPRedirectHandler):
 def redirect_request(self,request,fp,code,msg,headers,newurl):
  if not public_image(newurl):raise ValueError('Unexpected image redirect')
  return super().redirect_request(request,fp,code,msg,headers,newurl)

def download(job):
 slug,item,old=job;folder=ROOT/'artifacts/master-articles'/slug/'originals';folder.mkdir(exist_ok=True)
 checkpoint=folder/(item['id']+'.source.json')
 previous=old.get(item['id'])or(json.loads(checkpoint.read_text(encoding='utf-8'))if checkpoint.exists()else None)
 if previous and previous.get('url')==item['url']:
  path=ROOT/previous['source']
  if path.is_file()and digest(path.read_bytes())==previous['sha256']:return {**item,**{k:previous[k]for k in ['source','sha256','width','height','bytes']}}
 if not public_image(item['url']):raise ValueError('Unexpected image host')
 for attempt in range(3):
  try:
   with build_opener(ImageRedirect()).open(Request(item['url'],headers={'User-Agent':'Mozilla/5.0','Referer':'https://vk.ru/'}),timeout=30)as response:data=response.read(12_000_001)
   break
  except HTTPError:raise
  except URLError as error:
   if attempt==2:raise RuntimeError(f"Cannot load {slug}/{item['id']} from {urlparse(item['url']).hostname}")from error
   time.sleep((attempt+1)*.5)
 if len(data)>12_000_000:raise ValueError('Photograph exceeds size budget')
 with Image.open(BytesIO(data))as photo:
  if photo.width*photo.height>40_000_000:raise ValueError('Photograph exceeds pixel budget')
  width,height=photo.size;extension={'JPEG':'jpg','PNG':'png','WEBP':'webp'}.get(photo.format)
  if (width,height)!=(item['declaredWidth'],item['declaredHeight']):raise ValueError('Largest public photograph returned different dimensions')
  if not extension:raise ValueError('Unexpected photograph format')
  photo.verify()
 path=folder/(item['id']+'.'+extension)
 if path.exists()and digest(path.read_bytes())!=digest(data):path=folder/(item['id']+'-'+digest(data)+'.'+extension)
 path.write_bytes(data)
 result={**item,'source':path.relative_to(ROOT).as_posix(),'sha256':digest(data),'width':width,'height':height,'bytes':len(data)}
 save(checkpoint,result);return result

def prepare(slug):
 folder=ROOT/'artifacts/master-articles'/slug;raw=(folder/'source-dom.json').read_bytes();dom=json.loads(raw.decode('utf-8-sig'));master_id,name,description=PEOPLE[slug]
 team=json.loads((ROOT/'content/team.json').read_text(encoding='utf-8'))['masters'];assert any(m['id']==master_id for m in team)
 assert 'vk.ru/'in dom['url'] and name.split()[0]in dom['title'] and re.search(r'id="article_view_-210007626_\d+"',dom['html'])
 source_lines=[];line_at={};figure_photos={};jobs=[];source_blocks=[]
 alt_file=folder/'alt-texts.json';alt_texts=json.loads(alt_file.read_text(encoding='utf-8'))if alt_file.exists()else{}
 for block in dom['blocks']:
  text=block.get('text','').strip()
  if block['tag']=='FIGURE':
   counter=re.match(r'^\d+\s+из\s+(\d+)(?:\s*\n)?',text);caption=text[counter.end():].strip()if counter else text
   sizes=[photo for host in block['photoSources']for photo in host['sizes']]
   assert sizes and (not counter or int(counter[1])==len(sizes)),(slug,block['index'])
   ids=[]
   for number,sizes_for_photo in enumerate(sizes,1):
    candidates=[value for value in sizes_for_photo.values()if isinstance(value,list)and len(value)>=3 and isinstance(value[0],str)and public_image(value[0])and isinstance(value[1],(int,float))and isinstance(value[2],(int,float))]
    assert candidates,(slug,block['index'],number)
    url,width,height=max(candidates,key=lambda v:v[1]*v[2])[:3];photo_id=f'photo-{len(jobs)+1:02}';ids.append(photo_id)
    alt=(caption+' — 'if caption else'Фотография к интервью — ')+name+(f', кадр {number} из {len(sizes)}'if len(sizes)>1 else'')
    jobs.append({'id':photo_id,'url':url,'declaredWidth':width,'declaredHeight':height,'sourceBlock':block['index'],'sourceImage':number,'alt':alt_texts.get(photo_id,alt)})
   figure_photos[block['index']]={'kind':'photos','images':ids,'caption':caption}
   text=caption
  if text:
   line_at[block['index']]=len(source_lines)+1;source_lines.extend(text.splitlines());source_lines.append('')
  source_blocks.append({'index':block['index'],'tag':block['tag'],'text':text})
 source_text='\n'.join(source_lines).rstrip()+'\n';(folder/'source.txt').write_text(source_text,encoding='utf-8',newline='\n')
 old_path=folder/'media-sources.json';old={item['id']:item for item in json.loads(old_path.read_text(encoding='utf-8'))['images']}if old_path.exists()else{}
 with ThreadPoolExecutor(max_workers=4)as pool:photos=list(pool.map(download,[(slug,item,old)for item in jobs]))
 sources={'source':dom['url'],'capturedAt':dom['capturedAt'],'domSha256':digest(raw),'images':photos};save(old_path,sources)
 cover_block=next(block for block in dom['blocks']if block['tag']=='FIGURE');cover_info=figure_photos[cover_block['index']]
 assert len(cover_info['images'])==1
 blocks=[];lead=[];closing={'title':'','paragraphs':[]};current=None;question_count=0;all_blocks=dom['blocks']
 last_heading=max(block['index']for block in all_blocks if block['tag']in ['H2','H3'])
 for i,block in enumerate(all_blocks):
  text=block.get('text','').strip();tag=block['tag'];next_tag=all_blocks[i+1]['tag']if i+1<len(all_blocks)else''
  if tag=='H1'or not text and tag!='FIGURE':continue
  if tag=='FIGURE':
   current=None
   if block['index']!=cover_block['index']:blocks.append(figure_photos[block['index']])
   continue
  if block['index']<cover_block['index']:
   assert tag=='P';lead.append(text);continue
  if block['index']==last_heading and next_tag!='BLOCKQUOTE':closing['title']=text;current=None;continue
  if tag in ['H2','H3','P']and next_tag=='BLOCKQUOTE':
   question_count+=1;current={'kind':'qa','id':f'q{question_count:02}','question':text,'paragraphs':[],'sourceLine':line_at[block['index']]};blocks.append(current)
  elif tag=='BLOCKQUOTE':
   if current is not None:current['paragraphs'].append(text)
   else:blocks.append({'kind':'text','paragraphs':[text],'quoted':True,'sourceLine':line_at[block['index']]})
  elif block['index']>last_heading:
   assert tag=='P';closing['paragraphs'].append(text)
  else:
   current=None;blocks.append({'kind':'text','paragraphs':[text],'heading':tag in ['H2','H3'],'sourceLine':line_at[block['index']]})
 article={'schemaVersion':1,'slug':slug,'masterId':master_id,'title':dom['title'],'description':description,'cover':cover_info['images'][0],'source':{'kind':'owner-linked-vk-article','url':dom['url'],'capturedAt':dom['capturedAt'],'file':(folder/'source.txt').relative_to(ROOT).as_posix(),'sha256':digest(source_text.encode())},'sections':[{'id':'interview','title':'','blocks':blocks}],'closing':closing}
 if lead:article['lead']=lead
 if cover_info['caption']:article['coverCaption']=cover_info['caption']
 emitted=[article['title'],*lead,article.get('coverCaption','')]
 for block in blocks:emitted.extend(([block['question'],*block['paragraphs']]if block['kind']=='qa'else[block['caption']]if block['kind']=='photos'else block['paragraphs']))
 emitted.extend([closing['title'],*closing['paragraphs']])
 normalize=lambda s:' '.join(s.split())
 assert [normalize(t)for t in emitted if t]==[normalize(b['text'])for b in source_blocks if b['text']],slug+' text/order changed'
 save(folder/'article-candidate.json',article);save(STAGE/'content/master-articles'/(slug+'.json'),article)
 exporter.export_article(slug,article,sources,STAGE)
 # Inspection sheet only; originals and runtime photographs are unchanged.
 sheet=Image.new('RGB',(1000,230*((len(photos)+4)//5)),(245,240,230));draw=ImageDraw.Draw(sheet)
 for index,item in enumerate(photos):
  with Image.open(ROOT/item['source'])as opened:
   thumb=ImageOps.exif_transpose(opened).convert('RGB');thumb.thumbnail((190,200))
  x=index%5*200;y=index//5*230;sheet.paste(thumb,(x+(190-thumb.width)//2,y));draw.text((x+5,y+205),item['id'],fill='black')
 sheet.save(folder/'inspection-sheet.jpg',quality=90)
 report={'slug':slug,'masterId':master_id,'questions':question_count,'photos':len(photos),'sourceBlocks':len(source_blocks),'sourceTextSha256':article['source']['sha256'],'domSha256':digest(raw),'textAndOrderVerified':True,'carousels':[{'sourceBlock':b['index'],'count':len(figure_photos[b['index']]['images'])}for b in all_blocks if b['tag']=='FIGURE'and len(figure_photos[b['index']]['images'])>1]}
 save(folder/'import-verification.json',report);print(json.dumps(report,ensure_ascii=False),flush=True)
 return report

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--install',action='store_true');args=parser.parse_args()
 reports=[prepare(slug)for slug in PEOPLE]
 if args.install:
  for slug in PEOPLE:
   shutil.copytree(STAGE/'public/media/articles'/slug,ROOT/'public/media/articles'/slug,dirs_exist_ok=True)
   # The media catalogue exists before the article enters the live Astro glob.
   for suffix in ['.media.json','.json']:
    path=ROOT/'content/master-articles'/(slug+suffix);temporary=path.with_suffix(path.suffix+'.tmp');shutil.copyfile(STAGE/'content/master-articles'/(slug+suffix),temporary);temporary.replace(path)
 save(ROOT/'artifacts/master-articles/vk-import-2026-11-15.json',{'capturedBy':'public DOM in agent-browser','importedAt':datetime.now(timezone.utc).isoformat(),'articles':reports,'installed':args.install,'websitePublished':False})

if __name__=='__main__':main()
