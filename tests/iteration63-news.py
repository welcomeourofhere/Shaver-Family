"""Posts arrive over the network; compact Hero stays video-only without fetching news."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reg',ROOT/'tests/device-regression.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
server,url=reg.serve(ROOT/'dist');before=reg.digest(ROOT/'dist');rows=[]
feed=json.loads((ROOT/'content/news.json').read_text(encoding='utf-8'));feed['generatedAt']='2030-01-01T00:00:00+03:00'
endpoint=json.loads((ROOT/'content/site.json').read_text(encoding='utf-8'))['newsFeedUrl']
html=(ROOT/'dist/index.html').read_text(encoding='utf-8')
assert 'data-news-id='not in html
for item in feed['items']:assert item['text']not in html and item['url']not in html
try:
 with sync_playwright()as p:
  for engine in ['chromium','firefox','webkit']:
   browser=getattr(p,engine).launch(**({'channel':'chrome'}if engine=='chromium'else{}));context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');pending=[];requests=[];mode=['hold'];errors=[]
   def route_request(route):
    address=route.request.url
    if address==endpoint or address==url+'data/news.json':
     requests.append(address)
     if mode[0]=='hold':pending.append(route)
     elif mode[0]=='error':route.abort()
     else:route.fulfill(content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps(feed))
     return
    if urlparse(address).hostname=='raw.githubusercontent.com'and'/media/news/'in address:
     route.fulfill(path=ROOT/'public/media/news'/Path(urlparse(address).path).name);return
    if address.startswith(url):route.continue_()
    else:route.abort()
   context.route('**/*',route_request);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.set_default_timeout(12000)
   page.goto(url);page.wait_for_function("document.querySelector('.hero-news-state [data-loading-indicator]').dataset.loadingPaused==='false'")
   page.wait_for_function("document.querySelector('.hero-scene').getAttribute('aria-busy')==='true'")
   assert page.locator('[data-news-id]').count()==0 and len(pending)==1
   bounds=page.locator('.hero-scene').bounding_box()
   pending.pop().fulfill(content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps(feed))
   page.wait_for_selector('.hero-scene[data-news-state=ready]');assert page.locator('[data-news-id]').count()==10
   after=page.locator('.hero-scene').bounding_box();assert bounds==after,(bounds,after)
   page.locator('.hero-dot').nth(3).click();page.wait_for_function("document.querySelectorAll('.hero-slide')[3].dataset.heroActive==='true'")
   assert page.locator('.hero-news-link').get_attribute('href')==feed['items'][3]['url']
   rows.append({'engine':engine,'networkOnly':True,'stableGeometry':True,'carouselAndLink':True})
   page.close();context.set_default_timeout(12000);requests.clear();page=context.new_page();page.set_viewport_size({'width':390,'height':850});page.goto(url);page.wait_for_timeout(500)
   assert not requests and page.locator('[data-news-id]').count()==0
   assert not page.locator('.hero-news-state').is_visible();assert page.locator('.hero-video').is_visible();assert page.locator('.hero-scene').get_attribute('aria-roledescription')is None;assert page.locator('.hero-position').get_attribute('hidden')is not None
   page.set_viewport_size({'width':1440,'height':1000});page.wait_for_function("document.querySelector('.hero-scene').getAttribute('aria-busy')==='true'");assert len(pending)==1
   pending.pop().fulfill(content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps(feed));page.wait_for_selector('.hero-scene[data-news-state=ready]')
   rows.append({'engine':engine,'compactNoNewsRequest':True,'resizeLoadsPosts':True})
   page.close();mode[0]='error';page=context.new_page();page.goto(url);page.wait_for_selector('.hero-scene[data-news-state=error]');assert page.locator('.hero-news-retry').is_visible();assert page.locator('.hero-news-fallback').count()==0
   mode[0]='ready';page.locator('.hero-news-retry').focus();page.keyboard.press('Enter');page.wait_for_selector('.hero-scene[data-news-state=ready]');assert page.locator('[data-news-id]').count()==10;assert page.locator('.hero-rail').evaluate('e=>e===document.activeElement')
   rows.append({'engine':engine,'failureAndKeyboardRetry':True,'focusRetained':True});assert not errors,errors
   context.close();browser.close();print('PASS',engine,'network posts, geometry, compact mode, retry',flush=True)
finally:
 after=reg.digest(ROOT/'dist');server.shutdown();server.server_close();out=ROOT/'tmp/planning/iteration63';out.mkdir(parents=True,exist_ok=True);(out/'news.json').write_text(json.dumps({'before':before,'after':after,'unchanged':before==after,'cases':rows},indent=2),encoding='utf-8')
assert len(rows)==9 and before==after
