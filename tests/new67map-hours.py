"""Frozen compiled map/hours/dock QA. Default provider is an explicit delayed fixture.

--actual-provider adds one stationary real Yandex view, never a tile scan. It writes
marker/tile evidence for root visual review and intentionally returns exit2 while
that manual review remains outstanding. No booking, geo navigation or accounts.
"""
import argparse
import hashlib
import json
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, urlunsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
ROUTE='https://yandex.ru/maps/?rtext=~58.588674%2C49.669973'
MARKER='58.588674,49.669973'
BUSINESS='116019915414'
SOURCE=['src/content/contact-map.ts','src/components/Contacts.astro','src/scripts/contact-map.ts','src/styles/contacts.css','src/scripts/loading.ts','src/styles/loading.css','src/scripts/business-hours.ts','src/scripts/business-clock.ts','src/styles/business-hours.css','src/components/BusinessHoursStatus.astro','src/components/MobileNav.astro','src/scripts/mobile-nav.ts','src/scripts/dock-actions.ts']
STATES=[('07:59','closed','Сейчас закрыто','Откроемся через 1 мин'),('08:00','open','Сейчас открыто','До закрытия 11 ч'),('17:00','closing','Сейчас открыто','До закрытия 2 ч'),('19:00','closed','Сейчас закрыто','Откроемся через 13 ч')]
def hashes():return{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in SOURCE}
def clean(url):
 p=urlsplit(url);return urlunsplit((p.scheme,p.netloc,p.path,'',''))
