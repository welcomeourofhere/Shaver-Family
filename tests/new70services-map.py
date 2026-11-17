"""Service geometry and map interaction regression on an explicit own-site origin.

The default map document is a controlled cross-origin gesture fixture, not evidence
of Yandex rendering. --actual-provider uses two stationary real widget views only.
No booking, route, geolocation, advertising link or external account is activated.
"""
import argparse,hashlib,json,re,traceback
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
SOURCE=['src/scripts/service-disclosure.ts','src/scripts/service-deck.ts','src/styles/service-deck.css','src/components/Contacts.astro','src/content/contact-map.ts','src/scripts/contact-map.ts','src/styles/contacts.css']
POSE="""()=>{const e=document.querySelector('#services'),s=e.querySelector('.sd-stack'),r=s.getBoundingClientRect();return{height:r.height,bottom:e.getBoundingClientRect().bottom+scrollY}}"""
MAP_FIXTURE='''<!doctype html><html><meta charset="utf-8"><body style="margin:0;overflow:hidden;background:#b6c9bb;user-select:none"><main style="height:100vh;touch-action:none" onpointermove="if(event.buttons)document.body.dataset.drag='true'"><button style="min-width:44px;min-height:44px" onclick="this.dataset.zoom=Number(this.dataset.zoom||0)+1">Приблизить</button><p>Controlled map gesture fixture</p></main></body></html>'''

