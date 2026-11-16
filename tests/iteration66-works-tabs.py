"""Current portrait-only selection/filter contract. Earlier Works evidence stays separate."""
import argparse,hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321');parser.add_argument('--label',default='portrait');args=parser.parse_args()
OUT=ROOT/'artifacts/iteration66/works-tabs'/args.label;OUT.mkdir(parents=True,exist_ok=True);results=[];errors=[]
SOURCE=['src/components/Works.astro','src/styles/works.css','src/scripts/works.ts','src/scripts/works-layout.ts','src/config/headlines.ts','src/content/works.ts','content/work-photos.json','src/styles/interactions.css','src/styles/service-deck.css','src/scripts/feedback.ts']
def hashes():return{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()for f in SOURCE}
before_hashes=hashes()
def state(page):return page.locator('#works').evaluate('''e=>{const f=e.querySelector('.works-fan'),c=e.querySelector('[data-work-current=true]'),all=[...e.querySelectorAll('[data-work-card]')],m=e.querySelector('[data-work-master-tab][aria-selected=true]').dataset.workMasterTab,cs=all.filter(c=>m==='all'||c.dataset.workMasterId===m);return{index:+f.dataset.workIndex,position:+f.dataset.workPosition,target:+f.dataset.workTarget,moving:f.dataset.workMoving==='true',total:cs.length,id:c?.dataset.workId,master:e.querySelector('[data-work-author]').textContent,caption:e.querySelector('.works-caption [data-work-caption]').textContent,expectedMaster:c?.dataset.workMaster??'',expectedCaption:c?.dataset.workCaption??'',count:e.querySelector('output').textContent,empty:!e.querySelector('[data-work-empty]').hidden,visible:cs.filter(c=>!c.hidden&&getComputedStyle(c).visibility==='visible'&&+getComputedStyle(c).opacity>.01).length,overlay:getComputedStyle(f,'::before').content!=='none',fading:cs.filter(c=>!c.hidden&&getComputedStyle(c).visibility==='visible'&&+getComputedStyle(c).opacity>0&&+getComputedStyle(c).opacity<.99).length,overflow:document.documentElement.scrollWidth>innerWidth+1,dialogs:e.querySelectorAll('dialog').length,links:e.querySelectorAll('a[href]').length}}''')
def verify(page,index=None):
 s=state(page);normal=lambda text:' '.join(text.split());assert normal(s['master'])==normal(s['expectedMaster'])and normal(s['caption'])==normal(s['expectedCaption'])and not s['overflow']and s['dialogs']==s['links']==0,s
 assert s['count']==f"{s['index']+1} / {s['total']}",s
 if index is not None:assert s['index']==index,s
 return s
def rest(page):page.wait_for_function('document.querySelector(".works-fan").dataset.workMoving!=="true"',timeout=3500);page.wait_for_timeout(200)
def expose(page):page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(300)
def center(page):
 r=page.locator('[data-work-current=true]').bounding_box();return r['x']+r['width']/2,r['y']+r['height']/2
def choose(page,value):
 page.locator(f'[data-work-master-tab="{value}"]').click();page.wait_for_timeout(100);return verify(page)
def fresh(browser,**options):
 c=browser.new_context(**options);c.add_init_script('''window.__sounds=[];window.__vibrations=[];HTMLMediaElement.prototype.play=function(){if(this.src.includes('/audio/'))window.__sounds.push(this.src);return Promise.resolve()};navigator.vibrate=p=>{if(Array.isArray(p)&&p.some(n=>n>0))window.__vibrations.push(p);return true}''');page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(args.origin,wait_until='domcontentloaded');expose(page);return c,page
