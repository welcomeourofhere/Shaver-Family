"""Exercise shared modal scroll ownership at the native scrollbar breakpoint."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import argparse,json
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:4366/');parser.add_argument('--engine',choices=['chromium','firefox','webkit'],required=True);parser.add_argument('--theme',choices=['light','dark'],default='light');args=parser.parse_args()
out=ROOT/'artifacts/iteration65/modal-scroll';out.mkdir(parents=True,exist_ok=True);rows=[]
fixture='<html lang="ru"><meta charset="utf-8"><title>Контрольный макет записи</title><body><h1>Тестовая форма</h1><p>Заявка и оплата не создаются.</p></body></html>'

def ready(browser,width,motion,height=900):
 context=browser.new_context(viewport={'width':width,'height':height},reduced_motion=motion,color_scheme=args.theme)
 context.route('**/*',lambda r:r.continue_()if r.request.url.startswith(args.url)else r.fulfill(status=200,content_type='text/html; charset=utf-8',body=fixture)if 'yclients.ru'in r.request.url else r.abort())
 page=context.new_page();page.set_default_timeout(10000);page.goto(args.url);page.evaluate('document.fonts.ready');page.wait_for_function("document.querySelector('#mobile-menu').dataset.dockOwned==='true'");page.wait_for_timeout(200)
 return context,page
def pose(page):
 return page.evaluate("""()=>({y:scrollY,bodyY:document.body.scrollTop,mq:matchMedia('(max-width:960px)').matches,client:document.documentElement.clientWidth,locked:document.body.hasAttribute('data-modal-scroll-locked'),poses:[...document.querySelectorAll('#top,#about .section-title,#about .about-layer')].map(e=>{const r=e.getBoundingClientRect();return[r.x,r.y,r.width,r.height]})})""")
def same_pose(before,after):
 assert len(before['poses'])==len(after['poses'])==6,(before,after)
 assert before['mq']==after['mq'] and before['client']==after['client'],(before,after)
 assert all(abs(a-b)<1 for ra,rb in zip(before['poses'],after['poses'])for a,b in zip(ra,rb)),(before,after)
def open_menu(page):
 page.locator('[data-open-menu]').click();page.wait_for_function("document.querySelector('#mobile-menu').open&&document.body.hasAttribute('data-modal-scroll-locked')");page.wait_for_timeout(300)
def open_cookie(page,compact):
 if compact:
  open_menu(page);page.locator('#mobile-menu [data-analytics-settings]').click()
 else:
  page.locator('[data-site-settings]').click();page.locator('#site-settings-panel [data-analytics-settings]').click()
 page.wait_for_function("document.querySelector('#cookie-settings').open&&document.body.hasAttribute('data-modal-scroll-locked')");page.wait_for_timeout(300)
def close_all(page):
 for _ in range(4):
  if not page.locator('dialog[open]').count():break
  page.keyboard.press('Escape');page.wait_for_timeout(300)
 page.wait_for_function("!document.body.hasAttribute('data-modal-scroll-locked')")

with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 for width,location in [(390,'top'),(960,'about'),(961,'about'),(961,'bottom'),(1440,'top'),(1440,'about'),(1440,'bottom')]:
  for motion in ['no-preference','reduce']:
   print('CASE',args.engine,args.theme,width,location,motion,flush=True)
   context,page=ready(browser,width,motion)
   if location=='about':page.locator('#about').evaluate('e=>scrollTo(0,e.offsetTop+250)')
   elif location=='bottom':page.evaluate('scrollTo(0,document.documentElement.scrollHeight-innerHeight-100)')
   if width==1440 and location=='top':
    page.locator('.site-header .more-menu>summary').click();page.wait_for_timeout(100);assert not page.evaluate("document.body.hasAttribute('data-modal-scroll-locked')");page.keyboard.press('Escape')
   page.wait_for_timeout(350);before=pose(page)
   page.evaluate("()=>{window.rootEvents=0;window.innerEvents=0;window.unlocks=0;addEventListener('scroll',e=>{if(e.target===document)rootEvents++;else innerEvents++},{capture:true});new MutationObserver(records=>{for(const r of records)if(r.oldValue==='true'&&!document.body.hasAttribute('data-modal-scroll-locked'))unlocks++}).observe(document.body,{attributes:true,attributeOldValue:true,attributeFilter:['data-modal-scroll-locked']})}")
   open_cookie(page,before['mq']);after=pose(page);same_pose(before,after);assert after['locked'] and after['y']==0
   assert abs(after['bodyY']-before['y'])<.5
   if before['mq']:assert page.locator('#mobile-menu').get_attribute('open')is not None
   page.mouse.move(width-1,100);page.mouse.wheel(0,600)
   reserved_bar=page.evaluate('innerWidth>document.documentElement.clientWidth')
   if reserved_bar:page.mouse.down();page.mouse.move(width-1,450,steps=8);page.mouse.up()
   page.wait_for_timeout(150)
   same_pose(before,pose(page));assert page.evaluate('scrollY')==0
   assert page.evaluate('document.documentElement.scrollHeight<=innerHeight+1')
   assert page.evaluate('rootEvents')==0
   if width==961 and location=='about':page.screenshot(path=str(out/f'{args.engine}-{args.theme}-{width}-{motion}-locked.png'))
   page.keyboard.press('Escape');page.wait_for_timeout(300)
   if before['mq']:
    assert page.locator('#mobile-menu').get_attribute('open')is not None
    assert page.evaluate("document.body.hasAttribute('data-modal-scroll-locked')&&unlocks===0")
    assert page.locator('#mobile-menu [data-analytics-settings]').evaluate('e=>e===document.activeElement')
   close_all(page);restored=pose(page);assert abs(restored['y']-before['y'])<1,(args.engine,width,location,motion,before,restored)
   return_selector='[data-open-menu]'if before['mq']else'[data-site-settings]'
   assert page.locator(return_selector).evaluate('e=>e===document.activeElement')
   if before['y']>500:
    page.mouse.move(1,450);page.mouse.wheel(0,-400);page.wait_for_timeout(450);assert page.evaluate('scrollY')<before['y']
   rows.append({'type':'pose-nested-restore','width':width,'location':location,'motion':motion,'before':before,'locked':after,'restored':restored,'rootThumbAttempt':reserved_bar});context.close()
 for motion in ['no-preference','reduce']:
  print('EXTRA',args.engine,args.theme,motion,flush=True)
  context,page=ready(browser,960,motion);page.locator('#about').scroll_into_view_if_needed();page.wait_for_timeout(250);before=pose(page);open_cookie(page,True)
  for width in [961,960]:
   page.set_viewport_size({'width':width,'height':900});page.wait_for_timeout(300);assert page.locator('#cookie-settings').get_attribute('open')is not None;assert page.evaluate("document.body.hasAttribute('data-modal-scroll-locked')")
  resized=pose(page);close_all(page);assert abs(page.evaluate('scrollY')-resized['bodyY'])<1
  assert page.evaluate("document.activeElement.matches('[data-open-menu],[data-site-settings]')"),page.evaluate('document.activeElement.outerHTML.slice(0,250)')
  open_menu(page);page.locator('#mobile-menu nav a[href$="#services"]').click();page.wait_for_function("!document.querySelector('dialog[open]')&&!document.body.hasAttribute('data-modal-scroll-locked')")
  page.wait_for_function("()=>{const e=document.querySelector('#services');return Math.abs(e.getBoundingClientRect().top-(parseFloat(getComputedStyle(e).scrollMarginTop)||0))<3}")
  landing=page.locator('#services').evaluate('e=>({top:e.getBoundingClientRect().top,margin:parseFloat(getComputedStyle(e).scrollMarginTop)||0})');assert abs(landing['top']-landing['margin'])<3,landing
  assert page.locator('#services .section-title').evaluate('e=>e===document.activeElement'),page.evaluate('document.activeElement.outerHTML.slice(0,250)')
  rows.append({'type':'resize-anchor','motion':motion,'landing':landing});context.close()
  context,page=ready(browser,961,motion);page.locator('#masters').scroll_into_view_if_needed();portrait=page.locator('[data-team-open]').first;portrait.focus();page.keyboard.press('Enter');dialog=page.locator('#'+portrait.get_attribute('aria-controls'));page.wait_for_function("document.querySelector('.team-story-dialog[open]')&&document.body.hasAttribute('data-modal-scroll-locked')");page.wait_for_timeout(300)
  viewport=dialog.locator('.surface-content');viewport.evaluate('e=>{window.readEvents=0;e.addEventListener("scroll",()=>readEvents++)}');assert dialog.locator('.story-heading h2').evaluate('e=>e===document.activeElement')
  page.keyboard.press('PageDown');page.wait_for_timeout(250);keyboard_scroll=viewport.evaluate('e=>e.scrollTop');assert keyboard_scroll>0
  page.keyboard.press('ArrowDown');page.wait_for_timeout(150);assert viewport.evaluate('e=>e.scrollTop')>keyboard_scroll
  viewport.hover();page.mouse.wheel(0,500);page.wait_for_timeout(250);assert viewport.evaluate('e=>e.scrollTop')>0;assert page.evaluate('readEvents')>0
  viewport.evaluate('e=>e.scrollTop=e.scrollHeight');page.mouse.wheel(0,600);page.wait_for_timeout(100);assert page.evaluate('scrollY')==0
  close_all(page);assert portrait.evaluate('e=>e===document.activeElement')
  page.set_viewport_size({'width':1440,'height':900});page.locator('#reviews').scroll_into_view_if_needed();page.wait_for_timeout(350);page.locator('[data-review-more]').click();page.wait_for_timeout(150)
  reading=page.evaluate("""()=>{const e=[...document.querySelectorAll('.review-prose')].find(e=>e.getClientRects().length&&e.scrollHeight-e.clientHeight>50);if(!e)return null;e.scrollTop=(e.scrollHeight-e.clientHeight)/2;return e.id}""");assert reading,'A visible desktop review must offer native reading'
  page.wait_for_function('(id)=>Number(document.getElementById(id).closest(".review-card").style.getPropertyValue("--review-scroll-progress"))>.1',arg=reading)
  rows.append({'type':'native-dialog-reading','motion':motion,'scrollEvents':page.evaluate('readEvents'),'reviewProgressAfterRestore':True});context.close()
 for width in [961,1440]:
  for motion in ['no-preference','reduce']:
   print('BOOKING',args.engine,args.theme,width,motion,flush=True);context,page=ready(browser,width,motion)
   source=page.locator('.footer-booking [data-booking]');source.scroll_into_view_if_needed();page.wait_for_timeout(200);before=pose(page)
   opened=source.evaluate("""async e=>{e.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,detail:1}));await Promise.resolve();const d=document.querySelector('#booking-drawer');return{open:d.open,modal:d.matches(':modal'),layout:d.dataset.layout,locked:document.body.hasAttribute('data-modal-scroll-locked'),mq:matchMedia('(max-width:960px)').matches,client:document.documentElement.clientWidth,animating:d.querySelector('.booking-panel').getAnimations().some(a=>a.playState==='running')}}""")
   assert opened['open'] and opened['mq']==before['mq'] and opened['client']==before['client'],opened
   overlay=width==961;assert (opened['layout']=='overlay')==overlay and opened['modal']==overlay and opened['locked']==overlay,opened
   if motion=='no-preference':assert opened['animating'],opened
   if not overlay:page.wait_for_timeout(350)
   wheel_before=page.evaluate('scrollY');page.mouse.move(1,450);page.mouse.wheel(0,-400);page.wait_for_timeout(250)
   if overlay:
    assert page.evaluate('scrollY')==0
   else:assert page.evaluate('scrollY')<wheel_before
   closing=page.locator('[data-booking-close]').evaluate("""async e=>{e.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,detail:1}));await Promise.resolve();const d=document.querySelector('#booking-drawer');let checkpoint=false;if(d.dataset.layout==='overlay'&&!matchMedia('(prefers-reduced-motion:reduce)').matches){for(const el of d.querySelectorAll('[data-booking-panel],[data-booking-backdrop]'))for(const a of el.getAnimations()){a.pause();a.currentTime=Number(a.effect.getTiming().duration)*.4;checkpoint=true}}return{open:d.open,state:document.documentElement.dataset.bookingState,locked:document.body.hasAttribute('data-modal-scroll-locked'),checkpoint}}""")
   if motion=='no-preference':assert closing['open'] and closing['state']=='closing' and closing['locked']==overlay,closing
   if overlay and motion=='no-preference':
    page.mouse.wheel(0,400);assert page.evaluate('scrollY')==0
    source.evaluate("e=>e.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,detail:1}))");page.wait_for_timeout(80);assert page.evaluate("document.querySelector('#booking-drawer').matches(':modal')&&document.body.hasAttribute('data-modal-scroll-locked')")
    page.locator('[data-booking-close]').click()
   page.wait_for_function("!document.querySelector('#booking-drawer').open&&!document.body.hasAttribute('data-modal-scroll-locked')");page.wait_for_timeout(100)
   assert page.evaluate("matchMedia('(max-width:960px)').matches")==before['mq']
   if overlay:assert abs(page.evaluate('scrollY')-before['y'])<1
   rows.append({'type':'booking-fixture','width':width,'motion':motion,'opened':opened,'closing':closing,'overlay':overlay});context.close()
 for motion in ['no-preference','reduce']:
  print('FOOTER-RESIZE',args.engine,args.theme,motion,flush=True);context,page=ready(browser,961,motion)
  page.evaluate('scrollTo(0,document.documentElement.scrollHeight-innerHeight-100)');page.wait_for_timeout(250);open_cookie(page,pose(page)['mq']);resizes=[]
  for width,height in [(390,900),(1440,1200),(961,600),(960,900)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(350)
   assert page.evaluate("document.querySelector('#cookie-settings').matches(':modal')&&document.body.hasAttribute('data-modal-scroll-locked')")
   resizes.append({'width':width,'height':height,**pose(page)})
  locked=pose(page);close_all(page);restored=pose(page);same_pose(locked,restored)
  assert abs(restored['y']-locked['bodyY'])<1,(locked,restored)
  rows.append({'type':'footer-resize-native-clamp','motion':motion,'resizes':resizes,'locked':locked,'restored':restored});context.close()
 print('STICKY',args.engine,args.theme,flush=True);context,page=ready(browser,1440,'no-preference',1200)
 page.locator('#about').evaluate('e=>scrollTo(0,e.offsetTop+250)');page.wait_for_timeout(400)
 assert page.locator('#about').get_attribute('data-stack-mode')=='stack'
 before=pose(page);open_cookie(page,False);same_pose(before,pose(page));page.screenshot(path=str(out/f'{args.engine}-{args.theme}-sticky-locked.png'));close_all(page);same_pose(before,pose(page))
 rows.append({'type':'native-sticky-stack','before':before,'restored':pose(page)});context.close()
 browser.close()
(ROOT/f'tmp/planning/iteration65/modal-scroll-{args.engine}-{args.theme}.json').write_text(json.dumps({'theme':args.theme,'rows':rows,'published':False},indent=2),encoding='utf-8')
print('PASS',len(rows),'modal scroll cases;',args.engine,args.theme)
