"""Cookie settings against an isolated built site. Vendor code and external providers are stubbed."""
import argparse,hashlib,json,mimetypes,re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--build',default='.local/cookie65-dist');parser.add_argument('--label');args=parser.parse_args()
BUILD=ROOT/args.build
if args.label:
 assert re.fullmatch(r'[\w-]+',args.label)
 OUT=ROOT/'tmp/planning/iteration66/cookie'/args.label;OUT.mkdir(parents=True,exist_ok=False)
else:OUT=ROOT/'tmp/planning/iteration65/cookie';OUT.mkdir(parents=True,exist_ok=True)
def build_hashes():return{str(f.relative_to(BUILD)):hashlib.sha256(f.read_bytes()).hexdigest()for f in [BUILD/'index.html',*sorted((BUILD/'_astro').glob('*.js')),*sorted((BUILD/'_astro').glob('*.css'))]}
source_start=build_hashes()
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 vendors=[];errors=[]
 def setup(context,hold=False):
  held=[]
  def route(request):
   url=urlsplit(request.request.url)
   if url.hostname=='soyuz.hair':
    file=BUILD/('index.html'if url.path=='/'else url.path.lstrip('/'))
    if file.is_dir():file=file/'index.html'
    if file.is_file():request.fulfill(path=str(file),content_type='application/javascript'if file.suffix=='.js'else mimetypes.guess_type(file.name)[0]or'application/octet-stream')
    else:request.abort()
   elif url.hostname in ['www.googletagmanager.com','mc.yandex.ru']:
    vendors.append(request.request.url)
    if hold:held.append(request)
    else:request.fulfill(content_type='application/javascript',body='/* Counter intentionally not executed by QA. */')
   else:request.abort()
  context.route('**/*',route)
  return held
 def ready(page):
  page.on('pageerror',lambda e:errors.append(e.stack or str(e)))
  page.goto('https://soyuz.hair/?phone=private-fixture#private',wait_until='domcontentloaded')
  page.wait_for_timeout(450)
 def open_settings(page):
  # Exercise the user-visible cookie control in the floating settings panel.
  if page.locator('[data-analytics-prompt]').is_visible():page.locator('[data-analytics-prompt] [data-analytics-settings]').click()
  elif page.viewport_size['width']<=960:
   if not page.locator('#mobile-menu').is_visible():page.locator('[data-open-menu]').click();page.wait_for_timeout(350)
   page.locator('#mobile-menu .menu-contact-row [data-analytics-settings]').click()
  else:
   page.locator('[data-site-settings]').click()
   page.locator('#site-settings-panel [data-analytics-settings]').click()
  page.locator('#cookie-settings').wait_for(state='visible')
  page.wait_for_timeout(300)
 def save(page):
  page.locator('[data-analytics-save]').click();page.wait_for_timeout(300)
  assert not page.locator('#cookie-settings').is_visible()
 def consent(page):return page.evaluate("()=>JSON.parse(localStorage.getItem('soyuz.analytics.v2'))")
 context=browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce');setup(context)
 page=context.new_page();ready(page)
 assert page.locator('[data-analytics-prompt]').is_visible();assert vendors==[]
 open_settings(page)
 assert page.locator('[data-cookie-service]:checked').count()==0
 page.keyboard.press('Escape');page.wait_for_timeout(80)
 assert not page.locator('#cookie-settings').is_visible();assert vendors==[]
 assert page.locator('[data-analytics-prompt] [data-analytics-settings]').evaluate('(e)=>e===document.activeElement')
 open_settings(page);page.locator('[data-cookie-service=metrika]').check();save(page)
 assert consent(page)['metrika']and not consent(page)['ga4']
 assert len(vendors)==1 and'mc.yandex.ru'in vendors[0]
 page.evaluate("()=>{document.cookie='_ym_uid=fixture;Path=/;Secure';document.cookie='_ga=fixture;Path=/;Secure';dispatchEvent(new Event('fixture'));document.dispatchEvent(new CustomEvent('soyuz:booking-open',{detail:{master_id:'lyubov',service_id:'haircut',phone:'private',email:'private'}}));}")
 ym=page.evaluate('()=>ym.a.map(row=>Array.from(row))')
 assert any(row[1]=='reachGoal'and row[2]=='booking_open'for row in ym)
 assert all('phone'not in row[-1]and'email'not in row[-1]for row in ym if row[1]=='reachGoal')
 init=next(row for row in ym if row[1]=='init');assert init[-1]['url']=='https://soyuz.hair/'
 open_settings(page);page.locator('[data-analytics-withdraw]').click();page.wait_for_timeout(300)
 assert not consent(page)['metrika']and not consent(page)['ga4']
 assert page.locator('[data-site-settings]').evaluate('(e)=>e===document.activeElement'),'hidden cookie control lost return focus'
 assert not page.evaluate("()=>document.cookie.includes('_ym_uid')||document.cookie.includes('_ga=')")
 assert page.evaluate('()=>ym.a.length')==0
 open_settings(page);page.locator('[data-cookie-service=ga4]').check();save(page)
 assert consent(page)['ga4']and not consent(page)['metrika']
 assert len(vendors)==2 and'googletagmanager.com'in vendors[-1]
 page.evaluate("()=>document.dispatchEvent(new CustomEvent('soyuz:booking-open',{detail:{master_id:'lyubov',phone:'private'}}))")
 ga=page.evaluate('()=>dataLayer.map(row=>Array.from(row))')
 assert any(row[:2]==['event','booking_open']for row in ga)
 config=next(row for row in ga if row[0]=='config');assert config[-1]['page_location']=='https://soyuz.hair/'
 assert all('phone'not in row[-1]for row in ga if row[0]=='event')
 open_settings(page);page.locator('[data-cookie-service=metrika]').check();page.keyboard.press('Escape');page.wait_for_timeout(80)
 assert not consent(page)['metrika'],'closing an unsaved draft changed consent'
 second=context.new_page();ready(second)
 open_settings(page);page.locator('[data-analytics-withdraw]').click();page.wait_for_timeout(300)
 before=second.evaluate("()=>dataLayer.filter(row=>row[0]==='event').length")
 second.evaluate("()=>document.dispatchEvent(new CustomEvent('soyuz:booking-open',{detail:{master_id:'lyubov'}}))")
 assert second.evaluate("()=>dataLayer.filter(row=>row[0]==='event').length")==before,'cross-tab withdrawal did not stop events'
 second.close();page.reload(wait_until='domcontentloaded');page.wait_for_timeout(300)
 assert not page.locator('[data-analytics-prompt]').is_visible(),'refusal did not persist'
 context.close()
 # A withdrawal while SDKs are still in transit must empty delayed commands.
 delayed=browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce');held=setup(delayed,hold=True)
 page=delayed.new_page();ready(page);page.locator('[data-analytics-choice=granted]').click();page.wait_for_timeout(80)
 assert len(held)==2
 open_settings(page);page.locator('[data-analytics-withdraw]').click();page.wait_for_timeout(100)
 assert page.evaluate("()=>!dataLayer.some(row=>['config','event','js'].includes(row[0]))")
 assert page.evaluate('()=>ym.a.length')==0
 for route in held:route.fulfill(content_type='application/javascript',body='/* Delayed counter deliberately not executed. */')
 delayed.close()
 # Old grants are not silently widened. Old refusals remain refusals.
 for legacy,visible in [('granted',True),('denied',False)]:
  old=browser.new_context(viewport={'width':1440,'height':900});setup(old)
  old.add_init_script("localStorage.setItem('soyuz.analytics.v1',%s)"%json.dumps(legacy))
  page=old.new_page();prior=len(vendors);ready(page)
  assert page.locator('[data-analytics-prompt]').is_visible()==visible
  assert len(vendors)==prior;old.close()
 # Storage errors preserve a functional session choice without claiming persistence.
 blocked=browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce');setup(blocked)
 blocked.add_init_script("""{const get=Storage.prototype.getItem,set=Storage.prototype.setItem;Storage.prototype.getItem=function(k){if(k.startsWith('soyuz.analytics'))throw new DOMException('Blocked','SecurityError');return get.call(this,k)};Storage.prototype.setItem=function(k,v){if(k.startsWith('soyuz.analytics'))throw new DOMException('Blocked','QuotaExceededError');return set.call(this,k,v)}}""")
 page=blocked.new_page();ready(page);open_settings(page);page.locator('[data-cookie-service=ga4]').check();save(page);open_settings(page)
 assert'только в этой вкладке'in' '.join(page.locator('[data-cookie-state]').inner_text().split()),page.locator('[data-cookie-state]').inner_text()
 assert page.locator('[data-cookie-service=ga4]').is_checked();blocked.close()
 # Native modal focus stays in the dialog; closing interrupts the common motion.
 motion=browser.new_context(viewport={'width':1440,'height':900},reduced_motion='no-preference');setup(motion)
 page=motion.new_page();ready(page);page.locator('[data-analytics-prompt] [data-analytics-settings]').click();page.wait_for_timeout(40)
 for step in range(9):
  page.keyboard.press('Tab')
  # Native modal traversal may visit browser chrome; no outside page control may receive focus.
  assert page.evaluate("()=>document.activeElement===document.body||!!document.activeElement.closest('#cookie-settings')"),(step,page.evaluate("()=>({active:document.activeElement.tagName,open:document.querySelector('#cookie-settings').open})"))
 page.keyboard.press('Escape');page.wait_for_timeout(300)
 assert not page.locator('#cookie-settings').is_visible();assert page.locator('[data-analytics-prompt] [data-analytics-settings]').evaluate('(e)=>e===document.activeElement')
 motion.close()
 # The primary compact entry lives in the expanded native menu, under a second modal.
 nested=[]
 for width,height,movement in [(390,844,'reduce'),(320,568,'no-preference')]:
  compact=browser.new_context(viewport={'width':width,'height':height},reduced_motion=movement);setup(compact)
  page=compact.new_page();ready(page);open_settings(page);page.locator('[data-analytics-withdraw]').click();page.wait_for_timeout(300)
  page.locator('[data-open-menu]').click();page.wait_for_timeout(350)
  entry=page.locator('#mobile-menu .menu-contact-row [data-analytics-settings]')
  assert page.locator('#mobile-menu').evaluate('(e)=>e.matches(":modal")')
  for action in ['escape','save']:
   entry.click();page.locator('#cookie-settings').wait_for(state='visible');page.wait_for_timeout(300)
   assert page.locator('dialog:modal').count()==2
   assert page.locator('[data-mobile-nav]').get_attribute('data-suppressed')=='true','nested cookie left the dock visible'
   assert page.locator('[data-mobile-nav]').evaluate('(e)=>e.inert'),'nested cookie left the dock interactive'
   if action=='escape':page.keyboard.press('Escape')
   else:page.locator('[data-cookie-service=metrika]').check();page.locator('[data-analytics-save]').click()
   page.wait_for_timeout(350)
   assert not page.locator('#cookie-settings').is_visible()
   assert page.locator('#mobile-menu').evaluate('(e)=>e.matches(":modal")')
   assert page.locator('[data-mobile-nav]').get_attribute('data-suppressed')=='false'
   assert not page.locator('[data-mobile-nav]').evaluate('(e)=>e.inert')
   assert entry.evaluate('(e)=>e===document.activeElement'),(width,action,'cookie did not restore focus into the native menu')
  assert consent(page)['metrika']and not consent(page)['ga4']
  page.keyboard.press('Escape');page.wait_for_timeout(350)
  assert page.locator('dialog:modal').count()==0
  assert page.locator('[data-open-menu]').evaluate('(e)=>e===document.activeElement')
  nested.append({'width':width,'height':height,'motion':movement,'escapeAndSaveRestoreMenuFocus':True,'dockSuppressedBehindCookie':True})
  compact.close()
 # Width/theme/text stress. These are browser emulations, not physical-device tests.
 geometries=[]
 for width,height,dark,enlarged in [(1440,900,False,False),(600,480,True,False),(390,844,False,False),(320,568,True,False),(390,600,False,True),(320,568,True,True)]:
  small=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce',color_scheme='dark'if dark else'light');setup(small)
  page=small.new_page();ready(page);open_settings(page)
  if enlarged:
   page.evaluate("""()=>{for(const el of document.querySelectorAll('#cookie-settings h2,#cookie-settings p,#cookie-settings legend,#cookie-settings summary,#cookie-settings strong,#cookie-settings label>span>span,#cookie-settings .cookie-service-heading>span,#cookie-settings .btn'))el.style.fontSize=parseFloat(getComputedStyle(el).fontSize)*2+'px';}""")
  page.locator('[data-analytics-save]').scroll_into_view_if_needed()
  result=page.locator('#cookie-settings').evaluate("""e=>{const content=e.querySelector('.surface-content');return{width:e.getBoundingClientRect().width,viewport:innerWidth,horizontalOverflow:content.scrollWidth>content.clientWidth+1,scrollbarEdgeGap:e.getBoundingClientRect().right-content.getBoundingClientRect().right,scrollportPadding:parseFloat(getComputedStyle(content).paddingRight),buttons:[...e.querySelectorAll('.cookie-actions .btn')].map(b=>{const s=getComputedStyle(b),r=b.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(b);const t=range.getBoundingClientRect();return{height:r.height,textHeight:t.height,textRects:range.getClientRects().length,lineHeight:parseFloat(s.lineHeight),inlinePadding:parseFloat(s.paddingInlineStart),fits:t.width<=r.width-parseFloat(s.paddingInlineStart)-parseFloat(s.paddingInlineEnd)+1}})}}""")
  assert not result['horizontalOverflow'],(width,height,enlarged,result)
  assert result['width']<=width
  assert result['scrollbarEdgeGap']<1 and result['scrollportPadding']==0,result
  assert all(b['height']>=44 and b['inlinePadding']>=12 and b['fits']and b['textRects']==1 for b in result['buttons']),result
  accordion=page.locator('#cookie-settings .cookie-details')
  summary=accordion.locator('summary');summary.scroll_into_view_if_needed()
  assert accordion.evaluate('e=>e.classList.contains("faq-item")&&!!e.querySelector(".faq-mark")&&!e.open')
  summary.click();assert accordion.evaluate('e=>e.open')
  before_choice=consent(page)
  summary.press('Space');assert not accordion.evaluate('e=>e.open')
  summary.press('Enter');assert accordion.evaluate('e=>e.open')
  assert consent(page)==before_choice,'reading consent details changed the saved choice'
  disclosure=summary.evaluate("""e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect(),label=[...e.children].find(x=>getComputedStyle(x).display!=='none'&&!x.classList.contains('faq-mark'));const range=document.createRange();range.selectNodeContents(label);return{height:r.height,nowrap:s.whiteSpace,padding:parseFloat(s.paddingLeft),labelFits:range.getBoundingClientRect().width<=label.getBoundingClientRect().width+1,textRects:range.getClientRects().length}}""")
  assert disclosure['height']>=44 and disclosure['nowrap']=='nowrap'and disclosure['padding']>=12 and disclosure['labelFits']and disclosure['textRects']==1,disclosure
  assert page.locator('#cookie-settings .surface-content').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
  copy=' '.join(page.locator('#cookie-settings').inner_text().split())
  assert 'Отказ не влияет'not in copy and'Эти настройки не заменяют'not in copy
  assert all(text in copy for text in ['ИП Бухарин Евгений Олегович','432909508772','180','Google','Яндекс','shaverfamily@yandex.ru'])
  geometries.append({'viewport':[width,height],'dark':dark,'text200':enlarged,'sharedDisclosure':disclosure,**result})
  page.screenshot(path=str(OUT/f'{args.engine}-{width}x{height}-text{200 if enlarged else 100}.png'))
  small.close()
 # FAQ owns the disclosure styling and CSS transition; there is no separate
 # cookie accordion state, height animator or delayed close timer.
 interrupted=[]
 for movement in ['no-preference','reduce']:
  check=browser.new_context(viewport={'width':1440,'height':900},reduced_motion=movement);setup(check)
  page=check.new_page();ready(page);open_settings(page)
  summary=page.locator('#cookie-settings .cookie-details>summary');summary.scroll_into_view_if_needed()
  page.evaluate("""()=>{window.disclosureFrames=[];function read(){const e=document.querySelector('.cookie-details'),m=e.querySelector('.faq-mark');disclosureFrames.push({open:e.open,transform:getComputedStyle(m,'::before').transform});if(disclosureFrames.length<40)requestAnimationFrame(read)}requestAnimationFrame(read)}""")
  summary.click();page.wait_for_timeout(45);summary.click();page.wait_for_timeout(45);summary.click();page.wait_for_timeout(350)
  assert page.locator('.cookie-details').evaluate('e=>e.open')
  frames=page.evaluate('disclosureFrames');assert any(v['open']for v in frames)and any(not v['open']for v in frames),frames
  if movement=='no-preference':assert len({v['transform']for v in frames})>3,frames
  page.keyboard.press('Escape');page.wait_for_timeout(300);assert not page.locator('#cookie-settings').is_visible()
  assert page.locator('[data-analytics-prompt] [data-analytics-settings]').evaluate('e=>e===document.activeElement')
  interrupted.append({'motion':movement,'frames':frames,'escapeRestoresFocus':True});check.close()
 # One compact shell starts with the notice; X saves a refusal without granting a service.
 banners=[]
 for width,theme in [(390,'light'),(390,'dark'),(1440,'light'),(1440,'dark')]:
  notice=browser.new_context(viewport={'width':width,'height':844 if width==390 else 900},color_scheme=theme,reduced_motion='reduce');setup(notice)
  page=notice.new_page();prior=len(vendors);ready(page)
  prompt=page.locator('[data-analytics-prompt]');assert prompt.is_visible()and len(vendors)==prior
  result=prompt.evaluate(r"""e=>{const r=e.getBoundingClientRect();return{width:r.width,availableWidth:document.documentElement.getBoundingClientRect().width,title:getComputedStyle(e.querySelector('h2')).fontSize,words:e.querySelector('p').innerText.trim().split(/\s+/).length,overflow:e.scrollWidth>e.clientWidth+1,buttons:[...e.querySelectorAll('.analytics-choice-actions button')].map(b=>{const s=getComputedStyle(b),r=b.getBoundingClientRect(),t=document.createRange();t.selectNodeContents(b);return{label:b.innerText,x:r.x,y:r.y,height:r.height,inlinePadding:parseFloat(s.paddingInlineStart),rects:t.getClientRects().length,fits:t.getBoundingClientRect().width<=r.width-parseFloat(s.paddingInlineStart)-parseFloat(s.paddingInlineEnd)+1}})}}""")
  if width>960:assert result['width']<=400 and abs(result['width']-min(400,result['availableWidth']-32))<1,result
  else:
   assert prompt.evaluate("e=>e.closest('[data-mobile-nav]')!==null")
   assert not page.locator('.dock-toolbar').is_visible()
   assert page.locator('.dock-shell').count()==1
  assert result['title']=='18px'and result['words']<=25 and not result['overflow'],result
  assert [b['label']for b in result['buttons']]==['Разрешить','Настройки'],result
  assert result['buttons'][1]['x']>result['buttons'][0]['x']and abs(result['buttons'][1]['y']-result['buttons'][0]['y'])<1,result
  assert all(b['height']>=44 and b['inlinePadding']>=12 and b['rects']==1 and b['fits']for b in result['buttons']),result
  page.screenshot(path=str(OUT/f'{args.engine}-banner-{width}-{theme}.png'))
  entry=prompt.locator('[data-analytics-settings]');entry.focus();page.keyboard.press('Enter');page.locator('#cookie-settings').wait_for(state='visible')
  assert page.locator('[data-cookie-service]:checked').count()==0
  page.locator('[data-cookie-service=ga4]').focus();page.keyboard.press('Space');page.keyboard.press('Escape');page.wait_for_timeout(100)
  assert len(vendors)==prior and consent(page)is None,'closing an unsaved keyboard draft loaded analytics'
  if width>960:assert entry.evaluate('e=>e===document.activeElement')
  else:
   assert not prompt.is_visible()and page.locator('.dock-toolbar').is_visible()
   assert page.locator('[data-open-menu]').evaluate('e=>e===document.activeElement')
  open_settings(page);assert page.locator('[data-cookie-service]:checked').count()==0
  page.locator('[data-analytics-withdraw]').press('Enter');page.wait_for_timeout(300)
  assert consent(page)['metrika']==False and consent(page)['ga4']==False and len(vendors)==prior
  page.reload(wait_until='domcontentloaded');page.wait_for_timeout(300)
  assert not prompt.is_visible()and len(vendors)==prior,'refusal was lost on reload'
  open_settings(page);assert page.locator('[data-cookie-service]:checked').count()==0
  page.keyboard.press('Escape');page.wait_for_timeout(100);assert len(vendors)==prior
  banners.append({'viewport':width,'theme':theme,'defaultVendorRequests':0,'unsavedDraftVendorRequests':0,'keyboardRefusalPersisted':True,'settingsReopened':True,**result})
  notice.close()
 browser.close()
assert errors==[],errors
source_end=build_hashes();assert source_start==source_end,'tested build changed during cookie QA'
(OUT/f'{args.engine}.json').write_text(json.dumps({'engine':args.engine,'build':str(BUILD),'sourceStart':source_start,'sourceEnd':source_end,'vendorCodeExecuted':False,'noVendorBeforeChoice':True,'granularChoice':True,'withdrawal':True,'delayedQueueRevocation':True,'legacyMigration':True,'crossTab':True,'noPIIInCustomEvents':True,'safePageLocation':True,'nestedMobileMenu':nested,'geometries':geometries,'disclosureInterruptions':interrupted,'compactBanners':banners,'pageErrors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'PASS {args.engine}: separate services, refusal/reopen/withdrawal, pending SDKs, safe events, cross-tab, legacy migration, storage errors, six layouts including 320px+200% text; vendors stubbed')
