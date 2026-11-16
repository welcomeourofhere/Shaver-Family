import os
from iteration33_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
base=os.environ.get('QA_URL','http://127.0.0.1:4321/')
for width,height,selector,name in [(390,844,'.hero-scene','hero-390'),(390,1000,'.sd-section','services-390'),(390,1000,'.hero-asides','promotions-390'),(320,844,'.of-rail','offers-320'),(390,1000,'.visit-ticket','fair-390'),(560,900,'.visit-ticket','fair-560'),(620,900,'.hero-asides','promotions-620'),(620,900,'.visit-ticket','fair-620'),(768,900,'.visit-ticket','fair-768'),(390,844,'#mobile-menu','menu-390')]:
 call('open',base);call('set','media','light','reduced-motion');call('set','viewport',str(width),str(height));settle();call('select','.footer [data-theme-select]','light')
 if name.startswith('hero'):js('scrollTo({top:0,behavior:"instant"})');settle()
 elif name.startswith('menu'):
  js('document.querySelector("[data-open-menu]").click()');settle()
 elif selector in ['.sd-section','.hero-asides']:
  js('scrollTo({top:document.querySelector('+json.dumps(selector)+').getBoundingClientRect().top+scrollY-24,behavior:"instant"})');settle()
 else:center(selector)
 js('Promise.allSettled([...document.images].filter(i=>{const r=i.getBoundingClientRect();return r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth&&getComputedStyle(i).visibility!=="hidden"}).map(i=>{i.loading="eager";return i.decode()}))');settle()
 call('screenshot',str(ROOT/f'docs/previews/round39-{name}.png'));print('CAPTURE',name,flush=True)
