"""One-line hours message, intrinsic width, narrow-screen/text enlargement fallback."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321/');parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');args=parser.parse_args()
OUT=ROOT/'tmp/planning/iteration65/business-hours';OUT.mkdir(parents=True,exist_ok=True)
rows=[];errors=[]
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 for width in [320,390,768,1024,1440]:
  for theme in ['light','dark']:
   for scale in [1,2]:
    time,state,heading,detail,color={390:('08:00','open','Сейчас открыто','До закрытия 11 ч','--status-open'),768:('17:33','closing','Сейчас открыто','До закрытия 1 ч 27 мин','--yellow')}.get(width,('00:33','closed','Сейчас закрыто','Откроемся через 7 ч 27 мин','--red'))
    context=browser.new_context(viewport={'width':width,'height':720},color_scheme=theme,reduced_motion='reduce');page=context.new_page();page.on('pageerror',lambda e:errors.append(e.stack));page.clock.set_fixed_time('2026-11-16T'+time+':00.000Z');page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.locator('.footer [data-business-hours-status][data-state]').wait_for(state='attached');page.wait_for_timeout(250)
    if scale==2:page.evaluate("""()=>{const es=[...document.querySelectorAll('body *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())),sizes=es.map(e=>parseFloat(getComputedStyle(e).fontSize));es.forEach((e,i)=>e.style.fontSize=sizes[i]*2+'px')}""")
    trigger=page.locator('.footer .info-trigger-text');trigger.scroll_into_view_if_needed();trigger.click();page.wait_for_timeout(100)
    panel=page.locator('.footer .business-hours-panel');assert panel.is_visible()
    value=panel.evaluate("""e=>{const s=e.querySelector('.business-hours-status'),d=e.querySelector('.business-hours-detail'),c=getComputedStyle(s),n=getComputedStyle(d);return{rect:e.getBoundingClientRect().toJSON(),status:s.textContent,detail:d.textContent,statusRect:s.getBoundingClientRect().toJSON(),detailRect:d.getBoundingClientRect().toJSON(),statusWeight:c.fontWeight,detailWeight:n.fontWeight,statusDot:getComputedStyle(s,'::before').content,separator:getComputedStyle(d,'::before').content,overflow:e.scrollWidth>e.clientWidth+1}}""")
    assert ' '.join(value['status'].split())==heading and ' '.join(value['detail'].split())==detail,value
    assert value['statusWeight']=='600' and value['detailWeight']=='400' and value['statusDot']=='""' and '•'in value['separator'],value
    assert panel.locator('.business-hours-status').get_attribute('data-state')==state
    assert panel.locator('.business-hours-status').evaluate("""(e,token)=>{const probe=document.createElement('span');probe.style.color=`var(${token})`;e.append(probe);const expected=getComputedStyle(probe).color;probe.remove();return getComputedStyle(e,'::before').backgroundColor===expected}""",color), (state,color)
    r=value['rect'];assert r['x']>=0 and r['right']<=width+1 and r['y']>=0 and r['bottom']<=720 and not value['overflow'],value
    if width>=1024 and scale==1:assert abs(value['statusRect']['y']-value['detailRect']['y'])<1,('desktop message is not one line',value)
    if width in [320,1440]and theme=='light':page.screenshot(path=str(OUT/f'{args.engine}-{width}-text{scale}.png'))
    page.keyboard.press('Escape');page.wait_for_timeout(50);assert not panel.is_visible();assert trigger.evaluate('e=>document.activeElement===e')
    rows.append({'width':width,'theme':theme,'textScale':scale,'utcTime':time,'state':state,'colorToken':color,'panel':value});context.close()
 browser.close()
assert not errors,errors
(OUT/f'acceptance-{args.engine}.json').write_text(json.dumps({'origin':args.origin,'engine':args.engine,'cases':rows,'errors':errors,'published':False,'physicalDevice':False},ensure_ascii=False,indent=2),encoding='utf8')
print('PASS',args.engine,len(rows),'hours cases: intrinsic desktop line, semantic weights, narrow/text200, keyboard dismissal')