def plain(text):return re.sub(r'\s+',' ',text).strip()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--origin');p.add_argument('--label');p.add_argument('--build');p.add_argument('--only',default='map,hours,route');p.add_argument('--actual-provider',action='store_true');p.add_argument('--self-check',action='store_true');a=p.parse_args()
 if a.self_check:
  assert parse_qs(urlsplit(ROUTE).query)['rtext']==['~'+MARKER]
  assert BUSINESS.isdigit() and all(float(x)>0 for x in MARKER.split(','))
  assert len(STATES)==4 and len({r[1]for r in STATES})==3
  assert clean('https://example.org/a?secret=x#b')=='https://example.org/a'
  source=(ROOT/'src/content/contact-map.ts').read_text(encoding='utf-8')
  assert 'map-widget/v1/' in source and 'oid=116019915414' in source and 'ol=biz' in source
  assert 'openstreetmap' not in source.lower()
  assert 'pointer-events:none' in (ROOT/'src/styles/contacts.css').read_text(encoding='utf-8')
  assert 'aria-hidden="true"' in (ROOT/'src/components/Contacts.astro').read_text(encoding='utf-8')
  print('PASS 8 pure checks; browserRuns=0');return
 assert a.origin and a.label and re.fullmatch(r'[\w-]+',a.label)
 assert urlsplit(a.origin).scheme in ['http','https']and urlsplit(a.origin).netloc
 selected=a.only.split(',');assert set(selected)<={'map','hours','route','provider'}
 actual_requested=a.actual_provider or 'provider'in selected
 out=ROOT/'artifacts/iteration67/map-hours'/a.label;out.mkdir(parents=True,exist_ok=False)
 report={'origin':a.origin,'declaredBuild':a.build,'utc':datetime.now(timezone.utc).isoformat(),'sourceStart':hashes(),'cases':[],'pageErrors':[],'provider':None,'frozenRejected':False,'boundary':'Chromium compiled wrapper QA; explicit controlled provider for default cases. Trusted CDP input, no real booking/calls/route navigation, no physical-device/performance/publication claim.'}
 def save():(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 def run(browser,name,action,width=390,theme='light',scale=1,clock=None,actual=False):
  row={'name':name,'width':width,'theme':theme,'textScale':scale,'providerFixture':not actual,'pass':False,'pageErrors':[],'network':[],'forbidden':[]};pending=[]
  c=browser.new_context(viewport={'width':width,'height':1000},color_scheme=theme,reduced_motion='reduce',is_mobile=width<=960,has_touch=width<=960)
  def route(r):
   u=urlsplit(r.request.url);h=u.hostname or''
   if h.endswith('yclients.ru')or h.endswith('yclients.com'):
    row['forbidden'].append(clean(r.request.url));r.abort();return
   if h in ['yandex.ru','www.yandex.ru'] and '/map-widget/'in u.path and not actual:
    row['network'].append({'url':r.request.url,'referer':r.request.headers.get('referer'),'kind':'held-Yandex-document-fixture'})
    if name.startswith('map-'):pending.append(r)
    else:r.fulfill(content_type='text/html',body='<html><body style="margin:0;height:100vh;background:#ddd">Controlled map response</body></html>')
   else:r.continue_()
  # The one real Yandex view keeps native HTTP cache/Referer; routing disables browser cache.
  if not actual:c.route('**/*',route)
  page=c.new_page();page.set_default_timeout(18000)
  if actual:
   def request_seen(request):
    u=urlsplit(request.url);h=u.hostname or''
    if h in ['yandex.ru','www.yandex.ru'] or (h.endswith('.yandex.net')):row['network'].append({'url':clean(request.url),'kind':'actual-provider','referer':request.headers.get('referer'),'cacheControl':request.headers.get('cache-control')})
    if h.endswith('yclients.ru')or h.endswith('yclients.com'):row['forbidden'].append(clean(request.url))
   page.on('request',request_seen)
   page.on('response',lambda response:row['network'].append({'url':clean(response.url),'status':response.status,'kind':'actual-provider-response'})if urlsplit(response.url).hostname in ['yandex.ru','www.yandex.ru'] or (urlsplit(response.url).hostname or '').endswith('.yandex.net')else None)
   page.on('requestfailed',lambda request:row['network'].append({'url':clean(request.url),'failure':request.failure,'kind':'actual-provider-failure'})if(urlsplit(request.url).hostname or'').endswith('yandex.ru')else None)
  if clock:page.clock.set_fixed_time(f'2026-11-16T{clock}:00.000Z')
  page.on('pageerror',lambda e:row['pageErrors'].append(str(e)))
  def opened():
   response=page.goto(a.origin,wait_until='domcontentloaded',timeout=35000);assert response and response.status==200
   raw=response.body();assert b'/@vite/client'not in raw,'HMR is not a frozen acceptance origin'
   identities=sorted(set(re.findall(rb'/Soyuz/releases/([a-f0-9]{20})/_astro/',raw)))
   if a.build and identities:assert[value.decode()for value in identities]==[a.build]
   row['document']={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'observedBuilds':[v.decode()for v in identities]}
   page.evaluate('document.fonts.ready');page.wait_for_function('document.documentElement.dataset.cookiePrompt!==undefined')
   prompt=page.locator('[data-analytics-prompt]')
   if prompt.is_visible():
    prompt.locator('[data-analytics-settings]').click();page.locator('#cookie-settings').wait_for(state='visible');page.locator('#cookie-settings [data-analytics-withdraw]').click();page.wait_for_function('!document.querySelector("#cookie-settings").open');prompt.wait_for(state='hidden')
  try:
   opened();action(page,c,row,pending)
   assert not row['pageErrors']and not row['forbidden'],(row['pageErrors'],row['forbidden'])
   row['pass']=True
  except Exception:
   row['failure']=traceback.format_exc()
   if 'HMR is not a frozen'in row['failure']:report['frozenRejected']=True
   try:page.screenshot(path=str(out/(name+'-failure.png')),timeout=5000)
   except Exception as e:row['screenshotFailure']=str(e)
  finally:
   for r in pending:
    try:r.abort()
    except Exception:pass
   try:c.close()
   except Exception as e:row.update(closeFailure=str(e),**{'pass':False})
   report['cases'].append(row);report['pageErrors'].extend({'case':name,'error':e}for e in row['pageErrors']);save()
  if report['frozenRejected']:raise RuntimeError('Stopped after HMR rejection')
 def verify_src(page):
  f=page.locator('#contacts-map-frame');src=f.get_attribute('src')or f.get_attribute('data-map-src');u=urlsplit(src);q=parse_qs(u.query)
  assert u.hostname=='yandex.ru'and u.path=='/map-widget/v1/'and q.get('oid')==[BUSINESS] and q.get('ol')==['biz'] and q.get('ll')==['49.669973,58.588674'] and q.get('scroll')==['false'],src
  assert f.get_attribute('referrerpolicy')=='strict-origin-when-cross-origin'
  assert page.locator('.contact-map').get_attribute('data-map-provider')=='yandex'
  assert page.locator('.contact-address').get_attribute('href')=='https://yandex.ru/maps/org/soyuz/116019915414/'
  return f,src
 def geometry(page):return page.locator('.contact-map').evaluate("""h=>{const r=h.getBoundingClientRect(),f=h.querySelector('#contacts-map-frame').getBoundingClientRect(),a=h.querySelector('.contact-map-credit'),c=a.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(a);return{host:r.toJSON(),frame:f.toJSON(),credit:c.toJSON(),creditText:range.getBoundingClientRect().toJSON(),creditHref:a.href,creditVisible:getComputedStyle(a).visibility,overflow:h.scrollWidth>h.clientWidth+1}}""")
 def wheel(page,host,row):
  host.scroll_into_view_if_needed();b=host.bounding_box();x=b['x']+b['width']/2;y=b['y']+min(b['height']/2,180)
  before=page.evaluate('scrollY');page.mouse.move(x,y);page.mouse.wheel(0,120);page.wait_for_timeout(180);after=page.evaluate('scrollY');assert after>before+20,(before,after)
  row['wheelTravel']=after-before
 def gesture(page,c,host,row):
  host.scroll_into_view_if_needed();b=host.bounding_box();x=b['x']+b['width']/2;y=b['y']+min(b['height']/2,180);cdp=c.new_cdp_session(page);start=page.evaluate('scrollY')
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
  for i in range(1,11):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-i*16,'id':1}]});page.wait_for_timeout(20)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(200);end=page.evaluate('scrollY');assert end>start+40,(start,end)
  host.scroll_into_view_if_needed();b=host.bounding_box();x=b['x']+b['width']/2;y=b['y']+min(b['height']/2,180);zoom=page.evaluate('visualViewport.scale')
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x-30,'y':y,'id':1},{'x':x+30,'y':y,'id':2}]})
  for i in range(1,9):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-30-i*6,'y':y,'id':1},{'x':x+30+i*6,'y':y,'id':2}]});page.wait_for_timeout(20)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(150);zoom_after=page.evaluate('visualViewport.scale');assert zoom_after>zoom+.1,(zoom,zoom_after);cdp.detach()
  row.update(touchTravel=end-start,pinchBefore=zoom,pinchAfter=zoom_after)
 def map_case(page,c,row,pending):
  host=page.locator('.contact-map');credit=host.locator('.contact-map-credit')
  if row['textScale']==2:credit.evaluate('e=>e.style.fontSize=parseFloat(getComputedStyle(e).fontSize)*2+"px"')
  host.scroll_into_view_if_needed();page.wait_for_function('document.querySelector(".contact-map").getAttribute("aria-busy")==="true"')
  limit=0
  while not pending and limit<40:page.wait_for_timeout(50);limit+=1
  assert len(pending)==1,len(pending)
  f,src=verify_src(page);indicator=host.locator('.loading-layer [data-loading-indicator]');indicator.wait_for(state='visible')
  centres=host.evaluate("""h=>{const a=h.getBoundingClientRect(),b=h.querySelector('.loading-layer [data-loading-indicator]').getBoundingClientRect(),s=getComputedStyle(h.querySelector('.loading-layer'));return{dx:(b.left+b.width/2)-(a.left+a.width/2),dy:(b.top+b.height/2)-(a.top+a.height/2),position:s.position}}""")
  assert abs(centres['dx'])<=1 and abs(centres['dy'])<=1 and centres['position']=='absolute',centres
  before=geometry(page);pending.pop().fulfill(content_type='text/html',body='<html><body style="margin:0;height:100vh;background:#ddd">Controlled delayed map</body></html>')
  page.wait_for_function('document.querySelector(".contact-map").dataset.mapState==="ready"');assert not host.locator('.loading-layer').is_visible()
  after=geometry(page);assert all(abs(after['host'][k]-before['host'][k])<=1 for k in ['width','height']), (before,after)
  assert not after['overflow']and after['creditVisible']=='visible'and after['creditHref']=='https://yandex.ru/maps/org/soyuz/116019915414/',after
  assert after['credit']['top']>=after['frame']['bottom']-1,after
  assert all(after['creditText'][side]>=after['host'][side]-1 for side in ['left','top'])and all(after['creditText'][side]<=after['host'][side]+1 for side in ['right','bottom']),after
  assert after['frame']['height']>200 and after['frame']['width']>200,after
  compact=row['width']<=960
  assert f.evaluate('e=>getComputedStyle(e).pointerEvents')==('none'if compact else'auto')and f.get_attribute('tabindex')==('-1'if compact else'0')and f.get_attribute('aria-hidden')==str(compact).lower()
  page.screenshot(path=str(out/(row['name']+'.png')));row.update(embed=src,loader=centres,geometry=after,controlledYandexResponse=True,actualMarkerVerified=False,textScaleScope='map credit')
  wheel(page,host,row)
  if row['width']<=960:gesture(page,c,host,row)
 def hours_case(state):
  def check(page,c,row,pending):
   time,kind,heading,detail=state;trigger=page.locator('.footer .business-hours .info-trigger-text');trigger.scroll_into_view_if_needed();trigger.focus();trigger.press('Enter');panel=page.locator('.footer .business-hours-panel');panel.wait_for(state='visible')
   status=panel.locator('[data-business-hours-status]');note=panel.locator('[data-business-hours-detail]');page.wait_for_function('(s)=>[...document.querySelectorAll("[data-business-hours-status]")].every(n=>n.dataset.state===s)',arg=kind)
   assert plain(status.text_content())==detail and plain(note.text_content())=='' and 'Сейчас'not in status.text_content(),(status.text_content(),note.text_content())
   assert not panel.evaluate('e=>e.scrollWidth>e.clientWidth+1');row.update(clockUTC=time,state=kind,compact=status.text_content(),dot=status.evaluate("e=>getComputedStyle(e,'::before').backgroundColor"))
   page.set_viewport_size({'width':1440,'height':1000});page.wait_for_function('(h)=>[...document.querySelectorAll("[data-business-hours-status]")].every(n=>n.textContent===h)',arg=heading)
   trigger.press('Enter');panel.wait_for(state='visible')
   assert plain(status.text_content())==heading and plain(note.text_content())==detail
   assert not panel.evaluate('e=>e.scrollWidth>e.clientWidth+1')
   row.update(desktop=status.text_content(),desktopDetail=note.text_content(),desktopPopupVisible=True)
  return check
 def route_case(page,c,row,pending):
  page.locator('#contacts').scroll_into_view_if_needed();link=page.locator('[data-dock-map-route]');link.wait_for(state='visible')
  def value():return link.evaluate('e=>({tag:e.tagName,href:e.href,target:e.target,rel:e.rel,visible:!!e.getClientRects().length})')
  first=value();assert first['tag']=='A'and first['href']==ROUTE and first['target']=='_blank'and'noopener'in first['rel'],first
  page.locator('[data-open-menu]').click();page.wait_for_function('document.querySelector("#mobile-menu").open');menu=value();assert menu['tag']=='A'and menu['href']==ROUTE and menu['target']=='_blank'and'noopener'in menu['rel'],menu
  row.update(contactContext=first,menuContext=menu,routeNavigated=False)
 def provider_case(page,c,row,pending):
  host=page.locator('.contact-map');host.scroll_into_view_if_needed();f,src=verify_src(page)
  page.wait_for_function('document.querySelector(".contact-map").dataset.mapState==="ready"',timeout=26000)
  frame=f.element_handle().content_frame();assert frame
  page.wait_for_timeout(2500)
  text=frame.locator('body').inner_text(timeout=5000)
  blocked=bool(re.search('captcha|капч|робот|доступ ограничен|access denied',text,re.I))
  page.screenshot(path=str(out/'actual-yandex-marker-review.png'))
  row.update(embed=src,providerText=text[:1200],blocked=blocked)
  report['provider']={'status':'blocked-or-unavailable' if blocked else 'observed-awaiting-root-visual-review','provider':'yandex','businessId':BUSINESS,'markerDOMVerified':False,'screenshot':'actual-yandex-marker-review.png','pinVerified':False}
 browser=None
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(channel='chrome',args=['--mute-audio'])
   if 'map'in selected:
    for width in [320,390,800,1440]:
     for theme in ['light','dark']:
      for scale in [1,2]:run(browser,f'map-{width}-{theme}-text{scale*100}',map_case,width,theme,scale)
   if 'hours'in selected:
    for width in [320,800]:
     for theme in ['light','dark']:
      for state in STATES:run(browser,f'hours-{width}-{theme}-{state[0].replace(":","")}',hours_case(state),width,theme,clock=state[0])
   if 'route'in selected:
    for width in [390,800]:run(browser,f'route-{width}',route_case,width)
   if actual_requested:
    run(browser,'actual-yandex-provider',provider_case,390,actual=True)
    if report['provider']is None:report['provider']={'status':'blocked-or-unavailable','markerDOMVerified':False,'failureCase':'actual-yandex-provider'}
   browser.close();browser=None
 except Exception:report['fatal']=traceback.format_exc()
 finally:
  if browser:
   try:browser.close();browser=None
   except Exception as e:report['closeFailure']=str(e)
  report['sourceEnd']=hashes();report['sourceUnchanged']=report['sourceStart']==report['sourceEnd'];report['browsersClosed']=browser is None
  report['functionalPass']=bool(report['cases'])and all(r['pass']for r in report['cases'])and not report['pageErrors']and not report.get('fatal')and report['sourceUnchanged']and report['browsersClosed'];report['allRequestedChecksPass']=report['functionalPass']and not actual_requested;save()
 print(json.dumps({'functionalPass':report['functionalPass'],'cases':len(report['cases']),'provider':report['provider'],'pageErrors':len(report['pageErrors']),'browsersClosed':report['browsersClosed'],'report':str(out/'verification.json')},ensure_ascii=False))
 raise SystemExit(0 if report['allRequestedChecksPass']else 2 if report['functionalPass']else 1)
if __name__=='__main__':main()
