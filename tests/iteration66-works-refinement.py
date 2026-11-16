"""Real browser checks for the revised fan; never overwrite the earlier 25-case evidence."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321');parser.add_argument('--label',default='candidate');args=parser.parse_args()
OUT=ROOT/'artifacts/iteration66/works-refinement'/args.label;OUT.mkdir(parents=True,exist_ok=True);results=[];errors=[]
def state(page):return page.locator('#works').evaluate('''e=>{const fan=e.querySelector('.works-fan'),card=e.querySelector('[data-work-current=true]');return{index:+fan.dataset.workIndex,position:+fan.dataset.workPosition,target:+fan.dataset.workTarget,moving:fan.dataset.workMoving==='true',id:card.dataset.workId,slot:+card.dataset.workSlot,master:e.querySelector('[data-work-author]').textContent,caption:e.querySelector('.works-caption [data-work-caption]').textContent,expectedMaster:card.dataset.workMaster,expectedCaption:card.dataset.workCaption,total:e.querySelectorAll('[data-work-card]').length,count:e.querySelector('[data-work-count]').textContent,dialog:e.querySelector('dialog').open,overflow:document.documentElement.scrollWidth>innerWidth+1,visible:[...e.querySelectorAll('[data-work-card]')].filter(c=>getComputedStyle(c).visibility==='visible'&&+getComputedStyle(c).opacity>.01).length}}''')
def verify(page,index=None):
 s=state(page);normal=lambda text:' '.join(text.split());assert s['index']==s['slot']and normal(s['master'])==normal(s['expectedMaster'])and normal(s['caption'])==normal(s['expectedCaption'])and not s['overflow'],s
 if index is not None:assert s['index']==index,s
 assert s['count']==f"{s['index']+1} / {s['total']}",s
 return s
def rest(page):page.wait_for_function('document.querySelector(".works-fan").dataset.workMoving!=="true"',timeout=3500)
def expose(page):page.locator('#works').scroll_into_view_if_needed();page.wait_for_timeout(350)
def point(page):
 b=page.locator('[data-work-current=true]').bounding_box();return b['x']+b['width']/2,b['y']+b['height']/2
def fresh(browser,**options):
 c=browser.new_context(**options);c.add_init_script('''window.__workSounds=[];HTMLMediaElement.prototype.play=function(){if(this.src.includes('/audio/'))window.__workSounds.push(this.src);return Promise.resolve()};navigator.vibrate=pattern=>{(window.__workVibrations??=[]).push(pattern);return true}''');p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.goto(args.origin,wait_until='domcontentloaded');expose(p);return c,p
with sync_playwright()as p:
 browser=p.chromium.launch(channel='chrome');context,page=fresh(browser,viewport={'width':1440,'height':1000});total=state(page)['total'];next_button=page.locator('[data-work-step="1"]')
 order=page.locator('[data-work-card]').evaluate_all('cs=>cs.map(c=>({id:c.dataset.workId,slot:+c.dataset.workSlot}))');assert len({x['slot']for x in order})==total
 seen=[]
 for turn in range(total*2):
  seen.append(verify(page,turn%total)['id']);next_button.click();rest(page)
 assert len(set(seen[:total]))==total and seen[:total]==seen[total:]
 results.append({'case':'two complete pointer cycles without repeats','total':total,'order':order,'state':verify(page,0)})
 # All geometry is CSS-owned; side fill is fully opaque and center fill is clear.
 geometry=page.locator('#works').evaluate('''e=>{const fan=e.querySelector('.works-fan').getBoundingClientRect(),cards=[...e.querySelectorAll('[data-work-card]')].filter(c=>+c.dataset.workDistance<=3),boxes=cards.map(c=>c.getBoundingClientRect()),center=e.querySelector('[data-work-current=true]');return{fan:fan.toJSON(),left:Math.min(...boxes.map(b=>b.left)),right:Math.max(...boxes.map(b=>b.right)),tints:cards.map(c=>({distance:+c.dataset.workDistance,alpha:+getComputedStyle(c.querySelector('.work-tint')).opacity,tone:c.dataset.workTone})),center:center.getBoundingClientRect().toJSON(),controls:e.querySelector('[data-work-controls]').getBoundingClientRect().toJSON(),oldRails:e.querySelectorAll('[data-rail-controls],.rail-progress').length}}''')
 assert abs(geometry['left']-geometry['fan']['left'])<20 and abs(geometry['right']-geometry['fan']['right'])<20,geometry
 assert geometry['oldRails']==0 and all(x['alpha']==(0 if x['distance']==0 else 1)for x in geometry['tints']if x['distance']in[0,3]),geometry
 page.locator('#works').screenshot(path=str(OUT/'desktop-initial.png'));results.append({'case':'full shell spread, center and opaque side tints, centered controls','geometry':geometry})
 start=verify(page)['position'];sounds=page.evaluate('window.__workSounds.length');x,y=point(page);page.mouse.move(x,y);page.mouse.down();held=[]
 for step in range(1,31):
  page.mouse.move(x-step*14,y+1);page.wait_for_timeout(16)
  if step%5==0:held.append(verify(page))
 assert len({s['index']for s in held})>=3 and abs(held[-1]['position']-start)>2,held
 assert page.evaluate('window.__workSounds.length')==sounds
 page.screenshot(path=str(OUT/'held-multiple.png'));page.mouse.up();rest(page);assert page.evaluate('window.__workSounds.length')==sounds+1,(sounds,page.evaluate('window.__workSounds'));assert not verify(page)['dialog']
 results.append({'case':'one held drag traverses multiple cards before release; one accepted feedback','held':held,'state':verify(page)})
 # Reversing an interrupted spring starts at its visible fractional position.
 next_button.click();page.wait_for_timeout(45);before=verify(page)['position'];x,y=point(page);page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+20,y);page.wait_for_timeout(20);after=verify(page)['position'];assert abs(after-before)<.8,(before,after)
 page.mouse.move(x+240,y,steps=16);page.wait_for_timeout(25);page.screenshot(path=str(OUT/'interrupted-reverse.png'));page.keyboard.press('Escape');page.mouse.up();rest(page);assert not verify(page)['dialog'];results.append({'case':'interrupted visible pose, held reversal and cancelled release','before':before,'after':after,'state':verify(page)})
 # Keyboard never schedules spring frames.
 page.locator('[data-work-current=true]').focus();page.keyboard.press('Home');assert not verify(page,0)['moving'];page.keyboard.press('End');assert not verify(page,total-1)['moving'];page.keyboard.press('ArrowRight');assert not verify(page,0)['moving']
 results.append({'case':'keyboard Home/End/Arrow is immediate','state':verify(page)})
 neighbour=page.locator('[data-work-slot="1"]');q=neighbour.evaluate('''e=>{const b=e.getBoundingClientRect();for(let y=b.top+20;y<b.bottom;y+=15)for(let x=b.left+5;x<b.right;x+=8)if(document.elementFromPoint(x,y)?.closest('[data-work-card]')===e)return{x,y};throw Error('No exposed neighbour')}''');page.mouse.click(q['x'],q['y']);rest(page);verify(page,1);assert not state(page)['dialog'];page.locator('[data-work-current=true]').click();page.wait_for_function('document.querySelector("#works-photo-dialog").open&&document.querySelector("[data-work-photo]").naturalWidth>0');page.locator('#works-photo-dialog').screenshot(path=str(OUT/'photo-dialog.png'));page.keyboard.press('Escape');page.wait_for_function('!document.querySelector("#works-photo-dialog").open');assert page.locator('[data-work-current=true]').evaluate('e=>e===document.activeElement');results.append({'case':'neighbour selects, center opens one image, Escape restores focus','state':verify(page)})
 next_button.click();page.wait_for_timeout(35);page.evaluate('scrollTo({top:0,behavior:"instant"})');page.wait_for_timeout(180);assert not state(page)['moving'];expose(page);a=state(page)['position'];page.wait_for_timeout(350);assert state(page)['position']==a;results.append({'case':'offscreen stops the spring and resting fan is idle','state':verify(page)});context.close()
 for theme in ['light','dark']:
  context,page=fresh(browser,viewport={'width':1440,'height':900},color_scheme=theme,reduced_motion='reduce')
  for width,height,scale in [(1440,900,1),(1207,900,1),(961,500,1),(900,700,1),(600,800,1),(390,844,1),(320,600,1),(390,600,2),(320,600,2)]:
   page.set_viewport_size({'width':width,'height':height});page.evaluate('''scale=>{const es=[...document.querySelectorAll('#works h2 span span,#works .works-caption h3,#works .works-caption p,#works output')];es.forEach(e=>e.style.removeProperty('font-size'));if(scale===2){const sizes=es.map(e=>parseFloat(getComputedStyle(e).fontSize)*2);es.forEach((e,i)=>e.style.fontSize=sizes[i]+'px')}}''',scale);expose(page);s=verify(page,0);assert s['visible']==(5 if width<=600 else 7),s;assert not s['moving']
   bounds=page.locator('[data-work-controls]').evaluate('''e=>({r:e.getBoundingClientRect().toJSON(),buttons:[...e.querySelectorAll('button')].map(b=>b.getBoundingClientRect().toJSON())})''');assert all(b['height']>=44 and b['width']>=44 for b in bounds['buttons']),bounds
   if width in[1207,390,320]:page.locator('#works').screenshot(path=str(OUT/f'{theme}-{width}-text{scale*100}.png'))
   results.append({'case':'layout','theme':theme,'width':width,'height':height,'text':scale,'state':s})
  page.locator('[data-work-step="1"]').click();assert not verify(page,1)['moving'];context.close()
 context,page=fresh(browser,viewport={'width':390,'height':844},is_mobile=True,has_touch=True);cdp=context.new_cdp_session(page);x,y=point(page)
 def touch(points,kind):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':points})
 sound=page.evaluate('window.__workSounds.length');touch([{'x':x,'y':y,'id':1}],'touchStart')
 for step in range(1,13):touch([{'x':x-125*step/12,'y':y,'id':1}],'touchMove');page.wait_for_timeout(16)
 assert state(page)['index']>=1;touch([],'touchEnd');rest(page);assert page.evaluate('window.__workSounds.length')==sound+1;index=state(page)['index'];x,y=point(page);touch([{'x':x,'y':y,'id':1}],'touchStart');touch([{'x':x-20,'y':y,'id':1}],'touchMove');touch([],'touchCancel');rest(page);assert not state(page)['dialog']
 before=page.evaluate('scrollY');x,y=point(page);touch([{'x':x,'y':y,'id':1}],'touchStart')
 for step in range(1,11):touch([{'x':x,'y':y-150*step/10,'id':1}],'touchMove');page.wait_for_timeout(16)
 touch([],'touchEnd');page.wait_for_timeout(300);after=page.evaluate('scrollY');assert after>before+40,(before,after)
 expose(page);x,y=point(page);before_scale=page.evaluate('visualViewport.scale');touch([{'x':x-35,'y':y,'id':1},{'x':x+35,'y':y,'id':2}],'touchStart')
 for step in range(1,9):touch([{'x':x-35-step*6,'y':y,'id':1},{'x':x+35+step*6,'y':y,'id':2}],'touchMove');page.wait_for_timeout(18)
 touch([],'touchEnd');page.wait_for_timeout(150);after_scale=page.evaluate('visualViewport.scale');assert after_scale>before_scale+.1,(before_scale,after_scale);results.append({'case':'real touch multi-selection/cancel, one feedback, vertical scroll and pinch','scroll':[before,after],'scale':[before_scale,after_scale],'state':verify(page)});context.close()
 context=browser.new_context(viewport={'width':390,'height':844},java_script_enabled=False);page=context.new_page();page.goto(args.origin,wait_until='domcontentloaded');page.locator('#works').scroll_into_view_if_needed();assert not page.locator('[data-work-controls]').is_visible();assert page.locator('.works-fallback a').count()==total;assert page.locator('[data-work-current=true]').get_attribute('href');results.append({'case':'no-JS image links and complete fallback list','total':total});context.close();browser.close()
assert not errors,errors
(OUT/'verification.json').write_text(json.dumps({'cases':results,'pageerrors':errors},ensure_ascii=False,indent=2),encoding='utf8');print('PASS',len(results),'revised Works groups; pageerrors',len(errors))