def hashes():return{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in SOURCE}
def page_y(p):return p.evaluate("document.body.dataset.modalScrollLocked==='true'?document.body.scrollTop:scrollY")
def touch(p,c,locator):
 b=locator.bounding_box();x=b['x']+b['width']/2;y=b['y']+min(b['height']*.65,240);start=page_y(p);session=c.new_cdp_session(p)
 session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
 for i in range(1,11):session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-i*12,'id':1}]});p.wait_for_timeout(18)
 session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_timeout(180);session.detach();return page_y(p)-start

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--origin',required=True);parser.add_argument('--label',required=True);parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--only',choices=['services','map','all'],default='all');parser.add_argument('--pilot',action='store_true');parser.add_argument('--actual-provider',action='store_true');parser.add_argument('--single',action='store_true');a=parser.parse_args()
 assert urlsplit(a.origin).hostname in ['127.0.0.1','localhost','soyuz.hair','stay-tan-habanero.tilda.ws'];assert re.fullmatch(r'[\w-]+',a.label)
 out=ROOT/'artifacts/iteration70'/a.label;out.mkdir(parents=True,exist_ok=False);report={'origin':a.origin,'engine':a.engine,'sourceStart':hashes(),'pilot':a.pilot,'providerFixture':not a.actual_provider,'physicalDevices':False,'performanceClaim':False,'cases':[]}
 def save():(out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 def run(browser,kind,width,theme='light',motion='no-preference',scale=1,fallback=False):
  row={'kind':kind,'width':width,'theme':theme,'motion':motion,'textScale':scale,'moveFallback':fallback,'pass':False,'pageErrors':[],'forbidden':[]};c=browser.new_context(viewport={'width':width,'height':1000},has_touch=width<=960,**({'is_mobile':width<=960}if a.engine!='firefox'else{}),color_scheme=theme,reduced_motion=motion)
  c.add_init_script("(()=>{if(top!==window)return;localStorage.setItem('soyuz.analytics.v1','denied');"+("delete Element.prototype.moveBefore;"if fallback else'')+"})()")
  def route(r):
   u=urlsplit(r.request.url);h=u.hostname or''
   if h.endswith('yclients.ru')or h.endswith('yclients.com'):row['forbidden'].append(u.netloc+u.path);r.abort()
   elif h=='yandex.ru'and '/map-widget/'in u.path and not a.actual_provider:r.fulfill(content_type='text/html',body=MAP_FIXTURE)
   else:r.continue_()
  c.route('**/*',route);p=c.new_page();p.set_default_timeout(18000);p.on('pageerror',lambda e:row['pageErrors'].append(str(e)))
  try:
   response=p.goto(a.origin,wait_until='domcontentloaded',timeout=45000);assert response and response.status==200;raw=response.body();row['documentSha256']=hashlib.sha256(raw).hexdigest();row['builds']=sorted(set(x.decode()for x in re.findall(rb'/Soyuz/releases/([a-f0-9]{20})/',raw)));assert a.pilot or b'/@vite/client'not in raw,'HMR rejected as compiled acceptance'
   p.evaluate('document.fonts.ready');p.wait_for_function('document.documentElement.dataset.cookiePrompt!==undefined')
   prompt=p.locator('[data-analytics-prompt]')
   if prompt.is_visible():prompt.locator('[data-analytics-settings]').click();p.locator('#cookie-settings [data-analytics-withdraw]').click();p.wait_for_function('!document.querySelector("#cookie-settings").open')
   if scale==2:p.evaluate("for(const e of document.querySelectorAll('#services .sd-summary,#services .sd-description,#contacts-map-dialog h2,.contact-map-credit'))e.style.fontSize=parseFloat(getComputedStyle(e).fontSize)*2+'px'")
   if kind=='services':services(p,row)
   else:map_case(p,c,row)
   assert not row['pageErrors']and not row['forbidden'],(row['pageErrors'],row['forbidden']);row['pass']=True
  except Exception:row['failure']=traceback.format_exc()
  finally:
   if not row['pass']:
    try:p.screenshot(path=str(out/(str(len(report['cases']))+'-failure.png')),timeout=5000)
    except Exception as e:row['captureError']=str(e)
   c.close();report['cases'].append(row);save();print(json.dumps({k:row[k]for k in ['kind','width','theme','motion','textScale','moveFallback','pass']}),flush=True)
  return row['pass']
 def services(p,row):
  p.locator('#services').scroll_into_view_if_needed();row['transitions']=[]
  for category in range(p.locator('[data-sd-tab]').count()):
   tab=p.locator('[data-sd-tab]').nth(category);tab.focus();p.keyboard.press('Enter');p.wait_for_timeout(350);panel=p.locator(f'[data-sd-panel="{category}"]');rows=panel.locator('.sd-service');count=rows.count()
   for target in list(range(1,count))+([0]if count>1 else[]):
    control=rows.nth(target).locator('summary');control.scroll_into_view_if_needed();p.wait_for_timeout(70)
    p.evaluate("""()=>{window.__serviceFrames=[];window.__serviceDone=false;const start=performance.now();function tick(){const e=document.querySelector('#services'),s=e.querySelector('.sd-stack');window.__serviceFrames.push({height:s.getBoundingClientRect().height,bottom:e.getBoundingClientRect().bottom+scrollY});if(performance.now()-start<360)requestAnimationFrame(tick);else window.__serviceDone=true;}tick();}""")
    control.click();p.wait_for_function('window.__serviceDone');frames=p.evaluate('window.__serviceFrames');dip=min(frames[0]['height'],frames[-1]['height'])-min(x['height']for x in frames);bottom_dip=min(frames[0]['bottom'],frames[-1]['bottom'])-min(x['bottom']for x in frames)
    row['transitions'].append({'category':category,'target':target,'samples':len(frames),'heightDip':dip,'followingContentDip':bottom_dip});assert dip<=1 and bottom_dip<=1,row['transitions'][-1];assert panel.locator('.sd-service[open]').count()==1
   if count>2:
    for target in [1,2,0,2]:rows.nth(target).locator('summary').focus();p.keyboard.press('Enter');p.wait_for_timeout(25)
    p.wait_for_timeout(300);assert panel.locator('.sd-service[open]').count()==1;assert panel.locator('[data-service-opening]').count()==0;assert rows.nth(2).get_attribute('open')is not None
  assert not p.evaluate('document.documentElement.scrollWidth>innerWidth+1');row['rapidKeyboardInterruptions']=True
 def map_case(p,c,row):
  def explore(frame,turn):
   f=frame.element_handle().content_frame()
   if a.actual_provider:
    close=f.get_by_role('button',name='Закрыть',exact=True)
    if close.count()and close.first.is_visible():close.first.click()
   zoom=f.get_by_role('button',name='Приблизить',exact=True);zoom.click();p.wait_for_timeout(180)
   b=frame.bounding_box();x=b['x']+b['width']*.25;y=b['y']+min(b['height']*.2,90)
   if a.actual_provider:
    row.setdefault('mapHitTargets',[]).append(f.evaluate("p=>{const e=document.elementFromPoint(p.x,p.y);return{tag:e.tagName,class:String(e.className?.baseVal??e.className),parent:String(e.parentElement.className)}}",{'x':x-b['x'],'y':y-b['y']}))
    crop={'x':x,'y':y,'width':60,'height':60};before=p.screenshot(clip=crop)
   p.mouse.move(x,y);p.mouse.down();p.mouse.move(x+35,y-20,steps=7);p.mouse.up();p.wait_for_timeout(250)
   if a.actual_provider:
    after=p.screenshot(clip=crop);changed=hashlib.sha256(before).hexdigest()!=hashlib.sha256(after).hexdigest();row.setdefault('mapDragVisualChanges',[]).append(changed);assert changed,'Map canvas did not respond visually to a drag';host.screenshot(path=str(out/(str(row['width'])+'-actual-after-drag-'+str(turn)+'.png')))
   else:assert f.locator('body').get_attribute('data-drag')=='true'and zoom.get_attribute('data-zoom')is not None
  host=p.locator('.contact-map');credit=host.locator('.contact-map-credit');host.scroll_into_view_if_needed();p.wait_for_function('document.querySelector(".contact-map").dataset.mapState==="ready"',timeout=35000);frame=p.locator('#contacts-map-frame');q=parse_qs(urlsplit(frame.get_attribute('src')).query);assert q.get('oid')==['116019915414']and q.get('scroll')==['false'];p.evaluate('window.__mapFrame=document.querySelector("#contacts-map-frame")');compact=row['width']<=960
  assert frame.evaluate('e=>getComputedStyle(e).pointerEvents')==('none'if compact else'auto');assert frame.get_attribute('aria-hidden')==str(compact).lower()
  if a.actual_provider:
   f=frame.element_handle().content_frame();f.locator('canvas').first.wait_for(state='visible',timeout=25000);text=f.locator('body').inner_text();assert 'Союз'in text and not re.search('captcha|капч|доступ ограничен',text,re.I);row['actualBusinessLabel']=True
   host.screenshot(path=str(out/(str(row['width'])+'-actual-inline.png')))
   if f.get_by_role('button',name='Закрыть',exact=True).count():f.get_by_role('button',name='Закрыть',exact=True).first.click()
  b=frame.bounding_box();x=b['x']+b['width']/2;y=b['y']+min(b['height']*.6,220);start=page_y(p);p.mouse.move(x,y);p.mouse.wheel(0,160);p.wait_for_timeout(250);row['inlineWheelTravel']=page_y(p)-start;assert row['inlineWheelTravel']>30
  if compact and a.engine=='chromium':host.scroll_into_view_if_needed();row['inlineTouchTravel']=touch(p,c,frame);assert row['inlineTouchTravel']>40
  if not compact:
   host.scroll_into_view_if_needed();explore(frame,0)
   row['inlineZoomDrag']=True;return
  row['cycles']=[];dialog=p.locator('#contacts-map-dialog')
  for turn in range(3):
   credit.scroll_into_view_if_needed();credit.focus();p.wait_for_timeout(60);start=page_y(p);p.keyboard.press('Enter');dialog.wait_for(state='visible');p.wait_for_function('document.body.dataset.modalScrollLocked==="true"');p.wait_for_function('document.querySelector(".contact-map").dataset.mapState==="ready"',timeout=35000);p.wait_for_timeout(300)
   assert dialog.locator('#contacts-map-frame').count()==1;assert p.evaluate('window.__mapFrame===document.querySelector("#contacts-map-frame")');assert frame.get_attribute('aria-hidden')=='false';assert frame.evaluate('e=>getComputedStyle(e).pointerEvents')=='auto';assert abs(page_y(p)-start)<=1
   close=dialog.get_by_role('button',name='Закрыть карту');box=close.bounding_box();assert box['width']>=44 and box['height']>=44 and box['x']>=0 and box['y']>=0 and box['y']+box['height']<=1000;assert not dialog.evaluate('e=>e.scrollWidth>e.clientWidth+1')
   explore(frame,turn);assert abs(page_y(p)-start)<=1
   if turn==0 and a.engine=='chromium':row['expandedTouchTravel']=touch(p,c,frame);assert abs(row['expandedTouchTravel'])<=1
   if turn==0:p.screenshot(path=str(out/(row['kind']+'-'+str(row['width'])+'-'+row['theme']+'-'+str(row['textScale'])+'-expanded.png')));close.click()
   elif turn==1:close.focus();p.keyboard.press('Escape')
   else:p.set_viewport_size({'width':961,'height':1000})
   p.wait_for_function('!document.querySelector("#contacts-map-dialog").open');p.wait_for_function('document.body.dataset.modalScrollLocked!=="true"');p.wait_for_function('document.querySelector(".contact-map-slot #contacts-map-frame")!==null')
   if turn<2:assert abs(page_y(p)-start)<=1,(start,page_y(p))
   else:
    # A breakpoint changes upstream layout; preserve the map's visible location,
    # rather than incorrectly requiring the old document's absolute scroll offset.
    box=p.locator('.contact-map-slot').bounding_box();assert box['y']<1000 and box['y']+box['height']>0,box
   assert credit.evaluate('e=>document.activeElement===e');row['cycles'].append({'closedBy':['button','Escape','resize'][turn],'scrollDelta':page_y(p)-start,'focusRestored':True})
  p.set_viewport_size({'width':row['width'],'height':1000});p.wait_for_timeout(80);credit.focus();p.keyboard.press('Enter');dialog.wait_for(state='visible');p.evaluate('document.dispatchEvent(new Event("astro:before-swap"))');p.wait_for_timeout(80);assert frame.get_attribute('src')is None;assert p.locator('.contact-map-slot #contacts-map-frame').count()==1;assert not dialog.get_attribute('open');row['cleanup']=True
 with sync_playwright()as pw:
  browser=getattr(pw,a.engine).launch(**({'channel':'chrome','args':['--mute-audio']}if a.engine=='chromium'else{}))
  try:
   cases=[]
   if a.actual_provider:cases=[('map',1440,'light','reduce',1,False),('map',390,'light','reduce',1,False)]
   else:
    if a.only in ['all','services']:cases.extend(('services',w,t,m,s,False)for w,t,m,s in[(390,'light','no-preference',1),(800,'dark','no-preference',1),(1440,'light','no-preference',1),(320,'dark','reduce',2)])
    if a.only in ['all','map']:cases.extend(('map',w,t,m,s,f)for w,t,m,s,f in[(320,'light','no-preference',1,False),(390,'dark','reduce',2,False),(800,'light','no-preference',1,True),(960,'dark','reduce',1,False),(961,'light','reduce',1,False),(1440,'dark','no-preference',1,False)])
   if a.single:cases=cases[:1]
   for case in cases:
    if not run(browser,*case):break
  finally:browser.close();report['browsersClosed']=True;report['sourceEnd']=hashes();report['sourceUnchanged']=report['sourceStart']==report['sourceEnd'];report['pass']=len(report['cases'])==len(cases)and all(r['pass']for r in report['cases'])and report['sourceUnchanged'];save()
 print(json.dumps({'pass':report['pass'],'cases':len(report['cases']),'report':str(out/'results.json')},ensure_ascii=False));raise SystemExit(0 if report['pass']else 1)
if __name__=='__main__':main()
