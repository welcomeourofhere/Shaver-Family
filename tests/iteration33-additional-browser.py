from iteration33_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
BASE='http://127.0.0.1:4321/'
report={'article':[],'externalSubmission':False}
def start(url=BASE):
 call('open',url);call('set','media','light');settle();call('select','.footer [data-theme-select]','light')
 js('window.__qaErrors=[];addEventListener("error",e=>__qaErrors.push(e.message));addEventListener("unhandledrejection",e=>__qaErrors.push(String(e.reason)))')
def audit():
 row=js(AUDIT);assert not row['overflow'] and not row['bad'] and not row['errors'],row;return row
def close():call('press','Escape');settle()
def screen(name):call('screenshot',str(ROOT/f'docs/previews/round33-{name}.png'))

start();call('set','viewport','390','844');js('scrollTo({top:0,behavior:"instant"})');settle();call('click','[data-open-menu]');settle();audit()
grip=js('(()=>{const r=document.querySelector(".menu-grip").getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()')
for distance in [10,120]:
 call('mouse','move',str(round(grip['x'])),str(round(grip['y'])));call('mouse','down');call('mouse','move',str(round(grip['x'])),str(round(grip['y']+distance)));call('mouse','up');settle()
 assert js('document.querySelector("#mobile-menu").open')==(distance==10)
 assert js('document.querySelector("#mobile-menu").style.translate===""')
assert js('document.activeElement.matches("[data-open-menu]")')
report['sheetDrag']={'shortDragReturns':True,'longDragCloses':True,'focusRestored':True}
for width,height in [(320,568),(390,844),(768,600)]:
 call('set','viewport',str(width),str(height));call('click','[data-open-menu]');settle();audit();screen(f'menu-final-{width}')
 js('(()=>{const c=document.querySelector("#mobile-menu .surface-content");c.scrollTop=c.scrollHeight})()');settle()
 assert js('(()=>{const b=document.querySelector("#mobile-menu [data-dismiss]"),r=b.getBoundingClientRect();return r.top>=8&&r.bottom<=innerHeight-8&&document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest("[data-dismiss]")===b})()')
 call('click','#mobile-menu [data-dismiss]');settle();audit()
print('PASS sheet drag, rebound, focus and small-window clipping',flush=True)
call('set','viewport','320','568')
for master in js('[...document.querySelectorAll(".team-discover")].map(b=>b.dataset.teamOpen)'):
 selector=f'.team-discover[data-team-open="{master}"]';center(selector);call('click',selector);settle()
 js('(()=>{const c=document.querySelector(".team-dialog[open] .surface-content");c.scrollTop=c.scrollHeight})()');settle();audit()
 assert js('(()=>{const b=document.querySelector(".team-dialog[open] [data-dismiss]"),r=b.getBoundingClientRect();return r.top>=8&&r.bottom<=innerHeight-8&&document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest("[data-dismiss]")===b})()')
 call('click','.team-dialog[open] [data-dismiss]');settle()
report['stickyCloseProfiles']=6
print('PASS all six sticky profile close controls at the end of scrolling',flush=True)

call('set','viewport','390','844');center('#welcome-offer');assert js('document.querySelector(".mobile-nav").dataset.section')=='welcome-offer'
call('click','[data-dock-secondary]');settle();audit();assert js('document.querySelector(".promo-dialog").open');close()
center('.visit-ticket');assert js('document.querySelector(".mobile-nav").dataset.section')=='first-visit'
for selector,company in [('[data-dock-secondary]','2266404'),('[data-dock-primary]','2440449')]:
 call('click',selector);settle();assert company in js('document.querySelector("[data-booking-frame]").getAttribute("src")');close()
center('.of-rail');before=js('document.querySelector(".of-card[data-offer-active=true]").id');call('click','[data-dock-secondary]');settle();after=js('document.querySelector(".of-card[data-offer-active=true]").id');assert before!=after
report['extraContexts']={'promo':True,'honestPricePersonalRoutes':True,'offerNext':True}
print('PASS promo, honest-price personal destinations and offer paging',flush=True)

# Enlarge actual text runs, including controls, without shrinking type to fit.
call('set','viewport','320','844');js('''(()=>{const sizes=[...document.querySelectorAll('body *')].filter(e=>!e.closest('script,style,svg')&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())).map(e=>[e,parseFloat(getComputedStyle(e).fontSize)]);for(const [e,size] of sizes)e.style.fontSize=`${size*1.25}px`;})()''');settle()
for selector in ['.hero-scene','.sd-stack','.team-grid','.about-stack','.gifts-grid','.certificates','.reviews-board','.faq-list','.contact-layout','.footer']:
 center(selector);audit()
area=js('(()=>{const p=document.querySelector(".sd-card[aria-hidden=false]"),a=p.querySelector(".sd-service-area").getBoundingClientRect(),f=p.querySelector(".sd-face").getBoundingClientRect();return{bottom:a.bottom,face:f.bottom}})()');assert area['bottom']<=area['face']+1,area
call('click','[data-open-menu]');settle();audit();screen('menu-large-text-320');close()
report['textScale']=1.25
print('PASS 125 percent text with adaptive button and menu layout',flush=True)

start(BASE+'masters/sofya-shalaginova/')
for theme in ['light','dark']:
 call('select','.footer [data-theme-select]',theme)
 for width,height in [(320,568),(390,844),(540,844),(768,844),(960,600)]:
  call('set','viewport',str(width),str(height));js('scrollTo({top:0,behavior:"instant"})');settle();audit();assert js('document.querySelectorAll(".story-answer").length')==36
  center('.story-answer');audit()
  center('.story-actions');audit();call('click','[data-dock-primary]');settle();assert '1208807' in js('document.querySelector("[data-booking-frame]").getAttribute("src")');close();assert js('document.activeElement.matches("[data-dock-primary]")')
  report['article'].append({'theme':theme,'width':width,'height':height})
  if width==390:js('scrollTo({top:0,behavior:"instant"})');settle();screen(f'article-final-{theme}-390')
 print('PASS full article and personal booking',theme,flush=True)
call('click','[data-open-menu]');settle();call('click','.mobile-menu a[href="/#services"]');settle();assert js('location.pathname==="/"&&location.hash==="#services"')
save('iteration33-additional',report)
print('PASS article-to-home navigation',flush=True)
