"""Local checks for the shared surfaces, booking chrome and complete master article."""
import sys
from iteration18_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
part=sys.argv[1] if len(sys.argv)>1 else 'main'
report={'rows':[],'externalSubmission':False}
BASE='http://127.0.0.1:4321/'
call('open',BASE+('masters/sofya-shalaginova/' if part=='article' else '?qa=32'))
call('reload');call('set','media','light');settle()
js('window.__errors=[];addEventListener("error",e=>__errors.push(e.message));addEventListener("unhandledrejection",e=>__errors.push(String(e.reason)))')
BUTTONS=r'''(()=>{const bad=[],range=document.createRange();for(const b of document.querySelectorAll('button,.btn,.text-btn')){const z=b.getBoundingClientRect(),s=getComputedStyle(b);if(!z.width||!z.height||b.closest('dialog:not([open]),[hidden],[inert]'))continue;if(z.height<43.9)bad.push('hit:'+b.textContent.trim());if(b.matches('.hero-edge,.hero-dot,.icon-btn,.certificate-object,.gift-visual')||b.querySelector('img')||!b.textContent.trim())continue;if(b.scrollWidth>b.clientWidth+1||parseFloat(s.paddingLeft)<12||parseFloat(s.paddingRight)<12)bad.push('label:'+b.textContent.trim());const walker=document.createTreeWalker(b,NodeFilter.SHOW_TEXT);while(walker.nextNode()){if(!walker.currentNode.textContent.trim())continue;range.selectNodeContents(walker.currentNode);if(range.getClientRects().length>1)bad.push('wrap:'+walker.currentNode.textContent);}}return{bad,overflow:document.documentElement.scrollWidth>innerWidth+1,width:innerWidth,theme:document.documentElement.dataset.theme}})()'''
VISIT=r'''(async()=>{const r=e=>e.getBoundingClientRect(),ticket=document.querySelector('.visit-ticket'),image=ticket.querySelector('.visit-art img');await image.decode();const t=r(ticket),i=r(image),title=r(document.querySelector('#visit-title')),copy=ticket.querySelector('.visit-copy'),right=Math.max(...[...copy.children].map(e=>r(e).right)),s=Math.min(i.width/image.naturalWidth,i.height/image.naturalHeight),center=i.left+i.width/2,ray=t.left+parseFloat(getComputedStyle(ticket.querySelector('.visit-rays')).left);return{width:innerWidth,midpoint:(right+t.right)/2,portraitCenter:center,rayCenter:ray,headClearance:i.bottom-image.naturalHeight*s-title.bottom,gap:t.top-title.bottom,expectedGap:parseFloat(getComputedStyle(document.querySelector('#visit-title')).marginBottom)}})()'''
SURFACE=r'''(()=>{const d=document.querySelector('dialog[open]:not(.booking-drawer)'),v=d.querySelector('.surface-viewport'),c=d.querySelector('.surface-content'),r=e=>e.getBoundingClientRect(),z=r(d),q=r(v),s=getComputedStyle(v);return{width:innerWidth,rootScrollbar:getComputedStyle(document.documentElement).scrollbarWidth,scrollbar:getComputedStyle(c).scrollbarWidth,overflow:s.overflow,radius:s.borderRadius,inside:q.left>=z.left-.1&&q.right<=z.right+.1&&q.top>=z.top-.1&&q.bottom<=z.bottom+.1,horizontal:c.scrollWidth>c.clientWidth+1,scrollable:c.scrollHeight>c.clientHeight,bodyScrollable:getComputedStyle(document.documentElement).overflow}})()'''
HEADER=r'''(()=>{const h=document.querySelector('.site-header'),c=h.querySelector('.header-capsule'),s=h.querySelector('.header-shape'),r=c.getBoundingClientRect();return{y:scrollY,floating:h.classList.contains('is-floating'),hidden:h.classList.contains('is-hidden'),scale:parseFloat(getComputedStyle(c).scale),shadow:getComputedStyle(s).boxShadow,tint:c.style.getPropertyValue('--shadow-tint'),left:r.left,right:r.right,width:innerWidth}})()'''

