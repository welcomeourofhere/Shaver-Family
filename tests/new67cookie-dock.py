"""First cookie choice shares the compact dock. Counters and providers never execute."""
import argparse,hashlib,json,mimetypes,re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321/');parser.add_argument('--build');parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--scope',choices=['full','keyboard'],default='full');parser.add_argument('--label',required=True);args=parser.parse_args()
assert re.fullmatch(r'[\w-]+',args.label)
OUT=ROOT/'tmp/planning/iteration67/cookie-dock'/args.label;OUT.mkdir(parents=True,exist_ok=False)
BUILD=ROOT/args.build if args.build else None
SOURCES=['src/components/MobileNav.astro','src/components/AnalyticsChoice.astro','src/scripts/analytics.ts','src/scripts/dock-surface.ts','src/scripts/mobile-nav.ts','src/styles/mobile-nav.css','src/styles/dock-surface.css','src/styles/analytics-choice.css']
def hashes():return{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in SOURCES}
source_start=hashes();errors=[];rows=[];requests=[]
SAMPLE="""()=>{const dock=document.querySelector('[data-mobile-nav]'),notice=dock.querySelector('[data-analytics-prompt]'),toolbar=dock.querySelector('.dock-toolbar'),shell=dock.querySelector('.dock-shell'),r=e=>e.getBoundingClientRect().toJSON(),visible=e=>!!e.getClientRects().length&&getComputedStyle(e).display!=='none';return{compact:matchMedia('(max-width:960px)').matches,notice:visible(notice),toolbar:visible(toolbar),dock:r(dock),noticeRect:r(notice),shell:r(shell),color:getComputedStyle(shell).backgroundColor,opacity:getComputedStyle(toolbar).opacity,shells:document.querySelectorAll('.dock-shell').length,availableWidth:document.documentElement.getBoundingClientRect().width,overflow:document.documentElement.scrollWidth>innerWidth+1,choice:JSON.parse(localStorage.getItem('soyuz.analytics.v2')),active:{tag:document.activeElement.tagName,id:document.activeElement.id,inNotice:notice.contains(document.activeElement),isMenu:document.activeElement.hasAttribute('data-open-menu'),connected:document.activeElement.isConnected},buttons:[...notice.querySelectorAll('.analytics-choice-actions button')].map(b=>{const s=getComputedStyle(b),t=document.createRange();t.selectNodeContents(b);return{height:r(b).height,padding:parseFloat(s.paddingLeft),rects:t.getClientRects().length,fits:t.getBoundingClientRect().width<=b.clientWidth-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight)+1}})}}"""
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 def context(width=390,height=844,theme='light',motion='no-preference',modules=True,saved=False):
  c=browser.new_context(viewport={'width':width,'height':height},color_scheme=theme,reduced_motion=motion)
  c.add_init_script("localStorage.setItem('soyuz_theme',%s)"%json.dumps(theme))
  c.add_init_script("window.cookieAudio=[];const nativePlay=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){const at=performance.now(),result=nativePlay.call(this);if(this.src.includes('/audio/'))cookieAudio.push({src:this.src,at,returnedAt:performance.now()});return result}")
  if saved:c.add_init_script("{const n=Date.now();localStorage.setItem('soyuz.analytics.v2',JSON.stringify({version:2,notice:'2026-11-16',updatedAt:n,expiresAt:n+180*86400000,metrika:false,ga4:false}))}")
  def route(r):
   u=urlsplit(r.request.url)
   if u.hostname in ['www.googletagmanager.com','mc.yandex.ru']:
    requests.append(r.request.url);r.fulfill(content_type='application/javascript',body='/* Counter deliberately not executed. */');return
   if u.hostname!='soyuz.hair':r.abort();return
   if not modules and r.request.resource_type=='script':r.abort();return
   if BUILD:
    f=BUILD/('index.html'if u.path=='/'else u.path.lstrip('/'))
    if f.is_dir():f=f/'index.html'
    if f.is_file():r.fulfill(path=str(f),content_type='application/javascript'if f.suffix=='.js'else mimetypes.guess_type(f.name)[0]or'application/octet-stream')
    else:r.abort()
   else:
    response=r.fetch(url=args.origin.rstrip('/')+u.path+('?' +u.query if u.query else''))
    r.fulfill(response=response)
  c.route('**/*',route)
  return c
 def ready(c):
  page=c.new_page();page.on('pageerror',lambda e:errors.append(e.stack or str(e)));page.goto('https://soyuz.hair/',wait_until='domcontentloaded');page.wait_for_timeout(350);return page
 # Modules unavailable: the inline choice bootstrap and CSS still choose the right first panel.
 for saved in ([False,True]if args.scope=='full'else[]):
  c=context(modules=False,saved=saved);page=ready(c);s=page.evaluate(SAMPLE)
  assert s['notice']!=saved and s['toolbar']==saved and s['shells']==1,s
  assert abs(s['dock']['width']-(s['availableWidth']-8))<1 and not s['overflow'],s
  page.screenshot(path=str(OUT/f'initial-scripts-unavailable-{saved}.png'));rows.append({'scenario':'scripts-unavailable','saved':saved,**s});c.close()
 # Compact, transition boundary and desktop in both themes.
 for width in (([320,390,600,960,961,965,1440]if args.engine=='webkit'else[320,390,600,960,961,1440])if args.scope=='full'else[]):
  for theme in ['light','dark']:
   c=context(width=width,theme=theme);page=ready(c);prior=len(requests);s=page.evaluate(SAMPLE)
   assert s['notice']and s['shells']==1 and not s['overflow'],(width,theme,s)
   assert all(b['height']>=44 and b['padding']>=12 and b['rects']==1 and b['fits']for b in s['buttons']),s
   if s['compact']:assert not s['toolbar']and abs(s['dock']['width']-(s['availableWidth']-8))<1,s
   close=page.locator('.analytics-choice-close');cr=close.bounding_box();nr=s['noticeRect']
   assert cr['height']>=44 and cr['width']>=44 and abs((cr['x']+cr['width'])-(nr['right']))<=20,(cr,nr)
   page.evaluate("""()=>{window.cookieFrames=[];window.cookieClickAt=undefined;function sample(){const d=document.querySelector('[data-mobile-nav]'),s=d.querySelector('.dock-shell'),t=d.querySelector('.dock-toolbar');cookieFrames.push({at:performance.now(),height:s.getBoundingClientRect().height,color:getComputedStyle(s).backgroundColor,opacity:getComputedStyle(t).opacity,animations:s.getAnimations().map(a=>({currentTime:a.currentTime,duration:a.effect.getTiming().duration,progress:a.effect.getComputedTiming().progress,playState:a.playState}))})}document.addEventListener('click',e=>{if(!e.isTrusted||!e.target.closest('.analytics-choice-close'))return;cookieClickAt=performance.now();window.cookieFocusAtClick={tag:document.activeElement.tagName,inNotice:document.querySelector('[data-analytics-prompt]').contains(document.activeElement)};sample();requestAnimationFrame(function frame(){sample();if(performance.now()<cookieClickAt+320)requestAnimationFrame(frame)})},{capture:true,once:true})}""")
   close.click();page.wait_for_timeout(400);after=page.evaluate(SAMPLE);frames=page.evaluate('cookieFrames');transition={'engine':args.engine,'width':width,'theme':theme,'before':s,'after':after,'clickAt':page.evaluate('cookieClickAt'),'focusAtClick':page.evaluate('cookieFocusAtClick'),'audioCalls':page.evaluate('cookieAudio'),'frames':frames};(OUT/f'transition-{width}-{theme}.json').write_text(json.dumps(transition,ensure_ascii=False,indent=2),encoding='utf-8')
   assert not after['notice']and after['choice']['metrika']==False and after['choice']['ga4']==False and len(requests)==prior,after
   if s['compact']:
    assert after['toolbar']and after['shells']==1 and after['dock']['height']<s['dock']['height'],after
    assert len({round(f['height'],1)for f in frames})>3 and len({f['color']for f in frames})>3,frames
    if transition['focusAtClick']['inNotice']:assert after['active']['isMenu'],transition
    else:assert not after['active']['inNotice']and after['active']['connected'],transition
   page.reload(wait_until='domcontentloaded');page.wait_for_timeout(300);assert not page.locator('[data-analytics-prompt]').is_visible()and len(requests)==prior
   if s['compact']:
    page.locator('[data-open-menu]').click();page.wait_for_timeout(320);page.locator('#mobile-menu .menu-contact-row [data-analytics-settings]').click()
   else:page.locator('[data-site-settings]').click();page.locator('#site-settings-panel [data-analytics-settings]').click()
   page.locator('#cookie-settings').wait_for(state='visible');assert page.locator('[data-cookie-service]:checked').count()==0
   page.keyboard.press('Escape');page.wait_for_timeout(320)
   page.screenshot(path=str(OUT/f'closed-{width}-{theme}.png'));rows.append({'scenario':'close',**transition});c.close()
 # A keyboard-owned close always hands focus to the live menu, including engines whose pointer click keeps body focus.
 c=context();page=ready(c);prior=len(requests);close=page.locator('.analytics-choice-close');close_rect=close.bounding_box();assert close_rect['width']>=44 and close_rect['height']>=44,close_rect;close.focus();page.keyboard.press('Enter');page.wait_for_timeout(320);s=page.evaluate(SAMPLE);assert not s['notice']and s['active']['isMenu']and s['choice']['metrika']==False and s['choice']['ga4']==False and len(requests)==prior,s;rows.append({'scenario':'keyboard-close-focus','closeRect':close_rect,**s});c.close()
 # Enlarged text and reserved screen edges change composition, never shrink or wrap action labels.
 for width,theme in ([(320,'dark'),(600,'light')]if args.scope=='full'else[]):
  c=context(width=width,height=700,theme=theme,motion='reduce');page=ready(c)
  page.evaluate("""()=>{const r=document.documentElement;r.style.setProperty('--safe-left','30px');r.style.setProperty('--safe-right','22px');r.style.setProperty('--safe-bottom','20px');for(const e of document.querySelectorAll('[data-analytics-prompt] h2,[data-analytics-prompt] p,[data-analytics-prompt] .btn'))e.style.fontSize=parseFloat(getComputedStyle(e).fontSize)*2+'px'}""")
  s=page.evaluate(SAMPLE);assert not s['overflow']and all(b['height']>=44 and b['padding']>=12 and b['rects']==1 and b['fits']for b in s['buttons']),s
  assert page.locator('[data-analytics-prompt]').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
  page.screenshot(path=str(OUT/f'text200-safe-area-{width}-{theme}.png'))
  settings=page.locator('[data-analytics-prompt] [data-analytics-settings]');settings.scroll_into_view_if_needed()
  reachable=page.locator('[data-analytics-prompt]').evaluate("e=>{const r=e.getBoundingClientRect();return[...e.querySelectorAll('.analytics-choice-actions button')].every(b=>{const q=b.getBoundingClientRect();return q.top>=r.top&&q.bottom<=r.bottom})}")
  assert reachable,'enlarged notice actions are not reachable inside their own scrollport'
  page.screenshot(path=str(OUT/f'text200-safe-area-actions-{width}-{theme}.png'));settings.press('Enter');page.locator('#cookie-settings').wait_for(state='visible');page.keyboard.press('Escape');page.wait_for_timeout(100)
  assert page.locator('[data-open-menu]').evaluate('e=>e===document.activeElement')and page.evaluate(SAMPLE)['choice']is None
  rows.append({'scenario':'text200-safe-area','width':width,'theme':theme,'actionsReachable':reachable,'keyboardSettingsEscape':True,**s});c.close()
 # Choosing settings dismisses only this notice, never checks a vendor or saves a draft.
 for motion in ['no-preference','reduce']:
  c=context(motion=motion);page=ready(c);prior=len(requests)
  page.locator('[data-analytics-prompt] [data-analytics-settings]').focus();page.keyboard.press('Enter');page.locator('#cookie-settings').wait_for(state='visible')
  page.locator('[data-cookie-service=ga4]').focus();page.keyboard.press('Space');page.keyboard.press('Escape');page.wait_for_timeout(350)
  assert page.evaluate(SAMPLE)['choice']is None and len(requests)==prior
  assert not page.locator('[data-analytics-prompt]').is_visible()and page.locator('.dock-toolbar').is_visible()
  assert page.locator('[data-open-menu]').evaluate('e=>e===document.activeElement')
  page.locator('[data-open-menu]').click();page.wait_for_timeout(320);page.locator('#mobile-menu .menu-contact-row [data-analytics-settings]').click();page.locator('#cookie-settings').wait_for(state='visible')
  assert not page.locator('[data-cookie-service=ga4]').is_checked()
  page.locator('[data-cookie-service=metrika]').check();page.locator('[data-analytics-save]').click();page.wait_for_timeout(350)
  s=page.evaluate(SAMPLE);assert s['choice']['metrika']and not s['choice']['ga4']and len(requests)==prior+1,s
  rows.append({'scenario':'settings-keyboard','motion':motion,**s});c.close()
 # Rapid reversal and breakpoint change settle one shell and remove temporary layers.
 if args.scope=='full':
  c=context();page=ready(c);page.locator('.analytics-choice-close').click();page.wait_for_timeout(35);page.set_viewport_size({'width':965,'height':844});page.wait_for_timeout(80);assert not page.evaluate("matchMedia('(max-width:960px)').matches");page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(300)
  assert page.locator('[data-cookie-exiting]').count()==0 and page.locator('.dock-toolbar').is_visible()
  page.locator('[data-open-menu]').click();page.wait_for_timeout(320);assert page.locator('#mobile-menu').evaluate('e=>e.matches(":modal")');page.keyboard.press('Escape');page.wait_for_timeout(300)
  rows.append({'scenario':'interrupted-breakpoint',**page.evaluate(SAMPLE)});c.close()
 browser.close()
assert errors==[],errors
source_end=hashes();assert source_start==source_end,'cookie source changed during browser test'
(OUT/f'{args.engine}.json').write_text(json.dumps({'engine':args.engine,'selection':args.scope,'sourceStart':source_start,'sourceEnd':source_end,'build':str(BUILD)if BUILD else None,'origin':args.origin,'counterCodeExecuted':False,'externalProvidersExecuted':False,'physicalDevice':False,'pageErrors':errors,'vendorRequests':requests,'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'PASS {args.engine} cookie dock ({args.scope}): {len(rows)} scenarios; X denial/focus, keyboard draft and per-service grant; counters stubbed')
