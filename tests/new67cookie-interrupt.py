"""Trusted close plus early native wheel: sample outgoing content continuity, no vendor execution."""
import argparse,json,re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--origin',required=True);a.add_argument('--label',required=True);args=a.parse_args();assert re.fullmatch(r'[\w-]+',args.label)
out=ROOT/'tmp/planning/iteration67/cookie-interrupt'/args.label;out.mkdir(parents=True,exist_ok=False)
report={'origin':args.origin,'pageErrors':[],'vendorRequests':[]}
with sync_playwright()as p:
 b=p.chromium.launch(channel='chrome',args=['--mute-audio']);c=b.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlsplit(r.request.url)
  if u.hostname in ['mc.yandex.ru','www.googletagmanager.com']:report['vendorRequests'].append(r.request.url);r.fulfill(content_type='application/javascript',body='/* Stub */')
  elif u.hostname=='soyuz.hair':r.fulfill(response=r.fetch(url=args.origin.rstrip('/')+u.path+('?' +u.query if u.query else'')))
  else:r.abort()
 c.route('**/*',route);page=c.new_page();page.on('pageerror',lambda e:report['pageErrors'].append(e.stack or str(e)));page.goto('https://soyuz.hair/',wait_until='domcontentloaded');page.wait_for_timeout(350);page.wait_for_function("document.fonts.status==='loaded'");page.evaluate("scrollTo({top:79,behavior:'instant'})");page.wait_for_timeout(100)
 page.evaluate("""()=>{window.framesCookie=[];window.cookieFades=[];window.cookieCancels=[];window.clickCookieAt=undefined;window.wheelCookieAt=undefined;const notice=document.querySelector('[data-analytics-prompt]'),dock=document.querySelector('[data-mobile-nav]'),shell=dock.querySelector('.dock-shell'),toolbar=dock.querySelector('.dock-toolbar');const nativeAnimate=Element.prototype.animate,nativeCancel=Animation.prototype.cancel;Element.prototype.animate=function(frames,options){const row=(this===notice||this===toolbar)&&frames[0]?.opacity!==undefined?{target:this===notice?'notice':'toolbar',at:performance.now(),first:Number(frames[0].opacity),last:Number(frames.at(-1).opacity),duration:options.duration}:undefined;if(row)cookieFades.push(row);const animation=nativeAnimate.call(this,frames,options);if(row)animation.finished.then(()=>row.fulfilledAt=performance.now(),()=>row.cancelledAt=performance.now());return animation};Animation.prototype.cancel=function(){const target=this.effect?.target;if(target===notice||target===toolbar)cookieCancels.push({target:target===notice?'notice':'toolbar',at:performance.now(),opacity:Number(getComputedStyle(target).opacity)});return nativeCancel.call(this)};const sample=()=>framesCookie.push({at:performance.now(),hidden:notice.hidden,visible:!!notice.getClientRects().length,opacity:Number(getComputedStyle(notice).opacity),exiting:notice.hasAttribute('data-cookie-exiting'),inert:notice.inert,toolbarInert:toolbar.inert,height:shell.getBoundingClientRect().height,toolbarOpacity:Number(getComputedStyle(toolbar).opacity),condensed:dock.dataset.condensed,scrollY});addEventListener('wheel',e=>{if(e.isTrusted)wheelCookieAt=performance.now()},{capture:true,once:true});document.addEventListener('click',e=>{if(!e.isTrusted||!e.target.closest('.analytics-choice-close'))return;clickCookieAt=performance.now();sample();requestAnimationFrame(function frame(){sample();if(performance.now()<clickCookieAt+650)requestAnimationFrame(frame)})},{capture:true,once:true})}""")
 # CDP sends the same trusted native inputs without locator.click's post-action
 # waiting; the wheel must arrive while the outgoing material is still visible.
 rect=page.locator('.analytics-choice-close').bounding_box();x=rect['x']+rect['width']/2;y=rect['y']+rect['height']/2;native=c.new_cdp_session(page)
 native.send('Input.dispatchMouseEvent',{'type':'mouseMoved','x':x,'y':y});native.send('Input.dispatchMouseEvent',{'type':'mousePressed','x':x,'y':y,'button':'left','buttons':1,'clickCount':1});native.send('Input.dispatchMouseEvent',{'type':'mouseReleased','x':x,'y':y,'button':'left','buttons':0,'clickCount':1});native.send('Input.dispatchMouseEvent',{'type':'mouseWheel','x':x,'y':y,'deltaX':0,'deltaY':180});page.wait_for_timeout(650)
 report.update(page.evaluate("({clickAt:clickCookieAt,wheelAt:wheelCookieAt,frames:framesCookie,fades:cookieFades,cancels:cookieCancels,choice:JSON.parse(localStorage.getItem('soyuz.analytics.v2'))})"));c.close();b.close()
frames=report['frames'];report['prematureHide']=[{'previous':before,'next':after}for before,after in zip(frames,frames[1:])if before['visible']and not after['visible']and before['opacity']>.1]
retarget=[fade for fade in report['fades']if fade['target']=='notice'and .25<fade['first']<.95]
report['retarget']=retarget
for fade in retarget:
 previous=max((entry for entry in report['cancels']if entry['target']=='notice'and entry['at']<=fade['at']),key=lambda entry:entry['at'])
 fade['alphaDeltaFromCancel']=abs(fade['first']-previous['opacity'])
 incoming=next(entry for entry in report['fades']if entry['target']=='toolbar'and entry['at']>=fade['at'])
 fade['pairedDuration']=incoming['duration'];fade['pairedStartDelta']=incoming['at']-fade['at'];fade['pairedEndDelta']=abs((incoming.get('fulfilledAt')or incoming.get('cancelledAt'))-fade['fulfilledAt'])
(out/'chromium.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
assert retarget,'The native wheel did not retarget while outgoing opacity was above .25; no false late PASS'
assert all(fade['alphaDeltaFromCancel']<.05 and fade['duration']==fade['pairedDuration']and fade['pairedStartDelta']<8 and fade['pairedEndDelta']<8 for fade in retarget),retarget
assert not report['pageErrors']and not report['vendorRequests'],report
assert not report['prematureHide'],report['prematureHide']
assert frames[-1]['hidden']and not frames[-1]['exiting']and not frames[-1]['inert']and not frames[-1]['toolbarInert']and frames[-1]['toolbarOpacity']==1,frames[-1]
print('PASS trusted X→early wheel preserves outgoing opacity through retarget')
