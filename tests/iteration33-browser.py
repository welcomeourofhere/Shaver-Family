"""Mobile redesign: layout, contextual actions, native sheets and desktop preservation."""
import sys
from iteration33_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
part=sys.argv[1] if len(sys.argv)>1 else 'layout'
BASE='http://127.0.0.1:4321/'
call('open',BASE+'?qa=33-final');call('set','media','light');settle();call('select','.footer [data-theme-select]','light')
js('window.__qaErrors=[];addEventListener("error",e=>__qaErrors.push(e.message));addEventListener("unhandledrejection",e=>__qaErrors.push(String(e.reason)))')
report={'rows':[],'externalSubmission':False}

def audit():
 row=js(AUDIT);assert not row['overflow'] and not row['bad'] and not row['errors'],row
 if row['dock']['suppressed']!='true':assert row['dock']['left']>=11.9 and row['dock']['right']<=row['width']-11.9 and row['dock']['bottom']<=row['height']-11.9,row
 return row
def screen(name):call('screenshot',str(ROOT/f'docs/previews/round33-{name}.png'))
def close_window():call('press','Escape');settle();assert not js('!!document.querySelector("dialog:modal")')
def context(selector,expected):
 center(selector);row=audit();assert row['context']==expected,row;return row

if part=='layout':
 for theme in ['light','dark']:
  call('select','.footer [data-theme-select]',theme)
  for width in [320,360,390,430,540,650,768,800,960]:
   call('set','viewport',str(width),'844');js('scrollTo({top:0,behavior:"instant"})');settle()
   row=audit()
   hero=js('(()=>{const r=document.querySelector(".hero-scene").getBoundingClientRect(),h=document.querySelector(".hero-heading").getBoundingClientRect(),c=document.querySelector(".hero-mobile-copy").getBoundingClientRect(),p=document.querySelector(".hero-news-panel").getBoundingClientRect(),d=document.querySelector(".mobile-nav").getBoundingClientRect();return{top:r.top,width:r.width,height:r.height,titleBottom:h.bottom,copyTop:c.top,copyBottom:c.bottom,newsTop:p.top,newsBottom:p.bottom,dockTop:d.top}})()')
   assert hero['top']==0 and abs(hero['width']-width)<1 and abs(hero['height']-844)<1,hero
   assert hero['titleBottom']<=hero['copyTop'] and hero['copyBottom']<=hero['newsTop'] and hero['newsBottom']<=hero['dockTop']-7,hero
   for selector in ['.sd-stack','.of-rail','.team-grid','.visit-ticket','.about-stack','.gifts-grid','.certificates','.reviews-board','.faq-list','.contact-layout','.footer-card']:
    center(selector);audit()
   report['rows'].append({'theme':theme,'width':width,'hero':hero})
   if width in [320,390,768]:
    js('scrollTo({top:0,behavior:"instant"})');settle();screen(f'hero-{theme}-{width}')
    for selector,name in [('.team-grid','masters'),('.about-stack','about'),('.visit-ticket','visit'),('.contact-layout','contacts')]:center(selector);screen(f'{name}-{theme}-{width}')
   print('PASS all mobile sections and labels',theme,width,flush=True)
  for width,height in [(667,375),(844,390),(960,540)]:
   call('set','viewport',str(width),str(height));js('scrollTo({top:0,behavior:"instant"})');settle();row=audit()
   h=js('({title:document.querySelector(".hero-heading").getBoundingClientRect().bottom,news:document.querySelector(".hero-news-panel").getBoundingClientRect().top})');assert h['title']<=h['news'],h
   report['rows'].append({'landscape':True,**row})
   if width==844:screen(f'hero-landscape-{theme}')
 print('PASS mobile portrait and landscape layouts',flush=True)
 # Repeat the saved desktop geometry in the same deterministic reduced-motion state.
 call('set','media','light','reduced-motion');call('select','.footer [data-theme-select]','light')
 baseline=json.loads((ROOT/'tmp/planning/iteration33-desktop-baseline.json').read_text(encoding='utf-8'))
 report['desktop']=[]
 for old in baseline:
  call('set','viewport',str(old['width']),'1000');js('scrollTo({top:0,behavior:"instant"})');settle()
  now=js('({width:innerWidth,rects:[...document.querySelectorAll("main>section,.site-header,.team-card,.gift-visual,.certificate-scene,.contact-layout,.footer")].map(e=>({key:e.id||e.className,x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y+scrollY,w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height}))})')
  assert len(old['rects'])==len(now['rects'])
  for a,b in zip(old['rects'],now['rects']):assert all(abs(a[k]-b[k])<.1 for k in ['x','y','w','h']),(a,b)
  audit();report['desktop'].append({'width':old['width'],'geometryUnchanged':True})
 print('PASS unchanged desktop geometry 1024/1440/1920',flush=True)

