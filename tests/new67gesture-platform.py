"""Trusted browser input for Works/Offers; modal capability fallback never calls :modal."""
import argparse,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321/');parser.add_argument('--engine',choices=['chromium','webkit','firefox'],default='chromium');parser.add_argument('--label',required=True);args=parser.parse_args()
assert re.fullmatch(r'[\w-]+',args.label)
OUT=ROOT/'tmp/planning/iteration67/gesture-platform'/args.label;OUT.mkdir(parents=True,exist_ok=False);HOST=urlsplit(args.origin).netloc
FILES=['src/scripts/modal-scroll-lock.ts','src/scripts/mobile-nav.ts','src/scripts/dock-surface.ts','src/scripts/works.ts','src/scripts/horizontal-swipe.ts','src/scripts/native-rail-drag.ts','src/scripts/rail-selection.ts','src/styles/works.css','src/styles/offers.css']
def hashes():return{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()for f in FILES}
start=hashes();rows=[];errors=[]
FALLBACK="""(()=>{window.__invalidModalQueries=[];const supports=CSS.supports.bind(CSS);CSS.supports=(...args)=>args[0]==='selector(dialog:modal)'?false:supports(...args);for(const name of ['querySelector','querySelectorAll']){const original=Document.prototype[name];Document.prototype[name]=function(selector){if(selector.includes(':modal')){__invalidModalQueries.push(selector);throw new DOMException('Unsupported selector fixture','SyntaxError')}return original.call(this,selector)}}})()"""
STATE="""()=>{const root=document.querySelector('#works'),fan=root.querySelector('.works-fan'),card=root.querySelector('[data-work-current=true]'),cards=[...fan.querySelectorAll('[data-work-card]')];return{index:+fan.dataset.workIndex,position:+fan.dataset.workPosition,target:+fan.dataset.workTarget,moving:fan.dataset.workMoving==='true',dragging:fan.classList.contains('is-dragging'),visible:cards.filter(c=>!c.hidden&&getComputedStyle(c).display!=='none'&&+getComputedStyle(c).opacity>.01).length,limit:+getComputedStyle(root).getPropertyValue('--works-neighbor-limit'),touch:getComputedStyle(fan).touchAction,master:root.querySelector('[data-work-author]').textContent,expectedMaster:card.dataset.workMaster,caption:root.querySelector('.works-caption [data-work-caption]').textContent,expectedCaption:card.dataset.workCaption,count:root.querySelector('output').textContent,total:cards.length,overflow:document.documentElement.scrollWidth>innerWidth+1,viewport:{inner:innerWidth,layout:document.documentElement.clientWidth,visual:visualViewport.width}}}"""
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome','args':['--mute-audio']}if args.engine=='chromium'else{}))
 def fresh(width=390,height=844,touch=False,fallback=False,modules=True):
  c=browser.new_context(viewport={'width':width,'height':height},has_touch=touch,**({'is_mobile':True}if touch and args.engine!='firefox'else{}))
  c.route('**/*',lambda r:r.continue_()if urlsplit(r.request.url).netloc==HOST and(modules or r.request.resource_type!='script')else r.abort())
  c.add_init_script("if(window.top===window){localStorage.setItem('soyuz.analytics.v1','denied');window.__input=[];for(const t of['pointerdown','pointerup','pointercancel','touchstart','touchend','touchcancel','click'])addEventListener(t,e=>{const row={type:e.type,trusted:e.isTrusted,target:e.target?.closest?.('.works-fan,.of-rail')?.className??'',prevented:false};__input.push(row);queueMicrotask(()=>row.prevented=e.defaultPrevented)},{capture:true,passive:true})}")
  if fallback:c.add_init_script(FALLBACK)
  page=c.new_page();page.on('pageerror',lambda e:errors.append(e.stack or str(e)));page.goto(args.origin,wait_until='domcontentloaded');page.wait_for_timeout(250);return c,page
 def expose(page,selector):
  page.locator(selector).first.scroll_into_view_if_needed();page.wait_for_timeout(180)
 def state(page):
  s=page.evaluate(STATE);normal=lambda v:' '.join(v.split());assert normal(s['master'])==normal(s['expectedMaster'])and normal(s['caption'])==normal(s['expectedCaption'])and not s['overflow'],s
  assert s['count']==f"{s['index']+1} / {s['total']}",s
  return s
 def rest(page):page.wait_for_function('document.querySelector(".works-fan").dataset.workMoving!=="true"');page.wait_for_timeout(80)
 def point(page,selector):
  return page.locator(selector).first.evaluate("e=>{const r=e.getBoundingClientRect();return{x:Math.max(30,Math.min(innerWidth-30,r.left+r.width/2)),y:Math.max(80,Math.min(innerHeight-100,r.top+r.height/2))}}")
 # Full CSS progression, including SSR without enhancement and the exact boundaries.
 for width in [430,600,601,800,801,1100,1101]:
  c,page=fresh(width=width,height=1000,modules=False);expose(page,'.works-fan')
  visible=page.locator('[data-work-card]').evaluate_all("cs=>cs.filter(c=>!c.hidden&&getComputedStyle(c).display!=='none'&&+getComputedStyle(c).opacity>.01).length")
  expected=page.evaluate("matchMedia('(max-width:600px)').matches?3:matchMedia('(max-width:800px)').matches?5:matchMedia('(max-width:1100px)').matches?7:9")
  assert visible==expected,(width,visible,expected);rows.append({'case':'initial-without-modules','width':width,'visible':visible});c.close()
 c,page=fresh(width=1440,height=1000)
 for theme in ['light','dark']:
  page.evaluate('v=>document.documentElement.dataset.theme=v',theme)
  for width in [320,390,430,600,601,800,801,960,961,1100,1101,1440]:
   page.set_viewport_size({'width':width,'height':1000});expose(page,'.works-fan');s=state(page);limit=page.evaluate("matchMedia('(max-width:600px)').matches?1:matchMedia('(max-width:800px)').matches?2:matchMedia('(max-width:1100px)').matches?3:4")
   assert s['limit']==limit and s['visible']==limit*2+1,s
   spacing=page.locator('.works-fan').evaluate("e=>{const c=e.querySelector('[data-work-current=true]'),next=[...e.querySelectorAll('[data-work-card]')].find(n=>Number(n.style.getPropertyValue('--work-offset'))===1);return{step:new DOMMatrix(getComputedStyle(next).transform).m41-new DOMMatrix(getComputedStyle(c).transform).m41,centerWidth:c.offsetWidth}}")
   assert spacing['step']>0,(width,spacing)
   cuts=page.locator('.works-fan').evaluate("e=>{const r=e.getBoundingClientRect();return[...e.querySelectorAll('[data-work-card]:not([hidden])')].filter(c=>{const b=c.getBoundingClientRect();return b.left<r.left-1||b.right>r.right+1||b.top<r.top-1||b.bottom>r.bottom+1}).length}")
   assert cuts==0,(width,s,cuts)
   if theme=='light'and width in [320,600,961,1440]:page.locator('#works').screenshot(path=str(OUT/f'works-{width}.png'))
   rows.append({'case':'neighbors','theme':theme,'width':width,'spacing':spacing,**s})
 # Trusted mouse: held traversal, reversal, keyboard cancellation and fresh drag.
 page.set_viewport_size({'width':1440,'height':1000});expose(page,'.works-fan');q=point(page,'[data-work-current=true]');page.mouse.move(q['x'],q['y']);page.mouse.down();held=[]
 for dx in [-30,-70,-120,-180,-240,-150,-80,20,100]:
  page.mouse.move(q['x']+dx,q['y']);page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');held.append(state(page))
 assert max(s['position']for s in held)-min(s['position']for s in held)>2 and all(s['dragging']for s in held),held
 page.keyboard.press('Escape');page.mouse.up();rest(page);assert not state(page)['dragging']
 q=point(page,'[data-work-current=true]');page.mouse.move(q['x'],q['y']);page.mouse.down();page.mouse.move(q['x']-80,q['y'],steps=8);page.mouse.up();rest(page)
 rows.append({'case':'trusted-mouse-reversal-cancel-new-sequence','held':held,'after':state(page)});c.close()
 # An unsupported :modal parser still locks native modal layers and ignores docked booking.
 c,page=fresh(fallback=True);page.locator('[data-open-menu]').click();page.wait_for_timeout(330)
 assert page.locator('#mobile-menu').evaluate('e=>e.open')and page.evaluate('document.body.dataset.modalScrollLocked')=='true'
 page.locator('#mobile-menu .menu-contact-row [data-analytics-settings]').click();page.locator('#cookie-settings').wait_for(state='visible');page.keyboard.press('Escape');page.wait_for_timeout(300)
 assert page.locator('#mobile-menu').evaluate('e=>e.open')and page.evaluate('document.body.dataset.modalScrollLocked')=='true'
 page.keyboard.press('Escape');page.wait_for_timeout(320);assert page.evaluate('document.body.dataset.modalScrollLocked')is None
 page.set_viewport_size({'width':1920,'height':1000});page.wait_for_timeout(180);page.locator('.header-book').click();page.wait_for_timeout(300)
 booking=page.locator('#booking-drawer').evaluate('e=>({open:e.open,layout:e.dataset.layout,modal:e.getAttribute("aria-modal")})')
 assert booking['open']and booking['layout']=='docked'and booking['modal']=='false'and page.evaluate('document.body.dataset.modalScrollLocked')is None,booking
 page.locator('[data-booking-close]').click();page.wait_for_timeout(320)
 assert page.evaluate('__invalidModalQueries')==[]
 rows.append({'case':'unsupported-modal-selector','dockedBooking':booking,'invalidSelectorCalls':page.evaluate('__invalidModalQueries')});c.close()
 # CDP supplies actual browser touch input. Other engines keep the precise boundary below.
 if args.engine=='chromium':
  for component,selector,width in [('works','[data-work-current=true]',390),('offers','.of-card[data-offer-active=true] .of-photo',390),('offers','.of-card[data-offer-active=true] .of-photo',1101)]:
   c,page=fresh(width=width,touch=True);expose(page,selector);cdp=c.new_cdp_session(page)
   def touch(points,kind):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':points})
   q=point(page,selector);before=state(page)['index']if component=='works'else page.locator('[data-offers]').get_attribute('data-offer-index')
   touch([dict(q,id=1)],'touchStart')
   for step in range(1,13):touch([{'x':q['x']-140*step/12,'y':q['y'],'id':1}],'touchMove');page.wait_for_timeout(18)
   touch([],'touchEnd');page.wait_for_timeout(500);rest(page)
   after=state(page)['index']if component=='works'else page.locator('[data-offers]').get_attribute('data-offer-index');assert after!=before,(component,before,after)
   if component=='offers'and width<=960:assert str(after)==page.locator('[data-of-rail]').get_attribute('data-rail-index')
   # Vertical browser scrolling must pass through either interaction surface.
   expose(page,selector);q=point(page,selector);scroll0=page.evaluate('scrollY');touch([dict(q,id=1)],'touchStart')
   for step in range(1,11):touch([{'x':q['x'],'y':q['y']-150*step/10,'id':1}],'touchMove');page.wait_for_timeout(18)
   touch([],'touchEnd');page.wait_for_timeout(250);scroll1=page.evaluate('scrollY');assert scroll1>scroll0+35,(component,scroll0,scroll1)
   # Add a second finger during a held primary contact; the page owns zoom.
   expose(page,selector);q=point(page,selector);page.evaluate('__input=[]');scale0=page.evaluate('visualViewport.scale')
   touch([{'x':q['x']-30,'y':q['y'],'id':1}],'touchStart');touch([{'x':q['x']-45,'y':q['y'],'id':1}],'touchMove')
   touch([{'x':q['x']-45,'y':q['y'],'id':1},{'x':q['x']+30,'y':q['y'],'id':2}],'touchStart')
   for step in range(1,10):touch([{'x':q['x']-45-step*5,'y':q['y'],'id':1},{'x':q['x']+30+step*5,'y':q['y'],'id':2}],'touchMove');page.wait_for_timeout(18)
   touch([],'touchEnd');page.wait_for_timeout(250);scale1=page.evaluate('visualViewport.scale');assert scale1>scale0+.1,(component,scale0,scale1)
   events=page.evaluate('__input');assert any(e['type']=='pointercancel'and e['trusted']for e in events),events
   assert not page.locator('.works-fan,.of-rail').evaluate_all("es=>es.some(e=>e.classList.contains('is-dragging'))")
   assert not any(e['type']=='click'and e['target']for e in events),events
   rows.append({'case':'trusted-CDP-touch','component':component,'width':width,'before':before,'after':after,'verticalScroll':[scroll0,scroll1],'pinchScale':[scale0,scale1],'input':events});c.close()
 else:
  c,page=fresh(touch=True);expose(page,'.works-fan');style=page.evaluate("()=>({works:getComputedStyle(document.querySelector('.works-fan')).touchAction,offers:getComputedStyle(document.querySelector('.of-rail')).touchAction,viewport:document.querySelector('meta[name=viewport]').content})")
  assert 'pan-y'in style['works']and'pinch-zoom'in style['works']and style['offers']=='auto'and'no'not in style['viewport']and'maximum-scale'not in style['viewport'],style
  c.close();c,page=fresh(touch=False);expose(page,'.works-fan');q=point(page,'[data-work-current=true]');scroll0=page.evaluate('scrollY');page.mouse.move(q['x'],q['y']);page.mouse.wheel(0,180);page.wait_for_timeout(300);assert page.evaluate('scrollY')>scroll0+30
  rows.append({'case':'engine-touch-zoom-boundary','styles':style,'nativeWheelScroll':True,'wheelContext':'desktop engine at compact viewport; mobile WebKit does not expose mouseWheel','multiTouchPinchExecuted':False,'boundary':'This Playwright engine has no CDP touch input; CSS permission and real mouse/keyboard/wheel were checked, not physical Safari pinch.'});c.close()
 browser.close()
assert errors==[],errors
end=hashes();assert start==end,'Gesture/modal sources changed during QA'
(OUT/f'{args.engine}.json').write_text(json.dumps({'engine':args.engine,'sourceStart':start,'sourceEnd':end,'rows':rows,'pageErrors':errors,'physicalDevice':False,'bookingSubmitted':False,'providerCodeExecuted':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'PASS {args.engine}: {len(rows)} gesture/platform groups; modal fallback, progressive neighbors, held reversal/cancel, touch/zoom boundary explicit')
