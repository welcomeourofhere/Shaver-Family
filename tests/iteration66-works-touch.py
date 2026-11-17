"""Real CDP touch regression for portrait fan travel and single rounded clip."""
import argparse,hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',required=True);parser.add_argument('--label',required=True);args=parser.parse_args()
OUT=ROOT/'artifacts/iteration66/works-touch'/args.label;OUT.mkdir(parents=True,exist_ok=True)
SOURCES=['src/content/works.ts','src/components/Works.astro','src/scripts/works.ts','src/scripts/works-layout.ts','src/styles/works.css','src/scripts/horizontal-swipe.ts','src/scripts/gesture-math.ts','src/styles/interactions.css','content/work-photos.json','content/work-photos-owner.json']
def hashes():return{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()for f in SOURCES}
before=hashes();cases=[];errors=[]
def state(page):return page.locator('#works').evaluate('''e=>{const f=e.querySelector('.works-fan'),c=e.querySelector('[data-work-current=true]'),s=c.querySelector('[data-press-surface]'),i=c.querySelector('img');return{index:+f.dataset.workIndex,position:+f.dataset.workPosition,target:+f.dataset.workTarget,moving:f.dataset.workMoving==='true',id:c.dataset.workId,box:c.getBoundingClientRect().toJSON(),sounds:window.sounds66.length,vibrations:window.vibrations66.length,dragging:f.classList.contains('is-dragging'),border:getComputedStyle(c).borderTopWidth,frameBorder:getComputedStyle(s).borderTopWidth,frameBackground:getComputedStyle(s).backgroundColor,imageRadius:getComputedStyle(i).borderRadius,frameRadius:getComputedStyle(s).borderRadius,focus:c.matches(':focus-visible'),outline:getComputedStyle(c).outlineWidth,overflow:document.documentElement.scrollWidth>innerWidth+1}}''')
def rest(page):page.wait_for_function('document.querySelector(".works-fan").dataset.workMoving!=="true"',timeout=4000);page.wait_for_timeout(100);return state(page)
def center(page):
 r=state(page)['box'];return r['x']+r['width']/2,r['y']+r['height']/2
def home(page):page.locator('[data-work-current=true]').focus();page.keyboard.press('Home');page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(80);return state(page)
def touch(cdp,kind,points):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':points})
def start(page,cdp):
 x,y=center(page);touch(cdp,'touchStart',[{'x':x,'y':y,'id':1}]);return x,y
def moves(page,cdp,x,y,offsets,delay=30):
 samples=[]
 for dx in offsets:
  touch(cdp,'touchMove',[{'x':x+dx,'y':y,'id':1}]);page.wait_for_timeout(delay);samples.append(state(page))
 return samples
def finish(page,cdp,cancel=False):touch(cdp,'touchCancel'if cancel else'touchEnd',[]);return rest(page)
def fresh(browser,width,motion):
 c=browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True,reduced_motion=motion)
 c.add_init_script('''window.sounds66=[];window.vibrations66=[];HTMLMediaElement.prototype.play=function(){if(this.src.includes('/audio/'))window.sounds66.push(this.src);return Promise.resolve()};navigator.vibrate=p=>{if(Array.isArray(p)&&p.some(v=>v>0))window.vibrations66.push(p);return true}''')
 page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(args.origin,wait_until='domcontentloaded');page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(250);return c,page,c.new_cdp_session(page)
