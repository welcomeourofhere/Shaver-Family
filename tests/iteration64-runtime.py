"""Normal-motion regressions: real loader frames, navigation and short-height About."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321');parser.add_argument('--engine',default='chromium',choices=['chromium','firefox','webkit']);args=parser.parse_args()
OUT=ROOT/'tmp/planning/iteration64';OUT.mkdir(parents=True,exist_ok=True)
rows=[];failures=[]
def check(condition,message):
 if not condition:failures.append(message)

with sync_playwright() as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 for motion in ['no-preference','reduce']:
  context=browser.new_context(viewport={'width':1440,'height':900},reduced_motion=motion)
  held=[];context.route('**/data/news.json',lambda route:held.append(route))
  page=context.new_page();page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(350)
  indicator=page.locator('.hero-news-state .loading-indicator');indicator.wait_for(state='visible')
  poses=[]
  for _ in range(11):
   poses.append(indicator.locator('i').first.evaluate('e=>[getComputedStyle(e).transform,getComputedStyle(e).opacity]'));page.wait_for_timeout(125)
  changes=len({tuple(pose)for pose in poses})
  check(changes>2 if motion=='no-preference'else changes==1,f'loader frames {motion}: {changes}')
  check(page.locator('.hero-news-fallback').count()==0,'unwanted VK link under loader')
  page.locator('#services').scroll_into_view_if_needed();page.wait_for_timeout(400)
  check(indicator.get_attribute('data-loading-paused')=='true','offscreen loader must pause')
  page.evaluate('scrollTo({top:0,behavior:"instant"})');page.wait_for_timeout(400)
  check(indicator.get_attribute('data-loading-paused')=='false','visible loader must resume')
  rows.append({'motion':motion,'loaderDistinctFrames':changes,'loaderPoses':poses})
  for route in held:route.fulfill(content_type='application/json',body=(ROOT/'public/data/news.json').read_text(encoding='utf-8'))
  context.close()
 context=browser.new_context(reduced_motion='no-preference',viewport={'width':1440,'height':900});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(500)
 for width,height in [(1024,600),(1280,720),(1440,900),(1440,1080)]:
  page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(450)
  page.locator('#about').evaluate('e=>scrollTo({top:e.getBoundingClientRect().top+scrollY+200,behavior:"instant"})');page.wait_for_timeout(500)
  geometry=page.evaluate("""()=>{const h=document.querySelector('#about-title'),s=document.querySelector('[data-about-stack]'),card=s.querySelector('.about-card');const hs=getComputedStyle(h);return{headingPosition:hs.position,headingTop:parseFloat(hs.top),headingHeight:h.getBoundingClientRect().height,headingRect:h.getBoundingClientRect().toJSON(),cardHeight:parseFloat(getComputedStyle(card).height),layers:[...s.children].map(e=>({position:getComputedStyle(e).position,top:parseFloat(getComputedStyle(e).top)})),mode:s.dataset.stackMode}}""")
  if geometry['headingPosition']=='sticky':
   check(all(layer['position']!='sticky'or layer['top']>=geometry['headingTop']+geometry['headingHeight']+12 for layer in geometry['layers']),f'About heading overlaps sticky card at {width}x{height}: {geometry}')
  page.screenshot(path=str(OUT/f'about-{args.engine}-{width}x{height}.png'))
  rows.append({'width':width,'height':height,'about':geometry})
 # Real menu activation, including opening the containing disclosure first.
 page.set_viewport_size({'width':1440,'height':900});page.evaluate('scrollTo({top:0,behavior:"instant"})');page.wait_for_timeout(450)
 for target in ['services','masters','gifts','offers','about','faq','contacts']:
  page.mouse.wheel(0,-120);page.wait_for_timeout(400)
  link=page.locator(f'.site-header a[href="#{target}"],.site-header a[href="/#{target}"]').first
  if not link.is_visible():
   page.locator('.more-menu > summary').hover();page.wait_for_timeout(350)
  link.click();page.wait_for_timeout(1100)
  positions=[]
  for _ in range(8):
   positions.append(page.locator('#'+target).evaluate('e=>e.getBoundingClientRect().top'));page.wait_for_timeout(150)
  top=page.locator('#'+target).evaluate('e=>e.getBoundingClientRect().top')
  check(abs(top-100)<=8 or target=='contacts'and 0<=top<=110,f'menu target {target}: {top}')
  rows.append({'menuTarget':target,'top':top,'positions':positions,'hash':page.evaluate('location.hash')})
 check(not errors,f'page errors: {errors}')
 context.close();browser.close()
(OUT/f'runtime-{args.engine}.json').write_text(json.dumps({'origin':args.origin,'rows':rows,'failures':failures},ensure_ascii=False,indent=2),encoding='utf-8')
for error in failures:print('FAIL',error,flush=True)
assert not failures,failures
print('PASS',args.engine,len(rows),'normal/reduced loading, short-height About and real menu actions')
