"""Mobile rail ownership, personal dock routes and common review entry points.

Usage: python tests/iteration34-journeys.py [URL]
By default serves the immutable dist production build on a temporary
loopback port. Uses real Chromium; does not submit any external form.
"""
import sys,functools,http.server,threading,hashlib
from urllib.parse import urlparse
from iteration33_browser_helpers import *

call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz34-journeys','--json']
class QuietHandler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=None
artifact=ROOT/'dist'
if len(sys.argv)>1:
 BASE=sys.argv[1].rstrip('/')+'/'
else:
 assert (artifact/'index.html').exists(),'Build dist before running journeys'
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(artifact)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 BASE=f'http://127.0.0.1:{server.server_address[1]}/'
report={'base':BASE,'artifact':'dist' if server else 'explicit URL','indexSha256':hashlib.sha256((artifact/'index.html').read_bytes()).hexdigest() if server else None,'cases':[],'externalSubmission':False,'errors':[]}

def rail_settle(selector):
 return js('''(async()=>{const e=document.querySelector(SELECTOR);let old=e.scrollLeft,stable=0;for(let i=0;i<180;i++){await new Promise(r=>requestAnimationFrame(r));const now=e.scrollLeft;stable=Math.abs(now-old)<.1?stable+1:0;old=now;if(stable>=10)return now}throw Error('Rail did not settle: '+SELECTOR)})()'''.replace('SELECTOR',json.dumps(selector)))

def state(section,rail):
 return js('''(()=>{const root=document.querySelector(SECTION),r=root.querySelector(RAIL),items=[...r.children],active=items.findIndex(e=>e.dataset.mobileCurrent==='true');return{index:active,count:root.querySelector('[data-rail-count]').textContent,prev:root.querySelector('[data-rail-step="-1"]').disabled,next:root.querySelector('[data-rail-step="1"]').disabled,left:r.scrollLeft,max:r.scrollWidth-r.clientWidth,dock:document.querySelector('[data-mobile-nav]').dataset.section,primary:document.querySelector('[data-dock-primary]').getAttribute('aria-label'),positions:items.map(e=>({left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})),bounds:{left:r.getBoundingClientRect().left,right:r.getBoundingClientRect().right}}})()'''.replace('SECTION',json.dumps(section)).replace('RAIL',json.dumps(rail)))

def expect_index(section,rail,index):
 call('wait','--fn',f'document.querySelector({json.dumps(section+" [data-rail-count]")}).textContent.trim().startsWith({json.dumps(str(index+1).zfill(2))})')
 rail_settle(rail);settle()
 row=state(section,rail)
 assert row['count'].strip().startswith(str(index+1).zfill(2)),row
 if section=='#masters':assert row['index']==index,row
 return row

def reset(rail):
 js('document.querySelector('+json.dumps(rail)+').scrollTo({left:0,behavior:"instant"})');rail_settle(rail);settle()

def visible_selection(row):
 index=int(row['count'].strip().split('/')[0])-1
 overlap=[max(0,min(p['right'],row['bounds']['right'])-max(p['left'],row['bounds']['left'])) for p in row['positions']]
 assert overlap[index]>=max(overlap)-1,(row,overlap)
 return index

def audit():
 row=js(AUDIT)
 assert not row['overflow'] and not row['bad'] and not row['errors'],row
 assert not js('!!document.querySelector("vite-error-overlay,astro-error-overlay")'),'Development overlay interferes with test'

def personal_route(index):
 center('#masters [data-rail-count]');settle()
 expect_index('#masters','.team-grid',index)
 expected=js(f'document.querySelectorAll(".team-card .team-book")[{index}].dataset.bookingUrl')
 name=js(f'document.querySelectorAll(".team-card h3")[{index}].textContent.trim()')
 accessible=js('document.querySelector("[data-dock-primary]").getAttribute("aria-label")')
 call('click','[data-dock-primary]');settle()
 actual=js('document.querySelector("[data-booking-frame]").getAttribute("src")')
 assert urlparse(actual).hostname==urlparse(expected.replace('https://n','https://b')).hostname,(expected,actual)
 call('press','Escape');settle()
 assert not js('!!document.querySelector("dialog:modal")')
 assert js('document.activeElement.matches("[data-dock-primary]")')
 return {'index':index,'name':name,'dockAccessibleName':accessible,'source':expected,'iframeHost':urlparse(actual).hostname}

