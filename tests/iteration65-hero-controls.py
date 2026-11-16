"""Hero uses the shared controls without changing the compact video-only contract."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321');parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');args=parser.parse_args();OUT=ROOT/'tmp/planning/iteration65/hero-controls';OUT.mkdir(parents=True,exist_ok=True)
feed=json.loads((ROOT/'public/data/news.json').read_text(encoding='utf-8'));feed['generatedAt']=datetime.now(timezone.utc).isoformat()
# Existing local photos and text; fixture ids are isolated from the current moderation policy.
for i,item in enumerate(feed['items']):item['id']=str(9000+i);item['url']='https://vk.ru/wall-210007626_'+item['id']
rows=[];errors=[]
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 def setup(width,height,theme,motion='reduce',clock=False):
  ctx=browser.new_context(viewport={'width':width,'height':height},color_scheme=theme,reduced_motion=motion);ctx.add_init_script('localStorage.setItem("soyuz_theme",'+json.dumps(theme)+')');ctx.route('https://raw.githubusercontent.com/**',lambda r:r.abort());ctx.route(args.origin+'/data/news.json',lambda r:r.fulfill(json=feed));page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  if clock:page.clock.install()
  requests=[];page.on('request',lambda r:requests.append(r.url));page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');return ctx,page,requests
 def active(page,index):page.wait_for_function('(i)=>document.querySelector(".hero-slide[data-hero-active=true]")?.dataset.newsId===String(9000+i)',arg=index)
 for width,height in [(961,600),(1024,600),(1280,720),(1440,900),(1920,1080)]:
  for theme in ['light','dark']:
   for motion in ['reduce','no-preference']:
    ctx,page,requests=setup(width,height,theme,motion);compact=page.evaluate("matchMedia('(max-width:960px)').matches")
    if compact:
     assert page.locator('.hero-scene .rail-controls').is_hidden();assert page.locator('.hero-slide').count()==1;assert not any('/data/news.json'in u or'raw.githubusercontent.com'in u for u in requests);rows.append({'width':width,'height':height,'theme':theme,'motion':motion,'compact':True});ctx.close();continue
    page.wait_for_selector('.hero-scene[data-news-state=ready]');page.wait_for_function('''()=>{const e=document.querySelector('.hero-slide[data-hero-active=true]'),i=e?.querySelector('.hero-photo');return i?.naturalWidth>100&&i.currentSrc.includes('/media/news/')&&e.getAttribute('aria-busy')!=='true'}''');page.mouse.move(width-2,2);page.wait_for_timeout(300)
    assert page.locator('.hero-edge,.hero-dot,.hero-news-panel .rail-controls').count()==0
    assert page.locator('.hero-news-state').is_hidden()
    geometry=page.locator('.hero-scene').evaluate('''e=>{const r=e.getBoundingClientRect(),m=e.querySelector('.hero-media').getBoundingClientRect(),c=e.querySelector('.rail-controls').getBoundingClientRect(),o=e.querySelector('output').getBoundingClientRect(),b=[...e.querySelectorAll('[data-rail-step]')].map(x=>x.getBoundingClientRect().toJSON());return{scene:r.toJSON(),media:m.toJSON(),controls:c.toJSON(),counter:o.toJSON(),buttons:b,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth}}''')
    assert abs(geometry['scene']['height']-710)<1 and abs(geometry['media']['height']-654)<1,geometry
    assert geometry['media']['bottom']+7<=geometry['controls']['top'] and geometry['controls']['bottom']<=geometry['scene']['bottom']+1,geometry
    assert geometry['counter']['left']<geometry['buttons'][0]['left']<geometry['buttons'][1]['left'] and geometry['scrollWidth']<=geometry['clientWidth']+1,geometry
    assert all(b['width']>=44 and b['height']>=44 for b in geometry['buttons']),geometry
    panel=page.locator('.hero-news-panel');assert page.locator('.hero-news-action').evaluate('e=>e.getBoundingClientRect().height')<1
    panel.hover();page.wait_for_timeout(300);assert page.locator('.hero-news-action').evaluate('e=>e.getBoundingClientRect().height')>=44
    page.locator('.hero-scene').evaluate('e=>scrollTo({top:e.getBoundingClientRect().bottom+scrollY-innerHeight+24,behavior:"instant"})');page.mouse.move(width-2,2);page.wait_for_timeout(300);page.screenshot(path=str(OUT/f'{args.engine}-{width}x{height}-{theme}-{motion}.png'))
    next=page.locator('.hero-scene [data-rail-step="1"]');prev=page.locator('.hero-scene [data-rail-step="-1"]');prev.click();active(page,9);next.click();active(page,0)
    page.locator('.hero-rail').focus();page.keyboard.press('ArrowRight');active(page,1);assert page.locator('.hero-scene output').inner_text()=='02 / 10';assert page.locator('.hero-scene .rail-progress [data-current=true]').count()==1
    tone=panel.get_attribute('data-news-tone');surface=panel.get_attribute('data-selection-surface');assert tone==surface=='blue';assert panel.evaluate('e=>getComputedStyle(e).backdropFilter')=='none'
    page.wait_for_function('document.querySelector(".hero-scene").dataset.heroPaused==="true"');rows.append({'width':width,'height':height,'theme':theme,'motion':motion,'compact':False,'geometry':geometry});ctx.close()
 # All actual images, coloured surfaces and complete cyclic order share the same index.
 ctx,page,_=setup(1440,1080,'dark');page.wait_for_selector('.hero-scene[data-news-state=ready]');tones=[]
 for i in range(10):
  active(page,i)
  if feed['items'][i]['image']:page.wait_for_function('''()=>{const e=document.querySelector('.hero-slide[data-hero-active=true]'),i=e?.querySelector('.hero-photo');return i?.naturalWidth>100&&i.currentSrc.includes('/media/news/')&&e.getAttribute('aria-busy')!=='true'}''')
  else:assert page.locator('.hero-slide[data-hero-active=true] .hero-photo').count()==0
  panel=page.locator('.hero-news-panel');tones.append(panel.get_attribute('data-news-tone'));assert panel.get_attribute('data-selection-surface')==tones[-1];assert ' '.join(page.locator('.hero-scene output').inner_text().split())==f'{i+1:02d} / 10',(i,repr(page.locator('.hero-scene output').inner_text()));assert page.locator('.hero-news-link').get_attribute('href')==feed['items'][i]['url'];page.locator('.hero-scene [data-rail-step="1"]').click()
 active(page,0);assert set(tones)=={'red','blue','yellow'} and all(tones[i]!=tones[(i+1)%10] for i in range(10))
 rail=page.locator('.hero-rail');r=rail.bounding_box();x=r['x']+r['width']*.75;y=r['y']+r['height']*.2
 page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-r['width']*.45,y,steps=8);page.mouse.up();active(page,1)
 page.mouse.move(x-r['width']*.45,y);page.mouse.down();page.mouse.move(x,y,steps=8);page.mouse.up();active(page,0)
 page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-30,y,steps=4);rail.dispatch_event('pointercancel',{'pointerId':1,'pointerType':'mouse','isPrimary':True,'button':0});page.mouse.up();active(page,0);ctx.close()
 # Compact screens request no news or post images and have no redundant controls.
 for width in [390,960]:
  for theme in ['light','dark']:
   ctx,page,requests=setup(width,844,theme);page.wait_for_timeout(150);assert page.locator('.hero-scene .rail-controls').is_hidden();assert page.locator('.hero-slide').count()==1;assert not any('/data/news.json'in u or'/media/news/'in u or'raw.githubusercontent.com'in u for u in requests);ctx.close()
 # One timer, mouse/focus pause, Space resume after a manual selection, and offscreen suspension.
 ctx,page,_=setup(1440,1080,'light','no-preference',True);page.wait_for_selector('.hero-scene[data-news-state=ready]');page.mouse.move(1438,2);page.clock.fast_forward(6200);active(page,1);page.locator('.hero-rail').focus();page.keyboard.press('ArrowRight');active(page,2);page.clock.fast_forward(6200);active(page,2);page.keyboard.press('Space');page.clock.fast_forward(6200);active(page,3);page.keyboard.press('Space');page.clock.fast_forward(6200);active(page,3);ctx.close()
 browser.close()
assert not errors,errors
(OUT/f'{args.engine}.json').write_text(json.dumps({'engine':args.engine,'rows':rows,'multiImageTones':tones,'pageErrors':errors,'compactCases':4,'playbackCase':True},ensure_ascii=False,indent=2),encoding='utf-8');print('PASS',args.engine,len(rows),'layout states +10 images +4 compact +playback, no pageerrors')