if part=='actions':
 call('set','viewport','390','844');js('scrollTo({top:0,behavior:"instant"})');settle()
 call('click','.hero-news-toggle');settle();assert js('document.querySelector(".hero-news-toggle").getAttribute("aria-expanded")==="true"');audit()
 call('press','Escape');settle();assert js('document.querySelector(".hero-news-toggle").getAttribute("aria-expanded")==="false"')
 call('click','[data-open-menu]');settle();audit();assert js('document.querySelector(".mobile-nav").inert')
 screen('menu-390');close_window();assert js('document.activeElement.matches("[data-open-menu]")')
 context('.sd-stack','services');call('click','[data-dock-secondary]');settle();audit();screen('categories-390')
 for index in range(5):
  if index:call('click','[data-dock-secondary]');settle()
  call('click',f'[data-dock-category="{index}"]');settle()
  assert js('document.querySelector('+json.dumps(f'[data-sd-tab="{index}"]')+').getAttribute("aria-selected")==="true"')
  assert js('document.querySelector(".sd-card[aria-hidden=false] details").open')
  assert js('document.activeElement.matches("[data-dock-secondary]")')
 context('.sd-stack','services');call('click','[data-dock-primary]');settle();assert js('document.querySelector("[data-booking-drawer]").open');close_window();assert js('document.activeElement.matches("[data-dock-primary]")')
 print('PASS hero disclosure, native menu, five categories, booking and focus',flush=True)
 context('.team-grid','masters')
 master_ids=js('[...document.querySelectorAll(".team-book")].filter(b=>b.closest(".team-card")).map(b=>b.dataset.master)')
 for index,master in enumerate(master_ids):
  js(f'(()=>{{const r=document.querySelector(".team-grid"),c=r.children[{index}];r.scrollTo({{left:r.scrollLeft+c.getBoundingClientRect().left-r.getBoundingClientRect().left,behavior:"instant"}})}})()');settle()
  assert js(f'document.querySelector(".team-card:nth-child({index+1})").dataset.mobileCurrent==="true"')
  call('click','[data-dock-primary]');settle()
  expected=js(f'document.querySelector(".team-card:nth-child({index+1}) .team-book").dataset.bookingUrl')
  got=js('document.querySelector("[data-booking-frame]").getAttribute("src")');assert expected.replace('https://n','https://b').rstrip('/') in got,(expected,got)
  close_window();assert js('document.activeElement.matches("[data-dock-primary]")')
  call('click','[data-dock-secondary]');settle();audit();assert js(f'document.querySelector("#team-dialog-{master}").open');close_window();assert js('document.activeElement.matches("[data-dock-secondary]")')
 print('PASS all six native gallery selections, interviews and personal booking destinations',flush=True)
 context('.about-stack','about')
 for index in range(4):
  call('click',f'[data-about-tab="{index}"]');settle()
  # Native smooth scrolling finishes on its observed selected state.
  call('wait','--fn',f'document.querySelector("[data-about-tab=\\"{index}\\"]").getAttribute("aria-selected")==="true"')
  call('click',f'.about-layer:nth-child({index+1}) [data-about-more]');settle();audit()
  assert js(f'document.querySelector(".about-layer:nth-child({index+1}) [data-about-more]").getAttribute("aria-expanded")==="true"')
  call('click',f'.about-layer:nth-child({index+1}) [data-about-more]');settle()
 context('.reviews-board','reviews');call('click','[data-dock-primary]');settle();audit();assert js('document.querySelector("#review-dialog").open');screen('review-choice-390');close_window()
 context('.certificates','certificates');call('click','[data-dock-secondary]');settle();assert js('!!document.querySelector("[data-certificate][aria-pressed=true]")')
 call('click','[data-dock-primary]');settle();assert js('document.querySelector(".contact-dialog").open');close_window()
 context('.contact-layout','contacts');call('click','[data-dock-secondary]');settle();assert js('document.querySelector(".contact-dialog").open');close_window()
 print('PASS expandable About, review choice, certificates and shared contact dialog',flush=True)
 call('set','media','light','reduced-motion');context('.team-grid','masters');audit();call('click','[data-dock-secondary]');settle();close_window()
 print('PASS reduced motion and restored focus',flush=True)

report['errors']=js('__qaErrors');assert not report['errors'],report['errors']
save('iteration33-'+part,report)
