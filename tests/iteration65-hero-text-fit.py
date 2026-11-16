"""Keep the normal Hero geometry, but allow genuinely enlarged text to grow."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--origin',default='http://127.0.0.1:4321');parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');args=parser.parse_args();OUT=ROOT/'tmp/planning/iteration65/hero-text-fit';OUT.mkdir(parents=True,exist_ok=True);rows=[]
legacy='@media(min-width:961px){.hero-asides{height:var(--hero-asides-height);min-height:0;grid-template-rows:minmax(0,1fr) var(--cashback-height)}.first-visit,.cashback,.cashback-copy{min-height:0}.hero-news-details p{height:calc(var(--hero-news-text-size)*1.5*var(--hero-news-lines))}}'
with sync_playwright()as p:
 b=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 for w,h in [(961,600),(1024,720),(1280,720),(1440,900),(1920,1080)]:
  for theme in ['light','dark']:
   c=b.new_context(viewport={'width':w,'height':h},color_scheme=theme,reduced_motion='reduce');c.add_init_script('localStorage.setItem("soyuz_theme",'+json.dumps(theme)+')');page=c.new_page();page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(300)
   get='''()=>Object.fromEntries(['.hero-scene','.hero-asides','.first-visit','.cashback'].map(s=>{const r=document.querySelector(s).getBoundingClientRect();return[s,{height:r.height,top:r.top}]}))''';old=page.add_style_tag(content=legacy);before=page.evaluate(get);old.evaluate('(e)=>e.remove()');after=page.evaluate(get);assert all(abs(before[s][k]-after[s][k])<1 for s in before for k in before[s]),(w,theme,before,after)
   page.evaluate('''()=>{const es=[...document.querySelectorAll('body *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()));const ss=es.map(e=>parseFloat(getComputedStyle(e).fontSize));es.forEach((e,i)=>e.style.fontSize=ss[i]*2+'px')}''');page.wait_for_timeout(150)
   data=page.evaluate('''()=>[...document.querySelectorAll('.first-visit,.cashback')].map(e=>{const r=e.getBoundingClientRect(),copy=e.querySelector('p').getBoundingClientRect(),actions=(e.querySelector('.first-actions')||e.querySelector('.cashback-link')).getBoundingClientRect();return{card:r.toJSON(),copy:copy.toJSON(),actions:actions.toJSON()}})''');assert all(d['actions']['bottom']<=d['card']['bottom']-19 and d['copy']['bottom']<=d['actions']['top']+1 for d in data),(w,theme,data)
   assert (data[1]['card']['left']>=data[0]['card']['right']+23 if abs(data[1]['card']['left']-data[0]['card']['left'])>1 else data[1]['card']['top']>=data[0]['card']['bottom']+23),(w,theme,data)
   for selector,label in [('.first-actions','first-actions'),('.cashback-link','cashback-action')]:page.locator(selector).evaluate('e=>scrollTo({top:e.getBoundingClientRect().bottom+scrollY-innerHeight+100,behavior:"instant"})');page.wait_for_timeout(80);page.screenshot(path=str(OUT/f'{args.engine}-{w}x{h}-{theme}-{label}.png'))
   rows.append({'width':w,'height':h,'theme':theme,'normalGeometryPreserved':True,'enlargedCards':data});c.close()
 b.close()
(OUT/f'{args.engine}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS',args.engine,len(rows),'normal A/B +200% Hero promo/cashback, CTA inside surface with readable text, gap24 preserved')
