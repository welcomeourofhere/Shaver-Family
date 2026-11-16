"""Reach every menu link at 200% text on short desktop/compact viewports."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4339/');parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');args=parser.parse_args()
OUT=ROOT/'tmp/planning/iteration65/menu-short-height';OUT.mkdir(parents=True,exist_ok=True)
rows=[];errors=[]
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 for width,height in [(320,320),(600,320),(1024,480),(1440,600)]:
  for theme in ['light','dark']:
   context=browser.new_context(viewport={'width':width,'height':height},color_scheme=theme,reduced_motion='reduce');page=context.new_page();page.on('pageerror',lambda e:errors.append(e.stack));page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_function("document.querySelector('#mobile-menu')?.dataset.dockOwned==='true'")
   page.evaluate("""()=>{const es=[...document.querySelectorAll('body *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())),sizes=es.map(e=>parseFloat(getComputedStyle(e).fontSize));es.forEach((e,i)=>e.style.fontSize=sizes[i]*2+'px')}""")
   page.wait_for_timeout(150)
   compact=page.evaluate("matchMedia('(max-width:960px)').matches")
   if compact:
    page.locator('[data-open-menu]').click();page.locator('#mobile-menu').wait_for(state='visible');port=page.locator('.dock-content .surface-content');window=page.locator('#mobile-menu');last=page.locator('.menu-contact-row>a')
   else:
    page.locator('.more-menu>summary').hover();page.wait_for_timeout(100);port=page.locator('.more-panel .surface-content');window=page.locator('.more-panel');last=page.locator('.more-panel a[href="#contacts"]')
   box=port.bounding_box();frame=window.bounding_box()
   assert box['y']>=0 and box['y']+box['height']<=height+1,(width,height,box)
   initial_frame=frame
   resized_height=None
   if width==1440:
    resized_height=480;page.set_viewport_size({'width':width,'height':resized_height});page.wait_for_timeout(150)
    box=port.bounding_box();frame=window.bounding_box()
    assert box['y']+box['height']<=resized_height-15,(box,resized_height)
   if not compact:assert abs(frame['x']+frame['width']-(box['x']+box['width']))<1,(frame,box)
   assert port.evaluate('e=>e.scrollHeight>e.clientHeight+1'),(width,height,'short scenario does not exercise internal scrolling')
   before=port.evaluate('e=>e.scrollTop');page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);page.mouse.wheel(0,150);page.wait_for_timeout(400);after=port.evaluate('e=>e.scrollTop');assert after>before,(width,height,before,after)
   last.focus();page.wait_for_timeout(100);link=last.bounding_box();assert link['y']>=box['y']-1 and link['y']+link['height']<=box['y']+box['height']+1,(box,link)
   assert last.evaluate("""e=>{const s=getComputedStyle(e),r=document.createRange();r.selectNodeContents(e);return r.getBoundingClientRect().width<=e.clientWidth-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight)+1}"""),'scrollbar clipped the last label'
   page.screenshot(path=str(OUT/f'{args.engine}-{width}x{height}-{theme}.png'))
   page.keyboard.press('Enter');page.wait_for_timeout(250);assert page.evaluate('location.hash')=='#contacts';assert not window.is_visible()
   rows.append({'width':width,'height':height,'resizedHeight':resized_height,'initialPanel':initial_frame,'theme':theme,'textScale':2,'compact':compact,'scrollport':box,'wheel':[before,after],'lastLink':link,'keyboardRoute':'#contacts'});context.close()
 browser.close()
assert not errors,errors
(OUT/f'{args.engine}.json').write_text(json.dumps({'origin':args.origin,'engine':args.engine,'cases':rows,'errors':errors,'published':False,'physicalDevice':False},ensure_ascii=False,indent=2),encoding='utf8')
print('PASS',args.engine,len(rows),'short-height menu cases, text200, native wheel, right edge, keyboard last link')
