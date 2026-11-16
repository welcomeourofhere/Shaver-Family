"""Foreground pixels stay above cashback shade; old layer fixture reproduces the tint."""
import argparse,hashlib,io,json,re,traceback
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321/');parser.add_argument('--label',required=True);args=parser.parse_args()
assert re.fullmatch(r'[\w-]+',args.label)
host=urlsplit(args.origin).netloc;OUT=ROOT/'tmp/planning/iteration66/cashback'/args.label;OUT.mkdir(parents=True,exist_ok=False)
def hashes():return{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [*sorted((ROOT/'src').rglob('*')),ROOT/'public/reference/pioneer.webp']if p.is_file()}
report={'origin':args.origin,'sourceStart':hashes(),'cases':[],'pageErrors':[],
        'boundary':'Chrome local functional/raster check, not benchmark, provider or physical-device acceptance.'}
SAMPLE="""async()=>{
 const card=document.querySelector('.cashback'),surface=card.querySelector('.cashback-surface'),copy=card.querySelector('.cashback-copy'),art=card.querySelector('.cashback-illustration'),image=art.querySelector('img');await image.decode();
 const r=card.getBoundingClientRect(),ir=image.getBoundingClientRect(),s=getComputedStyle(surface),shade=getComputedStyle(surface,'::after'),cs=getComputedStyle(copy),before=getComputedStyle(copy,'::before');
 const excludes=[...copy.children].map(e=>e.getBoundingClientRect()),canvas=document.createElement('canvas');canvas.width=Math.ceil(ir.width);canvas.height=Math.ceil(ir.height);const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0,ir.width,ir.height);const points=[];
 for(let y=Math.ceil(Math.max(2,r.top+12));y<Math.min(innerHeight-2,r.bottom-12);y+=8)for(let x=Math.ceil(r.left+12);x<r.right-12;x+=8){
  if(x<ir.left+2||x>ir.right-2||y<ir.top+2||y>ir.bottom-2||excludes.some(b=>x>=b.left-3&&x<=b.right+3&&y>=b.top-3&&y<=b.bottom+3))continue;
  const ix=Math.round(x-ir.left),iy=Math.round(y-ir.top),px=ctx.getImageData(ix-1,iy-1,3,3).data;
  if([...Array(9)].some((_,i)=>px[i*4+3]<254))continue;
  const channels=[0,1,2].map(c=>[...Array(9)].map((_,i)=>px[i*4+c]));if(channels.some(c=>Math.max(...c)-Math.min(...c)>18))continue;
  points.push({x,y,rgb:channels.map(c=>c.reduce((a,b)=>a+b,0)/9)});
 }
 const stride=Math.max(1,Math.floor(points.length/120));return{card:r.toJSON(),image:ir.toJSON(),clip:getComputedStyle(card).clipPath,surfaceZ:s.zIndex,artZ:getComputedStyle(art).zIndex,copyZ:cs.zIndex,shade:{content:shade.content,background:shade.backgroundImage,z:shade.zIndex},copyBefore:before.content,src:image.currentSrc,points:points.filter((_,i)=>i%stride===0).slice(0,120)};
}"""
LEGACY='.cashback-surface{z-index:auto}.cashback-surface::after{content:none}.cashback-copy::before{content:"";position:absolute;z-index:-1;inset:0;border-radius:inherit;background:var(--cashback-text-shade)}'
def pixels(page,points):
 image=Image.open(io.BytesIO(page.screenshot())).convert('RGB');deltas=[]
 for p in points:
  values=[image.getpixel((p['x']+dx,p['y']+dy))for dx in [-1,0,1]for dy in [-1,0,1]]
  actual=[sum(v[c]for v in values)/9 for c in [0,1,2]];deltas.append(max(abs(actual[c]-p['rgb'][c])for c in [0,1,2]))
 return{'count':len(deltas),'within18':sum(d<=18 for d in deltas),'above20':sum(d>20 for d in deltas),'median':sorted(deltas)[len(deltas)//2]if deltas else None,'max':max(deltas,default=0)}
with sync_playwright()as p:
 browser=p.chromium.launch(channel='chrome',args=['--mute-audio'])
 for width in [390,620,800,801,960,961,1100,1440]:
  for theme in ['light','dark']:
   context=browser.new_context(viewport={'width':width,'height':1000},color_scheme=theme,reduced_motion='reduce')
   context.route('**/*',lambda r:r.continue_()if urlsplit(r.request.url).netloc==host else r.abort())
   context.add_init_script('if(top===window){localStorage.setItem("soyuz_theme",'+json.dumps(theme)+');localStorage.setItem("soyuz_feedback_enabled","false")}')
   page=context.new_page();page.on('pageerror',lambda e:report['pageErrors'].append(str(e)));row={'width':width,'theme':theme}
   try:
    page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(180)
    page.locator('.cashback').evaluate('e=>scrollTo({top:scrollY+e.getBoundingClientRect().top-(innerHeight-e.offsetHeight)/2,behavior:"instant"})');page.wait_for_timeout(80)
    data=page.evaluate(SAMPLE);points=data.pop('points');row['state']=data
    assert [data['surfaceZ'],data['artZ'],data['copyZ']]==['0','1','2'],data
    assert data['copyBefore']=='none'and data['shade']['content']=='""'and'linear-gradient'in data['shade']['background'],data
    assert data['image']['top']<data['card']['top']and data['image']['height']>data['card']['height'],data
    result=pixels(page,points);row['foregroundPixels']=result
    assert result['count']>=12 and result['within18']/result['count']>=.9,result
    if width==961 and theme=='light':
     legacy=page.add_style_tag(content=LEGACY);old=page.evaluate(SAMPLE);old.pop('points');bad=pixels(page,points);row['legacyPixels']=bad
     for selector in ['card','image']:
      for key in ['x','y','width','height']:assert abs(data[selector][key]-old[selector][key])<.1,(selector,key,data,old)
     assert data['clip']==old['clip']
     assert bad['above20']>=5 and bad['above20']>result['above20'],(bad,result)
     page.screenshot(path=str(OUT/'961-light-legacy.png'));legacy.evaluate('e=>e.remove()')
    top=max(0,data['image']['top']-4);bottom=min(1000,data['card']['bottom']+4)
    page.screenshot(path=str(OUT/f'{width}-{theme}.png'),clip={'x':max(0,data['card']['x']),'y':top,'width':min(width,data['card']['right'])-max(0,data['card']['x']),'height':bottom-top})
    row['pass']=True
   except Exception:row.update(pass_=False,failure=traceback.format_exc());page.screenshot(path=str(OUT/f'failure-{width}-{theme}.png'))
   finally:report['cases'].append(row);context.close()
 browser.close()
report['sourceEnd']=hashes();report['unchanged']=report['sourceStart']==report['sourceEnd'];report['passed']=sum(r.get('pass',False)for r in report['cases']);report['failed']=16-report['passed']
(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'passed':report['passed'],'failed':report['failed'],'pageErrors':report['pageErrors'],'unchanged':report['unchanged'],'results':str(OUT/'results.json')}));assert report['failed']==0 and report['pageErrors']==[]and report['unchanged']
