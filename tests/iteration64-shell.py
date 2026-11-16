"""Serve the built source through native Tilda shared-page wrappers before publication."""
import argparse,importlib.util,json
from urllib.parse import urlsplit
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
package=module('package','scripts/prepare-tilda-release.py');reg=module('reg','tests/device-regression.py')
parser=argparse.ArgumentParser();parser.add_argument('--engine',default='chromium',choices=['chromium','firefox','webkit']);args=parser.parse_args()
OUT=ROOT/'tmp/planning/iteration64';OUT.mkdir(parents=True,exist_ok=True)
home=BeautifulSoup((ROOT/'dist/index.html').read_text(encoding='utf-8'),'html.parser');chrome=package.split_shared_chrome(home)
def fixture(soup):
 package.protect_embedded_css(soup)
 package.split_shared_chrome(soup)if soup.select('.site-header')else None
 soup.head.append(BeautifulSoup('<style>'+package.HOST_CSS+'</style>','html.parser'))
 content=soup.body.decode_contents();soup.body.clear()
 native=lambda code:'<div class="r t-rec"><div class="t123"><div class="t-container_100"><div class="t-width t-width_100">'+code+'</div></div></div></div>'
 soup.body.append(BeautifulSoup('<div id="allrecords"><div id="t-header" class="t-records">'+native(chrome['header'])+'</div>'+native(content)+'<div id="t-footer" class="t-records">'+native(chrome['footer'])+'</div></div>','html.parser'))
 return str(soup)
home_html=fixture(home)
story=BeautifulSoup((ROOT/'dist/masters/sonya-kid/index.html').read_text(encoding='utf-8'),'html.parser');story_html=fixture(story)
server,origin=reg.serve(ROOT/'dist');rows=[]
try:
 with sync_playwright()as p:
  browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
  for width in [1440,390]:
   context=browser.new_context(viewport={'width':width,'height':900},reduced_motion='no-preference');requests=[]
   # Leave provider navigation pending so its loading state remains visible.
   context.route('https://*.yclients.ru/**',lambda route:None)
   context.route(origin+'_astro/*.css',lambda route:route.fulfill(content_type='text/css',body=package.protected_css((ROOT/'dist'/urlsplit(route.request.url).path.lstrip('/')).read_text(encoding='utf-8'))))
   def document(route):
    requests.append(route.request.url);route.fulfill(content_type='text/html',body=story_html if'/masters/'in route.request.url else home_html)
   context.route(origin,document);context.route(origin+'masters/sonya-kid/',document)
   page=context.new_page();page.goto(origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(600)
   assert page.locator('.site-header').count()==page.locator('.footer').count()==page.locator('#mobile-menu').count()==1
   if width>960:
    page.locator('.header-nav a[href="/#masters"]').click();page.wait_for_timeout(2300)
    assert len(requests)==1,('local shared-header anchor reloaded document',requests)
    assert abs(page.locator('#masters').evaluate('e=>e.getBoundingClientRect().top')-100)<2
    page.mouse.wheel(0,-180);page.wait_for_timeout(700)
    assert page.locator('.site-header').bounding_box()['y']>=10
    page.locator('.more-menu > summary').hover();page.wait_for_timeout(350);assert page.locator('.more-panel').is_visible()
    original_canvas=page.locator('#allrecords').bounding_box()['width']
    page.locator('.header-book').click();page.wait_for_timeout(700)
    canvas=page.locator('#allrecords').bounding_box();header=page.locator('.site-header').bounding_box();section=page.locator('#services > .shell').bounding_box();panel=page.locator('.booking-panel').bounding_box()
    assert abs(canvas['width']-(original_canvas-panel['width']))<2,('booking canvas width',original_canvas,canvas,panel)
    assert abs(header['width']-section['width'])<2,('booking shrank nested content twice',header,section)
    loader=page.locator('.booking-panel .loading-indicator')
    assert loader.is_visible(),'pending provider has no visible loader'
    if loader.count():
     frames=[]
     for _ in range(8):
      frames.append(loader.evaluate('e=>Array.from(e.children,x=>getComputedStyle(x).opacity)'));page.wait_for_timeout(130)
     assert len({str(frame)for frame in frames})>1,'booking loader is static in normal motion'
    page.locator('[data-booking-close]').click();page.wait_for_timeout(400)
   else:
    page.locator('[data-open-menu]').click();page.wait_for_timeout(350)
    page.locator('.dock-content nav a[href="/#services"]').click();page.wait_for_timeout(2000)
    assert not page.locator('#mobile-menu').evaluate('e=>e.open'),'shared-page navigation left mobile menu open'
    assert len(requests)==1,('mobile shared-header anchor reloaded document',requests)
    service_top=page.locator('#services').evaluate('e=>e.getBoundingClientRect().top')
    positions=[]
    for _ in range(8):positions.append(page.locator('#services').evaluate('e=>e.getBoundingClientRect().top'));page.wait_for_timeout(150)
    assert abs(positions[-1]-16)<2,('mobile service target',service_top,positions)
   rows.append({'width':width,'sharedAnchorNoReload':True})
   page.goto(origin+'masters/sonya-kid/',wait_until='domcontentloaded');page.evaluate('document.fonts.ready')
   if width>960:page.locator('.header-nav a[href="/#masters"]').click()
   else:
    page.locator('[data-open-menu]').click();page.wait_for_timeout(350);page.locator('.dock-content nav a[href="/#masters"]').click()
   page.wait_for_url(origin+'#masters');rows.append({'width':width,'articleReturnsHome':True});context.close()
  browser.close()
finally:server.shutdown();server.server_close()
(OUT/f'shell-{args.engine}.json').write_text(json.dumps({'engine':args.engine,'cases':rows},indent=2),encoding='utf-8')
print('PASS',args.engine,len(rows),'native shared wrapper scenarios')
