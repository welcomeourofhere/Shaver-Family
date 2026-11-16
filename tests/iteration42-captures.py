"""Capture reviewed mobile states from the built artifact, without external writes."""
import functools,http.server,threading
from iteration33_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
class QuietHandler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(ROOT/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_address[1]}/';states=[]
try:
 for selector,name,expanded in [('.cashback','cashback-390',False),('.of-rail','offers-dock-390',False),('.about-section','about-390',False),('.about-copy','about-expanded-390',True)]:
  call('open',base+'?capture42='+name);call('set','media','light','reduced-motion');call('set','viewport','390','1000');settle();call('select','.footer [data-theme-select]','light')
  if expanded:js('document.querySelector("[data-about-more]").click()');settle()
  if selector=='.about-section':js('scrollTo({top:document.querySelector(".about-section").getBoundingClientRect().top+scrollY-24,behavior:"instant"})');settle()
  else:center(selector)
  js('Promise.allSettled([...document.images].filter(i=>{const r=i.getBoundingClientRect();return r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth&&getComputedStyle(i).visibility!=="hidden"}).map(i=>{i.loading="eager";return i.decode()}))');settle()
  states.append({'name':name,'expanded':js('[...document.querySelectorAll("[data-about-more]")].map(e=>e.getAttribute("aria-expanded"))'),'dock':js('document.querySelector("[data-mobile-nav]").dataset.section')})
  call('screenshot',str(ROOT/f'docs/previews/round42-{name}.png'));print('CAPTURE',name,flush=True)
 save('iteration42-captures',states)
finally:server.shutdown();server.server_close()
