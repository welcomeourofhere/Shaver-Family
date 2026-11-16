"""Separate reading attention from pending-image refresh; retain the same public API feed contract."""
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('regression',ROOT/'tests/device-regression.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
server,url=reg.serve(ROOT/'dist');before=reg.digest(ROOT/'dist');sources=reg.sources();rows=[]
endpoint=json.loads((ROOT/'content/site.json').read_text(encoding='utf-8'))['newsFeedUrl']
try:
 with sync_playwright()as p:
  for engine in ['chromium','firefox','webkit']:
   feed=json.loads((ROOT/'content/news.json').read_text(encoding='utf-8'));feed['generatedAt']='2030-01-01T00:00:00+03:00';requests=[]
   def route_request(route):
    address=route.request.url
    if address==endpoint:
     requests.append(feed['generatedAt']);route.fulfill(content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps(feed));return
    if address.startswith(url):route.continue_();return
    if urlparse(address).hostname=='raw.githubusercontent.com'and'/media/news/'in address:
     image=ROOT/'public/media/news'/Path(urlparse(address).path).name
     if image.exists():route.fulfill(path=image);return
    route.abort()
   browser=getattr(p,engine).launch(**({'channel':'chrome'}if engine=='chromium'else{}));context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');context.route('**/*',route_request);page=context.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.mouse.move(4,4);page.goto(url);page.evaluate('document.fonts.ready');page.wait_for_function("document.querySelector('.hero-scene').dataset.newsRevision==='2030-01-01T00:00:00+03:00'")
   colors={}
   for theme,expected in [('dark','rgb(255, 204, 41)'),('light','rgb(196, 47, 42)')]:
    page.evaluate('(theme)=>document.documentElement.dataset.theme=theme',theme)
    colors[theme]=page.locator('.hero-heading').evaluate('(e)=>getComputedStyle(e).color');assert colors[theme]==expected
    assert all(color==expected for color in page.locator('.section-title').evaluate_all('(elements)=>elements.map(e=>getComputedStyle(e).color)'))
   assert not {'1950','1941'}&set(page.locator('[data-news-id]').evaluate_all('(elements)=>elements.map(e=>e.dataset.newsId)'))
   def refresh(date):
    feed['generatedAt']=date;previous=len(requests);page.evaluate("document.dispatchEvent(new Event('visibilitychange'))");page.wait_for_timeout(250);assert len(requests)>previous
   page.locator('.hero-scene').hover();refresh('2031-01-01T00:00:00+03:00');assert page.locator('.hero-scene').get_attribute('data-news-revision').startswith('2030')
   page.mouse.move(4,4);page.wait_for_function("document.querySelector('.hero-scene').dataset.newsRevision.startsWith('2031')");rows.append({'engine':engine,'hoverPreservedThenReleased':True,'headingColors':colors,'excludedPostsAbsent':True})
   page.locator('.hero-rail').focus();refresh('2032-01-01T00:00:00+03:00');assert page.locator('.hero-scene').get_attribute('data-news-revision').startswith('2031')
   page.locator('.header-book').focus();page.wait_for_function("document.querySelector('.hero-scene').dataset.newsRevision.startsWith('2032')");rows.append({'engine':engine,'focusPreservedThenReleased':True})
   page.evaluate("(()=>{const image=document.querySelectorAll('.hero-photo')[1],decode=image.decode.bind(image);image.decode=()=>{image.decode=decode;return new Promise(resolve=>window.releasePendingImage=resolve)};document.querySelector('.hero-rail').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}))})()")
   page.wait_for_function("typeof releasePendingImage==='function'");refresh('2033-01-01T00:00:00+03:00');assert page.locator('.hero-scene').get_attribute('data-news-revision').startswith('2032')
   page.evaluate('releasePendingImage()');page.wait_for_function("document.querySelector('.hero-scene').dataset.newsRevision.startsWith('2033')");rows.append({'engine':engine,'decodeThenRefresh':True});assert not errors,errors
   context.close();browser.close();print('PASS',engine,'news attention and image refresh',flush=True)
finally:
 after=reg.digest(ROOT/'dist');server.shutdown();server.server_close();(ROOT/'tmp/planning/iteration62/news-attention.json').write_text(json.dumps({'before':before,'after':after,'unchanged':before==after,'sourcesUnchanged':sources==reg.sources(),'sourceDigests':sources,'cases':rows,'published':False},indent=2),encoding='utf-8')
assert len(rows)==9 and before==after and sources==reg.sources()
