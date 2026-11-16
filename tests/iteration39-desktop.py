"""Keep desktop geometry and typography; only selected service colours intentionally change."""
import functools,http.server,os,threading
from iteration33_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
class QuietHandler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(ROOT/os.environ.get('QA_BASELINE','tmp/baseline39/dist'))))
threading.Thread(target=server.serve_forever,daemon=True).start()
old=f'http://127.0.0.1:{server.server_address[1]}/';new=os.environ.get('QA_URL','http://127.0.0.1:4321/')
selectors='.site-header,.header-nav>a,.section-title,.hero-heading,.hero-scene,.hero-news-panel,.first-visit,.cashback,.sd-card,.sd-summary,.team-card,.visit-ticket,.about-card,.gift-visual,.certificates,.reviews-board,.review-source,.faq-item,.contact-card,.footer-card,.footer-groups a,.of-intro,.of-controls,.of-position,.of-rail,.of-card,.of-slider'
article='.site-header,.story-page,.story-cover,.story-heading,.story-body,.story-actions,.footer-card'
measure=r'''(()=>{const names=['fontFamily','fontSize','fontWeight','lineHeight','color','backgroundColor','borderRadius','padding','display','gridTemplateColumns','columnGap','rowGap','boxShadow','textAlign'];return[...document.querySelectorAll(SELECTORS)].map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return{kind:e.matches('.sd-summary')?'service':'layout',width:r.width,height:r.height,styles:Object.fromEntries(names.map(n=>[n,s[n]]))}})})()'''
report=[]
try:
 for width,route in [(1024,''),(1440,''),(1920,''),(1440,'masters/sofya-shalaginova/')]:
  if route and os.environ.get('QA_DESKTOP_HOME_ONLY'):continue
  versions=[]
  for base in [old,new]:
   call('open',base+route);call('set','media','light','reduced-motion');call('set','viewport',str(width),'1000');settle()
   call('select','.footer [data-theme-select]','light');call('mouse','move','0','0');js('scrollTo({top:0,behavior:"instant"})');settle()
   versions.append(js(measure.replace('SELECTORS',json.dumps(article if route else selectors))))
  before,after=versions;assert len(before)==len(after)
  changes=[]
  for a,b in zip(before,after):
   assert abs(a['width']-b['width'])<.6 and abs(a['height']-b['height'])<.6,(width,route,a,b)
   changed=[name for name in a['styles'] if a['styles'][name]!=b['styles'][name]]
   if changed:assert a['kind']=='service' and changed==['color'],(width,route,a,b)
   if changed:changes.append({'kind':'selected service foreground','before':a['styles']['color'],'after':b['styles']['color']})
  if not route:
   heads=js("[...document.querySelectorAll('.section-title')].map(e=>({id:e.id,aside:e.classList.contains('section-title--aside'),align:getComputedStyle(e).textAlign}))")
   assert all(h['align']==('left' if h['aside'] else 'center') for h in heads),heads
  report.append({'width':width,'route':route or '/','elements':len(before),'intentionalChanges':changes})
  print('PASS desktop geometry/typography and explicit heading exceptions',width,route or '/',flush=True)
 save(os.environ.get('QA_REPORT_PREFIX','iteration39')+'-desktop',report)
finally:server.shutdown();server.server_close()
