"""Compare computed desktop appearance with the untouched pre-change static build."""
import functools,http.server,threading
from iteration18_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
class QuietHandler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
handler=functools.partial(QuietHandler,directory=str(ROOT/'tmp/baseline33/dist'))
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
old=f'http://127.0.0.1:{server.server_address[1]}/'
new='http://127.0.0.1:4321/'
SELECTORS='.site-header,.header-nav>a,.hero-heading,.hero-scene,.hero-news-panel,.first-visit,.cashback,.sd-card,.sd-summary,.team-card,.visit-ticket,.about-card,.gift-visual,.certificates,.reviews-board,.review-source,.faq-item,.contact-card,.footer-card,.footer-groups a'
ARTICLE='.site-header,.story-page,.story-cover,.story-heading,.story-body,.story-actions,.footer-card'
MEASURE_STYLE=r'''(()=>{const names=['fontFamily','fontSize','fontWeight','lineHeight','color','backgroundColor','borderRadius','padding','display','gridTemplateColumns','columnGap','rowGap','boxShadow'];return[...document.querySelectorAll(SELECTORS)].map(e=>{const s=getComputedStyle(e);return{key:e.className,styles:Object.fromEntries(names.map(name=>[name,s[name]]))}});})()'''
report=[]
try:
 for width,route in [(1024,''),(1440,''),(1920,''),(1440,'masters/sofya-shalaginova/')]:
  versions=[]
  for base in [old,new]:
   call('open',base+route);call('set','media','light','reduced-motion');call('set','viewport',str(width),'1000');settle();call('select','.footer [data-theme-select]','light');call('mouse','move','0','0');js('scrollTo({top:0,behavior:"instant"})');settle()
   versions.append(js(MEASURE_STYLE.replace('SELECTORS',json.dumps(ARTICLE if route else SELECTORS))))
  before,after=versions;assert len(before)==len(after),(len(before),len(after))
  changes=[{'before':a,'after':b} for a,b in zip(before,after) if a!=b]
  row={'width':width,'route':route,'elements':len(before),'changes':changes};report.append(row)
  assert not changes,json.dumps(row,ensure_ascii=True)
  print('PASS unchanged desktop computed appearance',width,route or '/',flush=True)
 save('iteration33-desktop-appearance',report)
finally:server.shutdown();server.server_close()