if part=='main':
 for theme in ['light','dark']:
  call('select','.footer [data-theme-select]',theme)
  for width in [320,390,540,768,960,961,1024,1280,1440,1920]:
   call('set','viewport',str(width),'1000');center('.visit-ticket')
   v=js(VISIT);g=js(MEASURE);buttons=js(BUTTONS)
   assert not g['overflow'] and not g['issues'] and not buttons['bad'],(g,buttons)
   assert v['headClearance']>=10 and abs(v['gap']-v['expectedGap'])<.1,v
   if width>960:
    assert abs(v['portraitCenter']-v['midpoint'])<1 and abs(v['rayCenter']-v['portraitCenter'])<1,v
   report['rows'].append({'theme':theme,'visit':v,'buttons':buttons})
   if width in [390,1440]:call('screenshot',str(ROOT/f'docs/previews/round32-visit-{theme}-{width}.png'))
  print('PASS main geometry, labels, portrait/ray centers',theme,flush=True)
 for width in [320,1440]:
  call('set','viewport',str(width),'1000');center('.sd-stack')
  assert js('[...document.querySelectorAll(".sd-card")].every(p=>p.querySelectorAll("details[open]").length===1&&p.querySelector("details").open)')
  for category in range(5):
   js(f'document.querySelectorAll("[data-sd-tab]")[{category}].click()');settle()
   assert js('document.querySelector(".sd-card[aria-hidden=false] details").open')
   base=js('document.querySelector(".sd-stack").getBoundingClientRect().height')
   count=js('document.querySelector(".sd-card[aria-hidden=false]").querySelectorAll("details").length')
   if count>1:
    js('document.querySelector(".sd-card[aria-hidden=false]").querySelectorAll("summary")[1].click()');settle()
    assert js('document.querySelector(".sd-card[aria-hidden=false]").querySelectorAll("details")[1].open')
    js('document.querySelector(".sd-card[aria-hidden=false]").querySelectorAll("summary")[1].click()');settle()
    assert js('document.querySelector(".sd-card[aria-hidden=false]").querySelectorAll("details[open]").length===1')
    assert js('''(async()=>{const p=document.querySelector('.sd-card[aria-hidden=false]'),row=p.querySelector('details[open]');for(let i=0;i<100;i++){const image=p.querySelector('[data-photo-current=true]');if(image?.getAttribute('src')===row.dataset.photoSrc&&image.complete&&image.naturalWidth)return true;await new Promise(r=>setTimeout(r,20));}return false})()''')
   assert abs(js('document.querySelector(".sd-stack").getBoundingClientRect().height')-base)<.1
   js(f'document.querySelectorAll("[data-sd-tab]")[{(category+1)%5}].click()');settle()
   js(f'document.querySelectorAll("[data-sd-tab]")[{category}].click()');settle()
   assert js('document.querySelector(".sd-card[aria-hidden=false] details").open')
  print('PASS service disclosure, photos and stable heights',width,flush=True)
 for width in [961,1280,1440,1920]:
  call('set','viewport',str(width),'1000');js('document.activeElement.blur();scrollTo({top:0,behavior:"instant"})');settle()
  top=js(HEADER);assert top['scale']==1 and top['shadow']=='none' and not top['hidden'],top
  js('scrollTo({top:34,behavior:"instant"})');settle();floating=js(HEADER)
  assert floating['floating'] and abs(floating['scale']-1.03)<.001 and floating['shadow']!='none',floating
  assert floating['left']>=0 and floating['right']<=width,floating
  js('scrollTo({top:20,behavior:"instant"})');settle();assert js(HEADER)['floating']
  js('scrollTo({top:12,behavior:"instant"})');settle();assert js(HEADER)['scale']==1
  js('scrollTo({top:800,behavior:"instant"})');settle();assert js(HEADER)['hidden']
  js('scrollTo({top:720,behavior:"instant"})');settle();assert not js(HEADER)['hidden']
  report.setdefault('headers',[]).append({'top':top,'floating':floating})
 call('set','viewport','1440','1000');call('select','.footer [data-theme-select]','light')
 js('scrollTo({top:document.querySelector(".visit-ticket").getBoundingClientRect().top+scrollY+120,behavior:"instant"})');settle()
 js('scrollBy({top:-40,behavior:"instant"})');settle();red=js(HEADER)
 js('scrollTo({top:34,behavior:"instant"})');settle();paper=js(HEADER)
 assert red['shadow']!=paper['shadow'] and red['tint']!=paper['tint'],(red,paper)
 local=js('({red:getComputedStyle(document.querySelector(".visit-ticket")).getPropertyValue("--shadow-color"),blue:getComputedStyle(document.querySelector(".certificates")).getPropertyValue("--shadow-color")})')
 assert local['red']!=local['blue'],local
 report['shadows']={'red':red,'paper':paper,'local':local}
 print('PASS floating header, hysteresis, direction and actual shadow tints',flush=True)
 # Check all profile windows and the sticky close button at both scroll ends.
 for width in [320,1440]:
  call('set','viewport',str(width),'1000')
  ids=js('[...document.querySelectorAll(".team-discover")].map(b=>b.dataset.teamOpen)')
  for master in ids:
   selector=f'.team-discover[data-team-open="{master}"]';center(selector);call('click',selector);settle()
   surface=js(SURFACE);assert surface['scrollbar']==surface['rootScrollbar']=='thin' and surface['overflow']=='hidden' and surface['inside'] and not surface['horizontal'],surface
   report.setdefault('surfaces',[]).append({'master':master,**surface})
   if master=='souz-sofya-shalaginova':
    assert js('document.querySelector(".team-story-dialog").querySelectorAll(".story-answer").length')==36
    call('screenshot',str(ROOT/f'docs/previews/round32-story-dialog-top-{width}.png'))
    js('(()=>{const c=document.querySelector(".team-story-dialog .surface-content");c.scrollTop=c.scrollHeight})()');settle()
    assert not js(BUTTONS)['bad'],js(BUTTONS)
    call('screenshot',str(ROOT/f'docs/previews/round32-story-dialog-end-{width}.png'))
    call('click','.team-story-dialog [data-dismiss]');settle()
   else:call('press','Escape');settle()
   assert not js('!!document.querySelector(".team-dialog[open]")')
  print('PASS six profile windows and clipped thin scrollbars',width,flush=True)

