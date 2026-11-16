"""Public Tilda delivery vs the same source build; no booking or purchase submission."""
import argparse,importlib.util,json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reg',ROOT/'tests/device-regression.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
parser=argparse.ArgumentParser();parser.add_argument('--origin',choices=['https://stay-tan-habanero.tilda.ws','https://soyuz.hair'],default='https://stay-tan-habanero.tilda.ws');args=parser.parse_args()
server,local=reg.serve(ROOT/'dist');origin=args.origin;rows=[];out=ROOT/'tmp/planning/iteration63';out.mkdir(parents=True,exist_ok=True);before=reg.digest(ROOT/'dist')
try:
 with sync_playwright()as p:
  for engine in ['chromium','firefox','webkit']:
   browser=getattr(p,engine).launch(**({'channel':'chrome'}if engine=='chromium'else{}));context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');page=context.new_page();source=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.set_default_timeout(18000);source.set_default_timeout(18000);page.goto(origin);source.goto(local);page.evaluate('document.fonts.ready');source.evaluate('document.fonts.ready');page.wait_for_selector('.hero-scene[data-news-state=ready]');source.wait_for_selector('.hero-scene[data-news-state=ready]')
   assert page.locator('[data-news-id]').count()==10;assert page.locator('h1').count()==1
   for width in [320,390,768,960,1024,1440]:
    for theme in ['light','dark']:
     for tab in [page,source]:
      tab.bring_to_front();tab.set_viewport_size({'width':width,'height':1000});tab.evaluate('(t)=>document.documentElement.dataset.theme=t',theme);tab.evaluate('document.fonts.ready');tab.wait_for_timeout(350)
     def geometry(tab):return tab.evaluate("""()=>({overflow:document.documentElement.scrollWidth-innerWidth,font:getComputedStyle(document.querySelector('.first-visit p')).fontFamily,color:getComputedStyle(document.querySelector('h1')).color,sections:[...document.querySelectorAll('main > section')].map(e=>({id:e.id,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))})""")
     page.bring_to_front();page.wait_for_timeout(100);live,src=geometry(page),geometry(source);assert live['overflow']<=1,(engine,width,live,src);assert live['font']==src['font'];assert live['color']==src['color'];assert len(live['sections'])==len(src['sections'])
     for a,b in zip(live['sections'],src['sections']):assert a['id']==b['id']and abs(a['width']-b['width'])<=1 and abs(a['height']-b['height'])<=2,(engine,width,a,b)
     if engine=='chromium'and width in [390,768,1440]:page.screenshot(path=str(ROOT/f'artifacts/iteration63/live-{width}-{theme}.png'))
     rows.append({'engine':engine,'width':width,'theme':theme,'sourceLayoutMatch':True,'overflow':live['overflow'],'headingColor':live['color']})
   page.set_viewport_size({'width':1440,'height':1000});page.mouse.move(4,4);page.locator('.hero-dot').nth(2).click();page.wait_for_function("document.querySelectorAll('.hero-slide')[2].dataset.heroActive==='true'");rail=page.locator('.hero-rail');box=rail.bounding_box();y=max(140,box['y']+120);assert y<box['y']+box['height']-180;page.mouse.move(box['x']+box['width']*.65,y);page.mouse.down();page.mouse.move(box['x']+box['width']*.25,y,steps=12);page.mouse.up();page.wait_for_function("document.querySelectorAll('.hero-slide')[3].dataset.heroActive==='true'");rows.append({'engine':engine,'liveNewsMouseDrag':True})
   pending=[];context.route('https://*.yclients.ru/**',lambda r:pending.append(r)if r.request.resource_type=='document'else r.abort());page.locator('.header-book').click();indicator=page.locator('.booking-provider > .loading-layer .loading-indicator');indicator.wait_for(state='visible');centers=page.evaluate("""()=>{const p=document.querySelector('.booking-panel').getBoundingClientRect(),i=document.querySelector('.booking-provider .loading-indicator').getBoundingClientRect();return[Math.abs(i.x+i.width/2-p.x-p.width/2),Math.abs(i.y+i.height/2-p.y-p.height/2)]}""");assert max(centers)<1,centers
   for route in pending:route.fulfill(content_type='text/html',body='<html><body>Provider fixture</body></html>')
   page.wait_for_function("document.querySelector('.booking-provider').getAttribute('aria-busy')==='false'");page.locator('[data-booking-close]').click();page.wait_for_function("!document.querySelector('#booking-drawer').open")
   context.route('https://o16013.yclients.ru/**',lambda r:r.fulfill(content_type='text/html',body='<html><body>Certificate fixture</body></html>'))
   with context.expect_page()as popup:page.locator('.certificate-buy').click()
   popup.value.wait_for_url('https://o16013.yclients.ru/certificates');popup.value.close();assert not page.locator('#booking-drawer').evaluate('e=>e.open');rows.append({'engine':engine,'liveLoaderCenter':centers,'certificateNewTab':True,'providerFixture':True})
   assert not errors,errors;context.close();browser.close();print('PASS',engine,'Tilda source layout, live news drag and provider shell',flush=True)
finally:
 server.shutdown();server.server_close();after=reg.digest(ROOT/'dist');name='live-public.json'if origin=='https://soyuz.hair'else'live.json';(out/name).write_text(json.dumps({'origin':origin,'before':before,'after':after,'unchanged':before==after,'cases':rows,'bookingSubmitted':False,'purchaseSubmitted':False},indent=2),encoding='utf-8')
assert len(rows)==42
assert before==after
