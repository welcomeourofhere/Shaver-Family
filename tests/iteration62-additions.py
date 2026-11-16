"""Actual disclosure, native scrollbars and certificate navigation; no purchase is submitted."""
import importlib.util
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('regression',ROOT/'tests/device-regression.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
server,url=reg.serve(ROOT/'dist');before=reg.digest(ROOT/'dist');sources=reg.sources();rows=[]
out=ROOT/'artifacts/iteration62';out.mkdir(exist_ok=True,parents=True)
def route_request(route):
 if route.request.url.startswith(url):route.continue_()
 elif '.yclients.ru/'in route.request.url and route.request.resource_type=='document':route.fulfill(content_type='text/html',body='<h1>Provider navigation fixture</h1>')
 else:route.abort()
def visible(page):return page.locator('[data-review-tile]:not([hidden])')
try:
 with sync_playwright()as p:
  for engine in ['chromium','firefox','webkit']:
   browser=getattr(p,engine).launch(**({'channel':'chrome'}if engine=='chromium'else{}));context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');context.route('**/*',route_request)
   page=context.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:errors.append({'message':str(e),'stack':e.stack}))
   for width in [320,390,768,1024,1440]:
    for theme in ['light','dark']:
     page.set_viewport_size({'width':width,'height':1000});page.goto(url);page.evaluate('document.fonts.ready');page.wait_for_function("document.querySelector('[data-review-bento]').dataset.bentoReady==='true'");page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
     assert visible(page).count()==4
     first=visible(page).evaluate_all("cs=>cs.map(c=>({id:c.id,x:c.offsetLeft,y:c.offsetTop,w:c.offsetWidth,h:c.offsetHeight,tone:c.dataset.reviewTone}))")
     more=page.locator('[data-review-more]');more.click();page.wait_for_function("document.querySelectorAll('[data-review-tile]:not([hidden])').length===8");page.wait_for_timeout(150)
     after=page.locator('[data-review-tile]').evaluate_all("cs=>cs.map(c=>({id:c.id,x:c.offsetLeft,y:c.offsetTop,w:c.offsetWidth,h:c.offsetHeight,tone:c.dataset.reviewTone}))")
     assert all(item==next(c for c in after if c['id']==item['id'])for item in first),(engine,width,first,after)
     assert more.get_attribute('aria-expanded')=='true'
     if width<=960:assert page.locator('[data-rail-controls="reviews-rail"] output').inner_text().endswith('/ 08')
     if engine=='chromium'and theme=='light'and width in [390,1440]:page.screenshot(path=str(out/f'reviews-expanded-{width}.png'))
     more.click();page.wait_for_function("document.querySelectorAll('[data-review-tile]:not([hidden])').length===4");page.wait_for_timeout(150)
     if width<=960:assert page.locator('[data-rail-controls="reviews-rail"] output').inner_text().endswith('/ 04')
     assert more.evaluate("e=>{const s=getComputedStyle(e);return e.scrollWidth<=e.clientWidth&&e.offsetHeight>=44&&s.whiteSpace==='nowrap'&&parseFloat(s.paddingLeft)>=12}")
     rows.append({'engine':engine,'reviewDisclosure':True,'width':width,'theme':theme,'firstGroupUnchanged':True})
   # Idle thumb is transparent; real native scroll reveals it, then the same gutter remains.
   page.set_viewport_size({'width':390,'height':900});page.goto(url);page.evaluate('document.fonts.ready');page.wait_for_function("document.querySelector('[data-review-bento]').dataset.bentoReady==='true'")
   page.locator('#review-03').evaluate("e=>e.scrollIntoView({block:'center',inline:'start',behavior:'instant'})");page.wait_for_timeout(150);page.locator('#review-03 [data-review-read]').click();page.wait_for_timeout(1100)
   prose=page.locator('#review-03 .review-prose');width_before=prose.evaluate('e=>e.clientWidth');assert prose.evaluate("e=>getComputedStyle(e).getPropertyValue('--scrollbar-paint').trim()")=='transparent'
   prose.evaluate('e=>e.scrollTop=80');page.wait_for_function("document.querySelector('#review-03 .review-prose').hasAttribute('data-scrollbar-active')")
   assert prose.evaluate("e=>getComputedStyle(e).getPropertyValue('--scrollbar-paint').trim()")!='transparent'
   page.wait_for_timeout(1100);assert not prose.get_attribute('data-scrollbar-active')and prose.evaluate("e=>getComputedStyle(e).getPropertyValue('--scrollbar-paint').trim()")=='transparent'
   assert prose.evaluate('e=>e.clientWidth')==width_before
   rows.append({'engine':engine,'inactiveScrollbar':True,'unchangedGutter':True})
   # Hours and the phone/more panel share the same colour token, even in the top layer.
   page.set_viewport_size({'width':1440,'height':1000});page.goto(url);hours=page.locator('.header-hours button');hours.click();panel=page.locator('#'+hours.get_attribute('aria-describedby'))
   assert panel.evaluate('e=>getComputedStyle(e).backgroundColor')==page.locator('.header-contact-panel .surface-shell').evaluate('e=>getComputedStyle(e).backgroundColor')
   page.keyboard.press('Escape');rows.append({'engine':engine,'hoursPanelColour':True})
   # Desktop shares the existing drawer and can replace booking/certificate context.
   buy=page.locator('.certificate-buy');buy.click();page.wait_for_function("document.querySelector('[data-booking-frame]').src==='https://o16013.yclients.ru/certificates'")
   assert page.locator('#booking-drawer').get_attribute('data-booking-form')=='certificate'
   assert 'сертификат'in page.locator('#booking-drawer-title').inner_text().lower();assert page.locator('[data-booking-drawer][open]').count()==1
   page.locator('.header-book').click();page.wait_for_function("document.querySelector('[data-booking-frame]').src==='https://b2763199.yclients.ru/'")
   assert page.locator('#booking-drawer').get_attribute('data-booking-form')=='booking'
   page.locator('[data-booking-close]').click();rows.append({'engine':engine,'certificateDrawerAndBookingReplacement':True})
   for width in [390,768]:
    page.set_viewport_size({'width':width,'height':900});page.goto(url);buy=page.locator('.certificate-buy');buy.scroll_into_view_if_needed()
    assert buy.get_attribute('aria-haspopup')is None
    with context.expect_page()as opened:buy.click()
    popup=opened.value;popup.wait_for_url('https://o16013.yclients.ru/certificates');popup.close()
    assert not page.locator('#booking-drawer').evaluate('e=>e.open')
    page.wait_for_function("document.querySelector('[data-mobile-nav]').dataset.section==='certificates'")
    with context.expect_page()as opened:page.locator('[data-action="certificate-buy"]').click()
    popup=opened.value;popup.wait_for_url('https://o16013.yclients.ru/certificates');popup.close()
    assert not page.locator('#booking-drawer').evaluate('e=>e.open');rows.append({'engine':engine,'certificateNewTab':True,'width':width,'dock':True})
   assert not errors,errors;context.close()
   nojs=browser.new_context(java_script_enabled=False,viewport={'width':1440,'height':1000});nojs.route('**/*',route_request);fallback=nojs.new_page();fallback.goto(url)
   assert fallback.locator('.review-card:visible').count()==8 and fallback.locator('.certificate-buy').get_attribute('target')=='_blank'
   rows.append({'engine':engine,'noScriptReviewsAndCertificateLink':True});nojs.close();browser.close();print('PASS',engine,'latest owner additions',flush=True)
finally:
 after=reg.digest(ROOT/'dist');server.shutdown();server.server_close();(ROOT/'tmp/planning/iteration62/additions.json').write_text(json.dumps({'before':before,'after':after,'unchanged':before==after,'sourceDigests':sources,'sourcesUnchanged':sources==reg.sources(),'cases':rows,'providerFixture':True,'purchaseSubmitted':False,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
assert before==after and sources==reg.sources()