if part=='article':
 for theme in ['light','dark']:
  call('select','.footer [data-theme-select]',theme)
  for width in [320,390,540,768,960,961,1024,1440,1920]:
   call('set','viewport',str(width),'1000');settle();g=js(BUTTONS)
   assert not g['bad'] and not g['overflow'],g
   assert js('document.querySelectorAll(".story-answer").length===36&&document.querySelectorAll(".story-photo-grid img").length===21&&document.querySelectorAll("h1").length===1')
   assert js('[...document.querySelectorAll(".header-nav a,.mobile-nav a,.footer nav a")].every(a=>a.getAttribute("href").startsWith("/#"))')
   js('scrollTo({top:0,behavior:"instant"})');settle()
   if width in [390,1440]:call('screenshot',str(ROOT/f'docs/previews/round32-article-top-{theme}-{width}.png'))
   center('.story-answer');assert not js(BUTTONS)['bad']
   if width in [390,1440]:call('screenshot',str(ROOT/f'docs/previews/round32-article-text-{theme}-{width}.png'))
   report['rows'].append(g)
  print('PASS standalone article hierarchy, routes and labels',theme,flush=True)
 for index in range(js('document.querySelectorAll(".story-photo-grid img").length')):
  js(f'document.querySelectorAll(".story-photo-grid img")[{index}].scrollIntoView({{block:"center",behavior:"instant"}})')
  assert js(f'(async()=>{{const i=document.querySelectorAll(".story-photo-grid img")[{index}];await i.decode();return i.complete&&i.naturalWidth>0&&!!i.alt}})()')
 print('PASS all 22 article photos loaded including cover',flush=True)

# The same drawer is present on both pages. Open only; no provider interaction.
for width in [320,390,540,541,560,768,1280,1440,1920]:
 call('set','viewport',str(width),'1000')
 trigger='.story-actions [data-booking]' if part=='article' else '.team-book[data-master="souz-sofya-shalaginova"]'
 center(trigger);call('click',trigger);settle()
 drawer=js('''(()=>{const d=document.querySelector('[data-booking-drawer]'),p=d.querySelector('.booking-panel'),b=d.querySelector('.booking-close'),f=d.querySelector('iframe'),r=e=>e.getBoundingClientRect(),z=r(b),q=r(p),i=r(f);return{open:d.open,width:innerWidth,layout:d.dataset.layout,close:{left:z.left,right:z.right,height:z.height},panelLeft:q.left,frame:{top:i.top,height:i.height,bottom:i.bottom},viewportHeight:innerHeight,head:!!d.querySelector('.booking-head'),tools:!!d.querySelector('.booking-provider-tools'),url:f.getAttribute('src'),context:d.querySelector('[data-booking-selection]').textContent,closeReachable:document.elementFromPoint(z.left+z.width/2,z.top+z.height/2)?.closest('[data-booking-close]')===b}})()''')
 assert drawer['open'] and drawer['frame']['top']==0 and abs(drawer['frame']['height']-drawer['viewportHeight'])<1 and not drawer['head'] and not drawer['tools'],drawer
 assert 'b1208807.yclients.ru' in drawer['url'] and drawer['close']['left']>=0 and drawer['closeReachable'] and drawer['close']['height']>=44,drawer
 if width>560:assert drawer['close']['right']<drawer['panelLeft'],drawer
 if width in [390,1440]:call('screenshot',str(ROOT/f'docs/previews/round32-booking-{part}-{width}.png'))
 call('click','[data-booking-close]');settle();assert not js('document.querySelector("[data-booking-drawer]").open')
 assert js('document.activeElement.matches('+json.dumps(trigger)+')')
 report.setdefault('booking',[]).append(drawer)
print('PASS full-height booking, reachable left close and focus restoration',part,flush=True)
call('set','media','light','reduced-motion');call('set','viewport','390','844');center('.story-actions' if part=='article' else '.visit-ticket')
assert not js(BUTTONS)['bad'] and not js(BUTTONS)['overflow']
call('set','media','light');call('select','.footer [data-theme-select]','light');call('set','viewport','1440','1000')
report['errors']=js('__errors');assert not report['errors'],report['errors']
save('iteration32-'+part,report)
print('PASS reduced motion and clean local JavaScript',part,flush=True)