try:
 for width,height in [(390,844),(768,600),(960,1280),(960,540)]:
  call('open',BASE);call('set','media','light');call('set','viewport',str(width),str(height));settle()
  js('window.__qaErrors=[];addEventListener("error",e=>__qaErrors.push(e.message));addEventListener("unhandledrejection",e=>__qaErrors.push(String(e.reason)))')
  case={'width':width,'height':height,'masters':[],'routes':[],'gifts':[]}
  report['cases'].append(case)
  center('#masters [data-rail-count]');reset('.team-grid')
  row=expect_index('#masters','.team-grid',0);assert row['prev'] and not row['next'],row
  case['masters'].append(row)
  for index in range(1,6):
   call('click','#masters [data-rail-step="1"]')
   row=expect_index('#masters','.team-grid',index);case['masters'].append(row)
   if index in [1,5]:case['routes'].append(personal_route(index))
  assert row['next'] and not row['prev'],row
  call('screenshot',str(ROOT/f'docs/previews/round34-journeys-masters-last-{width}-{height}.png'))
  for index in range(4,-1,-1):
   call('click','#masters [data-rail-step="-1"]');expect_index('#masters','.team-grid',index)
  case['reverseMasters']=state('#masters','.team-grid')
  center('.team-grid');reset('.team-grid')
  second=state('#masters','.team-grid')
  if second['positions'][1]['left']>=second['bounds']['left']-.5 and second['positions'][1]['right']<=second['bounds']['right']+.5:
   call('click','.team-card:nth-child(2) h3');expect_index('#masters','.team-grid',1)
   case['secondCardTap']=personal_route(1)
  call('focus','.team-card:nth-child(3) .team-portrait');expect_index('#masters','.team-grid',2)
  case['thirdCardFocus']=personal_route(2)
  # A real horizontal wheel input interrupts/follows the arrow's native smooth scroll.
  reset('.team-grid');call('click','#masters [data-rail-step="1"]')
  before=state('#masters','.team-grid');call('scroll','left','450','--selector','.team-grid');rail_settle('.team-grid');settle()
  after=state('#masters','.team-grid')
  visible_selection(after)
  case['manualScrollAfterArrow']={'before':before,'after':after}
  if js('document.querySelector(".gifts-grid").scrollWidth>document.querySelector(".gifts-grid").clientWidth+1'):
   center('#gifts [data-rail-count]');reset('.gifts-grid')
   row=expect_index('#gifts','.gifts-grid',0);assert row['prev'],row
   for index in range(1,6):
    call('click','#gifts [data-rail-step="1"]');row=expect_index('#gifts','.gifts-grid',index);case['gifts'].append(row)
   assert row['next'],row
   for index in range(4,-1,-1):
    call('click','#gifts [data-rail-step="-1"]');expect_index('#gifts','.gifts-grid',index)
   case['reverseGifts']=state('#gifts','.gifts-grid')
   call('click','#gifts [data-rail-step="1"]');call('scroll','right','1000','--selector','.gifts-grid');rail_settle('.gifts-grid');settle()
   right=state('#gifts','.gifts-grid');visible_selection(right)
   call('scroll','left','1000','--selector','.gifts-grid');rail_settle('.gifts-grid');settle()
   left=state('#gifts','.gifts-grid');visible_selection(left)
   case['giftsManualScroll']={'right':right,'left':left}
  else:
   assert js('document.querySelector("[data-rail-controls=gifts-rail]").hidden')
   case['giftsAllVisible']=True
  center('.of-card[data-offer-active="true"] .of-action');call('click','.of-card[data-offer-active="true"] .of-action');settle()
  assert js('document.querySelector("#review-dialog").open'),'Offer review CTA does not open shared review choice'
  call('press','Escape');settle();center('.of-rail');call('click','[data-dock-primary]');settle()
  assert js('document.querySelector("#review-dialog").open'),'Dock offer action does not open shared review choice'
  call('press','Escape');settle();audit();case['reviews']={'offerAction':True,'dock':True}
  print('PASS journeys',width,height,flush=True)
 if server:
  assert hashlib.sha256((artifact/'index.html').read_bytes()).hexdigest()==report['indexSha256'],'Production build changed during verification'
 report['status']='passed'
except Exception as error:
 report['status']='failed';report['errors'].append(str(error))
 call('screenshot',str(ROOT/'docs/previews/round34-journeys-failure.png'))
 raise
finally:
 save('iteration34-journeys',report)
 if server:server.shutdown();server.server_close()