with sync_playwright()as p:
 b=p.chromium.launch(channel='chrome');context,page=fresh(b,viewport={'width':1440,'height':1000});total=state(page)['total'];next_button=page.locator('[data-work-step="1"]');seen=[]
 for turn in range(total*2):seen.append(verify(page,turn%total)['id']);next_button.click();rest(page)
 assert len(set(seen[:total]))==total and seen[:total]==seen[total:];results.append({'case':'two complete randomized logical cycles without repeats','state':verify(page,0),'order':seen[:total]})
 before_url=page.url;before_pages=len(context.pages);sound=page.evaluate('window.__sounds.length');page.locator('[data-work-current=true]').click();page.wait_for_timeout(100);assert page.url==before_url and len(context.pages)==before_pages and page.evaluate('window.__sounds.length')==sound;verify(page,0);results.append({'case':'selected card stays selection-only without original URL or dialog'})
 neighbour=page.locator('[data-work-slot="1"]');q=neighbour.evaluate('''e=>{const b=e.getBoundingClientRect();for(let y=Math.max(100,b.top+10);y<Math.min(innerHeight-80,b.bottom);y+=12)for(let x=b.left+4;x<b.right;x+=7)if(document.elementFromPoint(x,y)?.closest('[data-work-card]')===e)return{x,y};throw Error('No exposed neighbour')}''');page.mouse.click(q['x'],q['y']);rest(page);verify(page,1);results.append({'case':'exposed neighbour selects without navigation','state':state(page)})
 page.locator('[data-work-current=true]').focus();page.keyboard.press('Home');verify(page,0);page.keyboard.press('End');assert not verify(page,total-1)['moving'];page.keyboard.press('ArrowRight');assert not verify(page,0)['moving'];results.append({'case':'keyboard Home/End/Arrow is immediate'})
 # Individual press scale belongs to the inner frame, not the translated outer button.
 page.locator('[data-work-current=true]').focus();page.keyboard.press('Home');expose(page);x,y=center(page)
 def press_state():return page.locator('[data-work-current=true]').evaluate("""e=>{const f=e.querySelector('[data-press-surface]'),r=e.getBoundingClientRect(),q=f.getBoundingClientRect();return{outer:r.toJSON(),frame:q.toJSON(),outerScale:getComputedStyle(e).scale,scale:getComputedStyle(f).scale}}""")
 base=press_state();page.mouse.move(x,y);page.mouse.down();page.wait_for_timeout(60);mid=press_state();page.screenshot(path=str(OUT/'press-mid.png'));page.wait_for_timeout(85);pressed=press_state();page.mouse.up();page.wait_for_timeout(160);released=press_state()
 for sample in[mid,pressed,released]:
  for dimension in['x','y','width','height']:assert abs(sample['outer'][dimension]-base['outer'][dimension])<.1,(base,sample)
  assert abs(sample['frame']['x']+sample['frame']['width']/2-(base['frame']['x']+base['frame']['width']/2))<.6,(base,sample)
  assert abs(sample['frame']['y']+sample['frame']['height']/2-(base['frame']['y']+base['frame']['height']/2))<.6,(base,sample)
 assert pressed['outerScale']=='none' and abs(pressed['frame']['width']/base['frame']['width']-.97)<.003 and abs(released['frame']['width']/base['frame']['width']-1)<.002
 results.append({'case':'centered inner-frame tactile press with stable outer hit area; intermediate/release samples','base':base,'mid':mid,'pressed':pressed,'released':released})
 x,y=center(page);sound=page.evaluate('window.__sounds.length');page.mouse.move(x,y);page.mouse.down();held=[]
 for step in range(1,31):
  page.mouse.move(x-step*13,y);page.wait_for_timeout(16)
  if step%5==0:held.append(verify(page))
 assert len({s['index']for s in held})>=3 and any(s['fading'] for s in held)and not any(s['overlay']for s in held),held;assert page.evaluate('window.__sounds.length')==sound;page.screenshot(path=str(OUT/'held.png'));page.mouse.up();rest(page);assert page.evaluate('window.__sounds.length')==sound+1 and verify(page)['overlay']==0;results.append({'case':'continuous held multi-selection, fading outgoing cards without overlays and one feedback','held':held,'state':state(page)})
 next_button.click();page.wait_for_timeout(40);before=state(page)['position'];x,y=center(page);page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+18,y);page.wait_for_timeout(20);after=state(page)['position'];assert abs(after-before)<.9,(before,after);page.mouse.move(x+170,y,steps=12);page.wait_for_timeout(30);page.screenshot(path=str(OUT/'reverse.png'));sound=page.evaluate('window.__sounds.length');page.keyboard.press('Escape');page.mouse.up();rest(page);assert page.evaluate('window.__sounds.length')==sound;results.append({'case':'visible-pose interruption/reversal and cancelled gesture without feedback','state':verify(page)})
 # Seven service-like tabs own one master filter; category metadata has no UI.
 tabs=page.locator('[data-work-master-tab]');assert tabs.count()==7;assert page.locator('#works select,#works .choice').count()==0
 service_before=page.locator('[data-sd-tab][aria-selected=true]').get_attribute('id')
 for value in['souz-sonya-kid','souz-sofya-shalaginova','souz-darya','souz-milena','souz-lyubov','souz-svetlana']:
  plays=page.evaluate('window.__sounds.filter(s=>s.endsWith("/select.wav")).length');s=choose(page,value);assert s['total']>0;assert page.locator('[data-work-card]:not([hidden])').evaluate_all('(cs,value)=>cs.every(c=>c.dataset.workMasterId===value)',value);assert page.evaluate('window.__sounds.filter(s=>s.endsWith("/select.wav")).length')==plays+1
  assert page.locator('.works-fan').get_attribute('aria-labelledby')==page.locator(f'[data-work-master-tab="{value}"]').get_attribute('id');results.append({'case':'master tab','masterId':value,'state':s})
  if s['total']==2:
   first=s['id'];next_button.click();rest(page);assert verify(page)['id']!=first
 tabs.last.focus();page.keyboard.press('Home');verify(page);assert tabs.first.get_attribute('aria-selected')=='true';page.wait_for_timeout(60);page.keyboard.press('End');assert tabs.last.get_attribute('aria-selected')=='true';page.keyboard.press('ArrowRight');assert tabs.first.get_attribute('aria-selected')=='true';assert page.locator('[data-work-master-tab][tabindex="0"]').count()==1;assert page.locator('[data-sd-tab][aria-selected=true]').get_attribute('id')==service_before
 results.append({'case':'tab keyboard Home/End/wrap, roving focus and service selection isolation','state':verify(page)});context.close()
 for theme in['light','dark']:
  context,page=fresh(b,viewport={'width':1440,'height':1000},color_scheme=theme,reduced_motion='reduce')
  for width,height,scale in[(1920,1080,1),(1440,900,1),(1207,900,1),(961,500,1),(960,700,1),(600,800,1),(421,844,1),(420,844,1),(390,844,1),(320,600,1),(390,600,2),(320,600,2)]:
   page.set_viewport_size({'width':width,'height':height});page.evaluate('''scale=>{const es=[...document.querySelectorAll('#works h2 span span,#works .works-caption h3,#works .works-caption p,#works output,#works [data-work-master-tab],#works [data-work-reset],#works .works-empty p')];es.forEach(e=>e.style.removeProperty('font-size'));if(scale===2){const fs=es.map(e=>parseFloat(getComputedStyle(e).fontSize)*2);es.forEach((e,i)=>e.style.fontSize=fs[i]+'px')}}''',scale);expose(page);s=verify(page,0);assert s['visible']==(9 if width>=961 else 5 if width>=421 else 3),s;assert s['overlay']==0 and not s['moving']
   geometry=page.locator('#works').evaluate('''e=>{const f=e.querySelector('.works-fan'),r=f.getBoundingClientRect(),cs=[...e.querySelectorAll('[data-work-card]')].filter(c=>!c.hidden&&getComputedStyle(c).visibility==='visible'&&+getComputedStyle(c).opacity>.01),center=e.querySelector('[data-work-current=true]').getBoundingClientRect(),heading=e.querySelector(innerWidth<=600?'.headline-mobile':innerWidth<=960?'.headline-tablet':'.headline-desktop');return{cuts:cs.map(c=>c.getBoundingClientRect()).filter(b=>b.left<r.left-1||b.right>r.right+1||b.top<r.top-1||b.bottom>r.bottom+1).length,ratios:cs.map(c=>c.offsetWidth/c.offsetHeight),borders:cs.map(c=>({width:parseFloat(getComputedStyle(c).borderTopWidth),color:getComputedStyle(c).borderTopColor})),lower:cs.filter(c=>+c.dataset.workDistance>=1).every(c=>{const b=c.getBoundingClientRect();return b.top+b.height/2>center.top+center.height/2}),heading:[...heading.children].map(s=>({height:s.getBoundingClientRect().height,line:parseFloat(getComputedStyle(s).lineHeight),font:parseFloat(getComputedStyle(s).fontSize)})),buttons:[...e.querySelectorAll('[data-work-controls] button,[data-work-master-tab]')].map(c=>{const b=c.getBoundingClientRect();return{width:b.width,height:b.height,left:b.left,right:b.right,textWidth:c.scrollWidth,client:c.clientWidth}})}}''')
   assert geometry['cuts']==0 and all(abs(x-.75)<.006 for x in geometry['ratios']),geometry;assert geometry['lower'];assert all(x['width']==0 for x in geometry['borders']),geometry
   assert all(x['width']>=44 and x['height']>=44 and x['left']>=0 and x['right']<=width+1 for x in geometry['buttons']),geometry
   if scale==1:assert len(geometry['heading'])==2 and all(x['height']<=x['line']+1 for x in geometry['heading']),geometry
   if width in[1440,390,320]:page.locator('#works').screenshot(path=str(OUT/f'{theme}-{width}-text{scale*100}.png'))
   results.append({'case':'layout','theme':theme,'width':width,'height':height,'text':scale,'state':s,'geometry':geometry})
  context.close()
 context,page=fresh(b,viewport={'width':390,'height':844},is_mobile=True,has_touch=True);cdp=context.new_cdp_session(page);x,y=center(page)
 def touch(points,kind):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':points})
 sound=page.evaluate('window.__sounds.length');vibes=page.evaluate('window.__vibrations.length');touch([{'x':x,'y':y,'id':1}],'touchStart')
 for step in range(1,13):touch([{'x':x-125*step/12,'y':y,'id':1}],'touchMove');page.wait_for_timeout(16)
 assert page.evaluate('window.__sounds.length')==sound;touch([],'touchEnd');rest(page);assert page.evaluate('window.__sounds.length')==sound+1 and page.evaluate('window.__vibrations.length')==vibes+1;index=state(page)['index']
 x,y=center(page);touch([{'x':x,'y':y,'id':1}],'touchStart');touch([{'x':x-20,'y':y,'id':1}],'touchMove');touch([],'touchCancel');rest(page);assert page.evaluate('window.__sounds.length')==sound+1
 before=page.evaluate('scrollY');x,y=center(page);touch([{'x':x,'y':y,'id':1}],'touchStart')
 for step in range(1,11):touch([{'x':x,'y':y-150*step/10,'id':1}],'touchMove');page.wait_for_timeout(16)
 touch([],'touchEnd');page.wait_for_timeout(300);after=page.evaluate('scrollY');assert after>before+40,(before,after);expose(page);x,y=center(page);scale0=page.evaluate('visualViewport.scale');touch([{'x':x-30,'y':y,'id':1},{'x':x+30,'y':y,'id':2}],'touchStart')
 for step in range(1,9):touch([{'x':x-30-step*6,'y':y,'id':1},{'x':x+30+step*6,'y':y,'id':2}],'touchMove');page.wait_for_timeout(16)
 touch([],'touchEnd');page.wait_for_timeout(150);assert page.evaluate('visualViewport.scale')>scale0+.1;results.append({'case':'real touch selection/cancel, single sound/vibration, vertical chain and pinch','state':verify(page)});context.close()
 context=b.new_context(viewport={'width':390,'height':844},java_script_enabled=False);page=context.new_page();page.goto(args.origin,wait_until='domcontentloaded');assert page.locator('#works a[href],#works dialog').count()==0;assert not page.locator('.works-controls').is_visible();results.append({'case':'no-JS static portrait preview contains no original navigation or dialog'});context.close();b.close()
assert not errors,errors
assert hashes()==before_hashes,'Source changed during browser verification'
(OUT/'verification.json').write_text(json.dumps({'cases':results,'pageerrors':errors,'sourceHashes':before_hashes},ensure_ascii=False,indent=2),encoding='utf8');print('PASS',len(results),'current portrait Works groups; errors0; source unchanged')