with sync_playwright()as p:
 b=p.chromium.launch(channel='chrome')
 for motion in['no-preference','reduce']:
  for width in[320,390,800]:
   context,page,cdp=fresh(b,width,motion)
   for distance in[20,32]:
    base=home(page);x,y=start(page,cdp);samples=moves(page,cdp,x,y,[-distance*n/10 for n in range(1,11)]);page.wait_for_timeout(120);after=finish(page,cdp)
    assert all(s['index']==0 and abs(s['position'])<.4 for s in samples),samples
    assert after['index']==0 and after['position']==0 and after['sounds']==base['sounds']and after['vibrations']==base['vibrations'],after
    cases.append({'case':'short slow touch returns without selection or feedback','motion':motion,'width':width,'distance':distance,'samples':samples,'after':after})
   base=home(page);x,y=start(page,cdp);samples=moves(page,cdp,x,y,[-100*n/10 for n in range(1,11)]);page.wait_for_timeout(120);after=finish(page,cdp)
   assert after['index']==1 and after['sounds']==base['sounds']+1 and after['vibrations']==base['vibrations']+(0 if motion=='reduce' else 1),after;cases.append({'case':'deliberate 100px touch selects exactly one and gives one feedback','motion':motion,'width':width,'after':after})
   base=home(page);x,y=start(page,cdp);samples=moves(page,cdp,x,y,[-30,-60,-90],16);touch(cdp,'touchEnd',[]);settling=[]
   for _ in range(30):settling.append(state(page));page.wait_for_timeout(16)
   after=rest(page);assert after['index']==1 and after['sounds']==base['sounds']+1 and after['vibrations']==base['vibrations']+(0 if motion=='reduce' else 1),after;assert all(-.01<=s['position']<1.5 for s in settling),settling
   cases.append({'case':'fast flick bounded to one selected card without a phantom intermediate selection','motion':motion,'width':width,'settling':settling,'after':after})
   base=home(page);x,y=start(page,cdp);samples=moves(page,cdp,x,y,[-90*n/6 for n in range(1,7)]);committed=state(page);after=finish(page,cdp,True)
   assert after['sounds']==committed['sounds'] and after['vibrations']==committed['vibrations'] and not after['dragging'],after;cases.append({'case':'touch cancellation adds no feedback after already rendered crossings and clears capture/drag','motion':motion,'width':width,'committed':committed,'after':after})
   check=state(page);assert check['frameBackground']=='rgba(0, 0, 0, 0)'and check['imageRadius']=='0px'and check['frameRadius']!='0px'and check['border']==check['frameBorder']=='0px'and not check['overflow'],check
   if width==390:
    base=home(page);x,y=start(page,cdp);samples=moves(page,cdp,x,y,[-10,-20,-12,-5],40);page.wait_for_timeout(120);after=finish(page,cdp);assert after['index']==0 and after['sounds']==base['sounds'],after;cases.append({'case':'small reversal remains the same selection','motion':motion,'samples':samples,'after':after})
    base=home(page);page.locator('[data-work-step="1"]').click();page.wait_for_timeout(35);visible=state(page);x,y=start(page,cdp);samples=moves(page,cdp,x,y,[-10,-20],25);assert abs(samples[0]['position']-visible['position'])<.45,(visible,samples);finish(page,cdp);cases.append({'case':'new touch interrupts settling from visible fractional pose','motion':motion,'before':visible,'samples':samples})
    base=home(page);x,y=start(page,cdp);scroll=page.evaluate('scrollY')
    for n in range(1,11):touch(cdp,'touchMove',[{'x':x,'y':y-150*n/10,'id':1}]);page.wait_for_timeout(20)
    touch(cdp,'touchEnd',[]);page.wait_for_timeout(250);assert page.evaluate('scrollY')>scroll+40 and state(page)['sounds']==base['sounds'];cases.append({'case':'native vertical scroll stays available','motion':motion,'travel':page.evaluate('scrollY')-scroll})
    page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(100);page.locator('[data-work-current=true]').focus();page.keyboard.press('ArrowRight');focus=state(page);assert focus['focus']and float(focus['outline'].replace('px',''))>=3,focus
    page.mouse.click(2,100);page.screenshot(path=str(OUT/f'{motion}-single-clip.png'));cases.append({'case':'single transparent rounded clip; keyboard outline retained','motion':motion,'state':focus})
    page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(100);x,y=center(page);scale=page.evaluate('visualViewport.scale');touch(cdp,'touchStart',[{'x':x-30,'y':y,'id':1},{'x':x+30,'y':y,'id':2}])
    for n in range(1,9):touch(cdp,'touchMove',[{'x':x-30-n*6,'y':y,'id':1},{'x':x+30+n*6,'y':y,'id':2}]);page.wait_for_timeout(20)
    touch(cdp,'touchEnd',[]);page.wait_for_timeout(120);assert page.evaluate('visualViewport.scale')>scale+.1;cases.append({'case':'native pinch stays available','motion':motion,'scale':page.evaluate('visualViewport.scale')})
   context.close()
  # Mouse deliberately keeps the compact visual fan spacing and multi-card travel.
  context=b.new_context(viewport={'width':1440,'height':1000},reduced_motion=motion);context.add_init_script('window.sounds66=[];window.vibrations66=[];HTMLMediaElement.prototype.play=function(){if(this.src.includes("/audio/"))window.sounds66.push(this.src);return Promise.resolve()}');page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(args.origin,wait_until='domcontentloaded');page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(200);base=state(page);x,y=center(page);page.mouse.move(x,y);page.mouse.down();samples=[]
  for n in range(1,31):page.mouse.move(x-n*13,y);page.wait_for_timeout(16);samples.append(state(page))
  assert len({s['index']for s in samples})>=3 and all(not s['overflow']for s in samples)and samples[-1]['sounds']>base['sounds'],samples
  page.screenshot(path=str(OUT/f'{motion}-desktop-held.png'));page.mouse.up();after=rest(page);page.wait_for_timeout(150);assert state(page)['sounds']==after['sounds'];cases.append({'case':'desktop rendered crossings sound during held travel without a delayed replay tail','motion':motion,'samples':samples,'after':after});context.close()
 b.close()
assert not errors,errors
assert hashes()==before,'Works source changed during real gesture verification'
(OUT/'verification.json').write_text(json.dumps({'cases':cases,'pageerrors':errors,'sourceHashes':before,'origin':args.origin},ensure_ascii=False,indent=2),encoding='utf8');print('PASS',len(cases),'touch/clip/desktop groups; errors0; source unchanged')

