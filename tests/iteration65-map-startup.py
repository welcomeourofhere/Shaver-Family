"""Map: stable geometry, shared loading state, ready fade and timeout recovery."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321/');parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--theme',choices=['light','dark'],default='light');parser.add_argument('--real-provider',action='store_true');args=parser.parse_args()
OUT=ROOT/'tmp/planning/iteration65/map';OUT.mkdir(parents=True,exist_ok=True)
rows=[]
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 for motion in ['no-preference','reduce']:
  for outcome in ['ready','timeout']:
   context=browser.new_context(viewport={'width':1440,'height':900},reduced_motion=motion,color_scheme=args.theme);pending=[];requests=[];errors=[]
   context.route('https://yandex.ru/map-widget/**',lambda r:(requests.append(r.request.url),r.fulfill(content_type='text/html',body='<html><head><style>body{margin:0;background:#fff}</style></head><body>Controlled map provider<img src="https://yandex.ru/__soyuz_map_ready__.svg"></body></html>')))
   context.route('https://yandex.ru/__soyuz_map_ready__.svg',lambda r:pending.append(r))
   page=context.new_page();page.on('pageerror',lambda e:errors.append(e.stack));page.goto(args.origin,wait_until='domcontentloaded');page.wait_for_function('document.readyState==="complete"&&document.fonts.status==="loaded"');page.wait_for_timeout(200)
   assert not requests,'offscreen map must not bootstrap'
   host=page.locator('.contact-map');frame=host.locator(':scope>iframe')
   geometry=host.evaluate('e=>({width:e.offsetWidth,height:e.offsetHeight,top:e.getBoundingClientRect().top+scrollY})')
   if outcome=='timeout':page.evaluate('document.documentElement.style.setProperty("--loading-timeout","700ms")')
   host.scroll_into_view_if_needed();page.wait_for_function('document.querySelector(".contact-map").getAttribute("aria-busy")==="true"');page.wait_for_timeout(280)
   pending_opacity=frame.evaluate('e=>Number(getComputedStyle(e).opacity)')
   assert pending_opacity<.01,('blank iframe visible during load',args.engine,motion,pending_opacity)
   assert frame.evaluate('e=>getComputedStyle(e).pointerEvents')=='none','hidden provider must not capture approach wheel/clicks'
   assert page.locator('.contact-map>.loading-layer').is_visible()
   assert len(requests)==1
   if outcome=='ready':
    assert pending
    for route in pending:route.fulfill(content_type='image/svg+xml',body='<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>')
   page.wait_for_function('document.querySelector(".contact-map").getAttribute("aria-busy")==="false"')
   poses=[]
   for _ in range(8):poses.append(frame.evaluate('e=>Number(getComputedStyle(e).opacity)'));page.wait_for_timeout(35)
   assert poses[-1]>.99,(motion,outcome,poses)
   if motion=='reduce':assert all(v>.99 for v in poses)
   assert not page.locator('.contact-map>.loading-layer').is_visible()
   after=host.evaluate('e=>({width:e.offsetWidth,height:e.offsetHeight,top:e.getBoundingClientRect().top+scrollY})');assert all(abs(geometry[k]-after[k])<.01 for k in geometry),(geometry,after)
   page.wait_for_timeout(220)
   page.evaluate('window.__headerClassWrites=[];window.__headerObserver=new MutationObserver(ms=>__headerClassWrites.push(...ms.map(m=>m.target.className)));__headerObserver.observe(document.querySelector(".site-header"),{attributes:true,attributeFilter:["class"]});window.__mapScrollStart=scrollY')
   page.mouse.wheel(0,80);page.wait_for_timeout(650)
   chrome=page.evaluate('({moved:scrollY>__mapScrollStart,writes:__headerClassWrites.length})');page.evaluate('__headerObserver.disconnect()')
   assert chrome['moved']and chrome['writes']==0,('redundant header state writes during settled scroll',chrome)
   assert not errors,errors
   rows.append({'motion':motion,'theme':args.theme,'outcome':outcome,'pendingOpacity':pending_opacity,'readyPoses':poses,'geometry':geometry,'header':chrome,'errors':errors})
   if outcome=='timeout':
    for route in pending:route.fulfill(content_type='image/svg+xml',body='<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>')
   context.close()
 if args.real_provider:
  context=browser.new_context(viewport={'width':1440,'height':900},color_scheme=args.theme);page=context.new_page();page.goto(args.origin,wait_until='domcontentloaded');page.locator('.contact-map').scroll_into_view_if_needed()
  page.wait_for_function('document.querySelector(".contact-map iframe").src.includes("yandex.ru/map-widget")');page.wait_for_function('document.querySelector(".contact-map").getAttribute("aria-busy")==="false"',timeout=25000);page.wait_for_timeout(350)
  assert page.locator('.contact-map>iframe').evaluate('e=>Number(getComputedStyle(e).opacity)')>.99
  page.screenshot(path=str(OUT/f'map-real-{args.engine}.png'))
  rows.append({'realProvider':True,'loadedIframe':True,'visibleAfterLoad':True});context.close()
 browser.close()
(OUT/f'map-startup-{args.engine}-{args.theme}.json').write_text(json.dumps({'origin':args.origin,'cases':rows,'physicalDevice':False,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',args.engine,len(rows),'map loading/ready/timeout, normal and reduced motion, stable geometry')
