"""Enlarge existing text runs to 200%; this is not browser zoom or a hardware test."""
from iteration33_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz34-text','--json']
BASE='http://127.0.0.1:4321/'
SCALE=r'''(()=>{const sizes=[...document.querySelectorAll('body *')].filter(e=>!e.closest('script,style,svg')&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())).map(e=>[e,parseFloat(getComputedStyle(e).fontSize)]);for(const [e,size] of sizes)e.style.fontSize=`${size*2}px`;})()'''
report={'textScale':2,'method':'double computed size of existing text runs; not browser zoom','rows':[],'externalSubmission':False}

def inspect(scope='body'):
 return js(r'''(()=>{const scope=document.querySelector(SCOPE),bad=[],range=document.createRange();
 for(const b of scope.querySelectorAll('button,.btn,.text-btn,summary,.contact-channel,.footer-groups a')){
 const r=b.getBoundingClientRect(),s=getComputedStyle(b);if(!r.width||!r.height||s.visibility==='hidden'||b.closest('dialog:not([open]),[hidden],[inert]'))continue;
 const name=b.className+':'+b.textContent.trim().replace(/\s+/g,' ').slice(0,80);
 if(r.height<43.9)bad.push({kind:'hit',name});
 if(b.matches('.hero-edge,.hero-dot,.icon-btn,.certificate-object,.gift-visual,.dock-menu,.sd-summary')||b.querySelector('img')||!b.textContent.trim())continue;
 if(b.scrollWidth>b.clientWidth+1||parseFloat(s.paddingLeft)<12||parseFloat(s.paddingRight)<12)bad.push({kind:'label',name,width:r.width,scroll:b.scrollWidth});
 const nodes=document.createTreeWalker(b,NodeFilter.SHOW_TEXT);while(nodes.nextNode()){if(!nodes.currentNode.textContent.trim())continue;const parent=nodes.currentNode.parentElement;if(!parent.getClientRects().length)continue;range.selectNodeContents(nodes.currentNode);if(range.getClientRects().length>1)bad.push({kind:'wrap',name});}}
 const content=[...scope.querySelectorAll('h1,h2,h3,p,.sd-face,.team-copy,.about-copy,.contact-card,.surface-content')].filter(e=>{if(e.classList.contains('sr-only'))return false;const r=e.getBoundingClientRect();return r.width&&r.height&&!e.closest('dialog:not([open]),[hidden],[inert]')&&e.scrollWidth>e.clientWidth+1}).map(e=>({name:e.className||e.tagName,width:e.clientWidth,scroll:e.scrollWidth}));
 return{bad,content,overflow:document.documentElement.scrollWidth>innerWidth+1,errors:window.__qaErrors||[]};})()'''.replace('SCOPE',json.dumps(scope)))

def row(route,width,height,state,scope='body'):
 result={'route':route,'width':width,'height':height,'state':state,**inspect(scope)}
 report['rows'].append(result)
 print(json.dumps(result,ensure_ascii=True),flush=True)

def screen(name):call('screenshot',str(ROOT/f'docs/previews/round34-text-{name}.png'))

for route in ['', 'masters/sofya-shalaginova/']:
 for width,height in [(320,568),(390,844)]:
  call('open',BASE+route+'?qa=34-text');call('set','media','light','reduced-motion');call('set','viewport',str(width),str(height));settle();call('select','.footer [data-theme-select]','light')
  js('window.__qaErrors=[];addEventListener("error",e=>__qaErrors.push(e.message));addEventListener("unhandledrejection",e=>__qaErrors.push(String(e.reason)))')
  js(SCALE);settle();js('scrollTo({top:0,behavior:"instant"})');settle()
  row(route,width,height,'page');screen(('article' if route else 'hero')+f'-{width}')
  if not route:
   center('.hero-news-toggle');call('click','.hero-news-toggle');settle();row(route,width,height,'news','.hero-news-panel');screen(f'news-{width}');call('press','Escape');settle()
   for selector,name in [('.contact-layout','contacts'),('.reviews-board','reviews')]:
    center(selector);row(route,width,height,name);screen(f'{name}-{width}')
   call('click','.reviews-board [data-open-reviews]');settle();row(route,width,height,'review-dialog','#review-dialog');screen(f'review-dialog-{width}');call('press','Escape');settle()
   center('.contact-layout');call('click','.footer-phone');settle();row(route,width,height,'contact-dialog','#contact-dialog');screen(f'contact-dialog-{width}');call('press','Escape');settle()
   center('.sd-stack');call('click','[data-dock-secondary]');settle();row(route,width,height,'categories','#service-categories');screen(f'categories-{width}');call('press','Escape');settle()
   center('#welcome-offer');call('click','[data-dock-secondary]');settle();row(route,width,height,'promo','#promo-dialog');screen(f'promo-{width}');call('press','Escape');settle()
  else:
   center('.story-actions');row(route,width,height,'article-actions');screen(f'article-actions-{width}')
  call('click','[data-open-menu]');settle();row(route,width,height,'menu','#mobile-menu');screen(('article-menu' if route else 'menu')+f'-{width}');call('press','Escape');settle()
failures=[row for row in report['rows'] if row['bad'] or row['content'] or row['overflow'] or row['errors']]
report['status']='failed' if failures else 'passed'
save('iteration34-text',report)
assert not failures, 'Text resize evidence contains failures'
print(f'PASS 200 percent text, {len(report["rows"])} page/dialog states',flush=True)
