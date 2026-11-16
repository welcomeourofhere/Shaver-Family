"""Check the natural promo row and preserved desktop aside, without bookings."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/iteration66/hero-asides';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321');args=parser.parse_args()
rows=[];flows=[]
with sync_playwright()as p:
 browser=p.chromium.launch(channel='chrome')
 for theme in ['light','dark']:
  context=browser.new_context(viewport={'width':1207,'height':900},color_scheme=theme,reduced_motion='reduce');page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(180)
  cases=[(width,900,1)for width in [1440,1250,1207,1100,1000,961,960,900,801,800,700,620,390]]+[(width,500,1)for width in [1250,961,900]]+[(width,500,2)for width in [1250,1207,961,960,900,620,390]]
  for width,height,scale in cases:
   page.set_viewport_size({'width':width,'height':height})
   page.evaluate('''scale=>{const es=[...document.querySelectorAll('.hero-asides *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()));es.forEach(e=>e.style.removeProperty('font-size'));if(scale===2){const sizes=es.map(e=>parseFloat(getComputedStyle(e).fontSize)*2);es.forEach((e,i)=>e.style.fontSize=sizes[i]+'px')}}''',scale)
   page.wait_for_timeout(180)
   row=page.evaluate('''()=>{const box=s=>{const e=document.querySelector(s),b=e.getBoundingClientRect();return{x:b.x,y:b.y,w:b.width,h:b.height,scroll:e.scrollHeight,client:e.clientHeight}};return{scene:box('.hero-scene'),asides:box('.hero-asides'),first:box('.hero-asides .first-visit'),cash:box('.hero-asides .cashback'),minHeight:getComputedStyle(document.querySelector('.hero-asides')).minHeight,overflow:document.documentElement.scrollWidth>innerWidth+1,buttons:[...document.querySelectorAll('.hero-asides :is(a.btn,button.promo-code)')].map(e=>{const b=e.getBoundingClientRect(),s=getComputedStyle(e),ys=[];const walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);while(walker.nextNode()){const n=walker.currentNode;if(!n.textContent.trim()||!n.parentElement.checkVisibility())continue;const range=document.createRange();range.selectNode(n);for(const rect of range.getClientRects())if(rect.width)ys.push(Math.round(rect.y));}return{label:e.getAttribute('aria-label')||e.textContent.trim(),h:b.height,paddingLeft:parseFloat(s.paddingLeft),paddingRight:parseFloat(s.paddingRight),lines:new Set(ys).size,overflow:e.scrollWidth>e.clientWidth+1}})}}''')
   row.update(width=width,height=height,scale=scale,theme=theme);rows.append(row)
   assert not row['overflow'],row
   for b in row['buttons']:assert b['h']>=44 and b['paddingLeft']>=12 and b['paddingRight']>=12 and b['lines']<=1 and not b['overflow'],(row,b)
   assert row['first']['scroll']<=row['first']['client']+1,row
   assert page.locator('.cashback p').evaluate('e=>e.scrollWidth<=e.clientWidth+1'),'cashback text clipped at '+str((width,height,scale,theme))
   if width>960:
    assert row['asides']['x']>=row['scene']['x']+row['scene']['w']-1,row
    if scale==1:assert abs(row['asides']['h']-710)<1 and abs(row['first']['h']-386)<1 and abs(row['cash']['h']-300)<1,row
   else:
    assert row['minHeight']=='0px',row
    if width>=620:
     assert abs(row['first']['h']-row['cash']['h'])<1,row
     if scale==1 and width>=800:assert row['asides']['h']<=401,row
   if (width,scale)in [(900,1),(961,2),(960,2)]:page.locator('.hero-asides').screenshot(path=str(OUT/f'checked-{theme}-{width}-text{scale*100}.png'))
  page.evaluate("document.querySelectorAll('.hero-asides [style]').forEach(e=>e.style.removeProperty('font-size'))");page.set_viewport_size({'width':900,'height':700});page.locator('.cashback-link').click();page.wait_for_function("document.querySelector('#offer-cashback').dataset.offerActive==='true'")
  tip=page.locator('#offer-cashback [data-info-tip] button');tip.click();page.wait_for_timeout(120)
  flow=page.locator('#offer-cashback [data-info-tip]').evaluate("e=>({hash:location.hash,active:e.closest('[data-offer-id]').dataset.offerActive,open:e.querySelector('button').getAttribute('aria-expanded')})")
  assert flow['hash']=='#offer-cashback'and flow['active']=='true'and flow['open']=='true',flow
  page.keyboard.press('Escape');flows.append({'theme':theme,**flow,'pageerrors':errors});assert not errors,errors;context.close()
 browser.close()
(OUT/'verification.json').write_text(json.dumps({'cases':rows,'flows':flows},ensure_ascii=False,indent=2),encoding='utf8')
print(f'PASS {len(rows)} natural Hero promo cases, both themes, short heights/text200, one-line 44px controls, cashback and note flow')
