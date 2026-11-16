import argparse,json,math
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/iteration66/works';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321');args=parser.parse_args();results=[]
def selected(page):return int(page.locator('.works-fan').get_attribute('data-work-index'))
def rest(page):page.wait_for_timeout(330)
def center(page):
 b=page.locator('[data-work-current=true]').bounding_box();return b['x']+b['width']/2,b['y']+b['height']/2
def expose(page):
 page.locator('#works').scroll_into_view_if_needed();page.wait_for_timeout(380)
def state(page):return page.locator('#works').evaluate('''e=>({index:+e.querySelector('.works-fan').dataset.workIndex,current:e.querySelectorAll('[data-work-current=true]').length,cards:e.querySelectorAll('[data-work-card]').length,visible:[...e.querySelectorAll('[data-work-card]')].filter(c=>getComputedStyle(c).visibility==='visible'&&+getComputedStyle(c).opacity>.1).length,author:e.querySelector('[data-work-author]').textContent,expected:e.querySelector('[data-work-current=true]').dataset.workMaster,count:e.querySelector('output').textContent,active:[...e.querySelectorAll('.rail-progress span')].findIndex(s=>s.dataset.current==='true'),overflow:document.documentElement.scrollWidth>innerWidth+1,dialog:document.querySelector('#works-photo-dialog').open,animations:[...e.querySelectorAll('[data-work-card]')].reduce((n,c)=>n+c.getAnimations().length,0)})''')
def assert_state(page,index):
 s=state(page);assert s['index']==index and s['active']==index and s['current']==1 and s['cards']==12 and s['author']==s['expected']and not s['overflow'],s;return s
