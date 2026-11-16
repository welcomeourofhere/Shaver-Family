"""Desktop certificate placement is mirrored; artwork and compact order are not."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--origin',default='http://127.0.0.1:4321');parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');args=parser.parse_args();OUT=ROOT/'tmp/planning/iteration65/certificate-mirror';OUT.mkdir(parents=True,exist_ok=True);rows=[]
with sync_playwright() as p:
 b=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 for width,height in [(961,600),(1024,720),(1280,720),(1440,900),(1920,1080),(390,844),(960,720)]:
  for theme in ['light','dark']:
   for scale in [1,2]:
    c=b.new_context(viewport={'width':width,'height':height},color_scheme=theme,reduced_motion='no-preference');c.add_init_script('localStorage.setItem("soyuz_theme",'+json.dumps(theme)+')');page=c.new_page();page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(200)
    if scale==2:page.evaluate('''()=>{const es=[...document.querySelectorAll('body *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()));const ss=es.map(e=>parseFloat(getComputedStyle(e).fontSize));es.forEach((e,i)=>e.style.fontSize=ss[i]*2+'px')}''')
    page.locator('.certificate-scene').evaluate('e=>scrollTo({top:e.getBoundingClientRect().top+scrollY-210,behavior:"instant"})');page.wait_for_timeout(150);cards=page.locator('[data-certificate]');compact=page.evaluate("matchMedia('(max-width:960px)').matches")
    lefts=cards.evaluate_all('es=>es.map(e=>e.getBoundingClientRect().left)');assert (all(lefts[i]>lefts[i+1]for i in range(3))if not compact else all(lefts[i]<lefts[i+1]for i in range(3))),(width,theme,scale,lefts)
    for index in [0,1,2,3,2,1,0]:
     card=cards.nth(index);point=card.evaluate('''e=>{const r=e.getBoundingClientRect();for(const x of [r.left+4,r.right-4,r.left+r.width/2])for(const y of [r.top+Math.min(r.height*.5,50),r.bottom-4])if(document.elementFromPoint(x,y)?.closest('[data-certificate]')===e)return{x,y};return null}''');assert point,(width,theme,scale,index,'no exposed hit area');page.mouse.move(point['x'],point['y']);page.wait_for_function('(i)=>document.querySelectorAll("[data-certificate]")[i].getAttribute("aria-pressed")==="true"',arg=index);page.wait_for_timeout(350)
     m=page.locator('#certificates').evaluate('''e=>{const r=e.getBoundingClientRect(),p=document.querySelector('.gifts-placeholder').getBoundingClientRect(),arts=[...e.querySelectorAll('.certificate-art')];return{card:r.toJSON(),placeholder:p.toJSON(),arts:arts.map(x=>({rect:x.getBoundingClientRect().toJSON(),m11:new DOMMatrix(getComputedStyle(x).transform).m11,m22:new DOMMatrix(getComputedStyle(x).transform).m22})),title:e.querySelector('.certificate-copy').getBoundingClientRect().toJSON(),buy:e.querySelector('.certificate-buy').getBoundingClientRect().toJSON()}}''')
     assert all(a['m11']>0 and a['m22']>0 for a in m['arts']),(width,theme,scale,index,'reflected artwork',m)
     if not compact:assert min(a['rect']['left']for a in m['arts'])>=m['placeholder']['right']+4,(width,theme,scale,index,'art touches left gift text',m)
     assert max(a['rect']['bottom']for a in m['arts'])<=m['title']['top']+1,(width,theme,scale,index,'art overlaps certificate title',m)
     assert m['buy']['bottom']<=m['card']['bottom']-20,(width,theme,scale,index,'buy escaped card',m)
    page.screenshot(path=str(OUT/f'{args.engine}-{width}x{height}-{theme}-{scale}x.png'));rows.append({'width':width,'height':height,'theme':theme,'textScale':scale,'compact':compact,'buttonLefts':lefts,'lastGeometry':m});c.close()
 b.close()
(OUT/f'{args.engine}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS',args.engine,len(rows),'desktop/compact certificate layouts, seven hover selections each, both themes and normal/200% text')
