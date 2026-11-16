"""Pending provider documents, common loader geometry and real certificate popups."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reg',ROOT/'tests/device-regression.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
server,url=reg.serve(ROOT/'dist');sha=reg.digest(ROOT/'dist');sources=reg.sources();rows=[]
out=ROOT/'tmp/planning/iteration63';out.mkdir(parents=True,exist_ok=True)
shots=ROOT/'artifacts/iteration63';shots.mkdir(parents=True,exist_ok=True)
try:
 with sync_playwright()as p:
  for engine in ['chromium','firefox','webkit']:
   browser=getattr(p,engine).launch(**({'channel':'chrome'}if engine=='chromium'else{}))
   context=browser.new_context(reduced_motion='reduce');pending=[]
   def route_request(route):
    address=route.request.url
    if address.startswith(url):route.continue_()
    elif urlparse(address).hostname=='o16013.yclients.ru':route.fulfill(content_type='text/html',body='<html><body>Certificate provider fixture</body></html>')
    elif '.yclients.'in urlparse(address).hostname:pending.append(route)
    else:route.abort()
   context.route('**/*',route_request);page=context.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for width in [1440,800,390]:
    for theme in ['light','dark']:
     page.set_viewport_size({'width':width,'height':900});page.goto(url);page.evaluate('document.fonts.ready');page.evaluate('(theme)=>document.documentElement.dataset.theme=theme',theme)
     page.wait_for_function("document.querySelector('.of-rail')?.dataset.loopReady")
     booking=next(b for b in page.locator('[data-booking]:not([data-booking-form=certificate])').all()if b.is_visible())
     booking.click();page.wait_for_function("document.querySelector('.booking-provider')?.getAttribute('aria-busy')==='true'")
     indicator=page.locator('.booking-provider > .loading-layer [data-loading-indicator]');indicator.wait_for(state='visible')
     geometry=page.evaluate("""()=>{const p=document.querySelector('.booking-panel').getBoundingClientRect(),i=document.querySelector('.booking-provider .loading-indicator').getBoundingClientRect(),s=getComputedStyle(document.querySelector('[data-booking-status]'));return{dx:i.x+i.width/2-p.x-p.width/2,dy:i.y+i.height/2-p.y-p.height/2,statusClip:s.clipPath,tiles:document.querySelectorAll('.booking-provider .loading-indicator>i').length}}""")
     assert abs(geometry['dx'])<1 and abs(geometry['dy'])<1,geometry
     assert geometry['tiles']==4 and geometry['statusClip']=='inset(50%)',geometry
     if engine=='chromium'and theme=='light':page.screenshot(path=str(shots/f'booking-loading-{width}.png'))
     assert pending,'The provider document must still be pending'
     for route in pending[:]:route.fulfill(content_type='text/html',body='<html><body>Booking provider fixture</body></html>');pending.remove(route)
     page.wait_for_function("document.querySelector('.booking-provider').getAttribute('aria-busy')==='false'")
     assert not indicator.is_visible();assert not page.locator('[data-booking-recovery]').is_visible()
     page.locator('[data-booking-close]').click();page.wait_for_function("!document.querySelector('#booking-drawer').open")
     rows.append({'engine':engine,'width':width,'theme':theme,'pendingLoader':geometry,'loadedDocument':True})
     buy=page.locator('.certificate-buy');assert buy.get_attribute('aria-haspopup')is None
     with context.expect_page()as opened:buy.click()
     popup=opened.value;popup.wait_for_url('https://o16013.yclients.ru/certificates');popup.close()
     assert not page.locator('#booking-drawer').evaluate('e=>e.open')
     rows.append({'engine':engine,'width':width,'theme':theme,'certificateNewTab':True})
     if width<=960:
      page.wait_for_function("document.querySelector('[data-mobile-nav]').dataset.section==='certificates'")
      with context.expect_page()as opened:page.locator('[data-action=certificate-buy]').click()
      popup=opened.value;popup.wait_for_url('https://o16013.yclients.ru/certificates');popup.close()
      assert not page.locator('#booking-drawer').evaluate('e=>e.open');rows.append({'engine':engine,'width':width,'theme':theme,'dockCertificateNewTab':True})
   assert not errors,errors
   context.close();browser.close();print('PASS',engine,'booking loader and external certificates',flush=True)
finally:
 after=reg.digest(ROOT/'dist');server.shutdown();server.server_close()
 (out/'booking.json').write_text(json.dumps({'before':sha,'after':after,'sourceDigests':sources,'sourcesUnchanged':sources==reg.sources(),'unchanged':sha==after,'cases':rows,'providerFixture':True,'bookingSubmitted':False,'purchaseSubmitted':False},indent=2),encoding='utf-8')
assert len(rows)==48 and sha==after and sources==reg.sources()