with sync_playwright()as p:
 browser=p.chromium.launch(channel='chrome')
 context=browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)));page.goto(args.origin,wait_until='domcontentloaded');expose(page)
 next_button=page.locator('[data-rail-controls=works-fan] [data-rail-step="1"]')
 for turn in range(24):next_button.click();rest(page);assert_state(page,(turn+1)%12)
 results.append({'case':'24 real pointer cyclic selections','state':state(page)})
 next_button.click();page.wait_for_timeout(45);next_button.click();page.wait_for_timeout(45);page.locator('#works').screenshot(path=str(OUT/'motion-interrupted-midpoint.png'));next_button.click();rest(page);assert_state(page,3)
 results.append({'case':'rapid interrupted selection x3','state':state(page)})
 # Hit-test an exposed part of a neighbour, rather than clicking through the center card.
 neighbour=page.locator('[data-work-card]').nth(4)
 point=neighbour.evaluate('''e=>{const b=e.getBoundingClientRect();for(let y=b.top+20;y<b.bottom;y+=20)for(let x=b.left+10;x<b.right;x+=10)if(document.elementFromPoint(x,y)?.closest('[data-work-card]')===e)return{x,y};throw Error('No exposed neighbour point')}''');page.mouse.click(point['x'],point['y']);rest(page);assert_state(page,4);assert not page.locator('#works-photo-dialog').evaluate('e=>e.open')
 page.locator('[data-work-current=true]').click();page.wait_for_function('document.querySelector("#works-photo-dialog").open');page.wait_for_function('document.querySelector("[data-work-photo]").naturalWidth>0');page.locator('#works-photo-dialog').screenshot(path=str(OUT/'photo-dialog.png'));page.keyboard.press('Escape');page.wait_for_function('!document.querySelector("#works-photo-dialog").open');assert page.locator('[data-work-current=true]').evaluate('e=>e===document.activeElement')
 results.append({'case':'neighbour selects once; center opens one dialog, Escape returns focus','state':state(page)})
 page.keyboard.press('ArrowRight');assert_state(page,5);assert state(page)['animations']==0
 page.keyboard.press('Home');assert_state(page,0);page.keyboard.press('End');assert_state(page,11)
 results.append({'case':'keyboard Arrow/Home/End is immediate','state':state(page)})
 x,y=center(page);page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-130,y+2,steps=12);page.wait_for_timeout(60);page.locator('#works').screenshot(path=str(OUT/'mouse-held.png'));assert selected(page)==11;page.mouse.up();rest(page);assert_state(page,0);assert not state(page)['dialog']
 x,y=center(page);page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-90,y,steps=8);page.keyboard.press('Escape');page.mouse.up();rest(page);assert_state(page,0);assert not state(page)['dialog']
 results.append({'case':'real mouse drag/release and keyboard cancellation suppress click','state':state(page)})
 next_button.click();page.wait_for_timeout(45);page.evaluate('scrollTo({top:0,behavior:"instant"})');page.wait_for_timeout(200);assert state(page)['animations']==0;expose(page);assert_state(page,1)
 results.append({'case':'offscreen stops effects and retains selected card','state':state(page)});assert not errors,errors;context.close()
 for theme in ['light','dark']:
  context=browser.new_context(viewport={'width':1207,'height':900},color_scheme=theme,reduced_motion='reduce');page=context.new_page();page.goto(args.origin,wait_until='domcontentloaded')
  for width,height,scale in [(1440,900,1),(1207,900,1),(961,500,1),(900,700,1),(600,800,1),(390,844,1),(320,600,1),(390,600,2),(320,600,2)]:
   page.set_viewport_size({'width':width,'height':height});page.evaluate('''scale=>{const es=[...document.querySelectorAll('#works h2 span span,#works .works-caption h3,#works .works-caption p,#works output')];es.forEach(e=>e.style.removeProperty('font-size'));if(scale===2){const sizes=es.map(e=>parseFloat(getComputedStyle(e).fontSize)*2);es.forEach((e,i)=>e.style.fontSize=sizes[i]+'px')}}''',scale);expose(page);s=assert_state(page,0);assert s['visible']==(5 if width<=600 else 7),s;assert s['animations']==0,s
   photo_box=page.locator('[data-work-current=true]').bounding_box();fan_box=page.locator('.works-fan').bounding_box();assert abs(photo_box['x']+photo_box['width']/2-(fan_box['x']+fan_box['width']/2))<1,(photo_box,fan_box)
   if width in [1207,390,320]:page.locator('#works').screenshot(path=str(OUT/f'{theme}-{width}-text{scale*100}.png'))
   results.append({'case':'layout','theme':theme,'width':width,'height':height,'text':scale,'state':s})
  page.locator('[data-rail-controls=works-fan] [data-rail-step="1"]').click();assert_state(page,1);assert state(page)['animations']==0;context.close()
 context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);page=context.new_page();page.goto(args.origin,wait_until='domcontentloaded');expose(page);cdp=context.new_cdp_session(page);x,y=center(page)
 def touch(points,kind):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':points})
 touch([{'x':x,'y':y,'id':1}],'touchStart')
 for step in range(1,11):touch([{'x':x-120*step/10,'y':y,'id':1}],'touchMove');page.wait_for_timeout(16)
 touch([],'touchEnd');rest(page);assert_state(page,1);assert not state(page)['dialog']
 x,y=center(page);touch([{'x':x,'y':y,'id':1}],'touchStart');touch([{'x':x-70,'y':y,'id':1}],'touchMove');touch([],'touchCancel');rest(page);assert_state(page,1)
 before=page.evaluate('scrollY');x,y=center(page);touch([{'x':x,'y':y,'id':1}],'touchStart')
 for step in range(1,11):touch([{'x':x,'y':y-150*step/10,'id':1}],'touchMove');page.wait_for_timeout(16)
 touch([],'touchEnd');page.wait_for_timeout(400);after=page.evaluate('scrollY');assert after>before+40,(before,after);assert selected(page)==1
 expose(page);x,y=center(page);before_scale=page.evaluate('visualViewport.scale');touch([{'x':x-35,'y':y,'id':1},{'x':x+35,'y':y,'id':2}],'touchStart')
 for step in range(1,9):touch([{'x':x-35-step*6,'y':y,'id':1},{'x':x+35+step*6,'y':y,'id':2}],'touchMove');page.wait_for_timeout(18)
 touch([],'touchEnd');page.wait_for_timeout(200);after_scale=page.evaluate('visualViewport.scale');assert after_scale>before_scale+.1,(before_scale,after_scale);assert selected(page)==1
 results.append({'case':'real CDP touch swipe/cancel, vertical chain, pinch','scroll':[before,after],'scale':[before_scale,after_scale],'state':state(page)});context.close();browser.close()
(OUT/'verification.json').write_text(json.dumps({'cases':results,'pageerrors':errors},ensure_ascii=False,indent=2),encoding='utf8');print('PASS',len(results),'Works checks:24cycles,interruption,mouse,touch/pinch,dialog,keyboard,18layouts,both/reduced/text200')
