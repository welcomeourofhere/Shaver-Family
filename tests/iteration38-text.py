"""The full promo button is retained until enlarged text needs its short label."""
from iteration33_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
report=[]
for width in [320,390,768,960]:
 for scale in [1,1.5,2]:
  call('open','http://127.0.0.1:4321/');call('set','viewport',str(width),'1000');call('set','media','light','reduced-motion');settle()
  js('window.__qaErrors=[];addEventListener("error",e=>__qaErrors.push(e.message));addEventListener("unhandledrejection",e=>__qaErrors.push(String(e.reason)))')
  js('''(()=>{for(const e of document.querySelectorAll('#welcome-offer *, .visit-ticket *'))if([...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))e.style.fontSize=`${parseFloat(getComputedStyle(e).fontSize)*SCALE}px`})()'''.replace('SCALE',str(scale)))
  for selector in ['#welcome-offer','.visit-ticket']:
   center(selector);row=js(AUDIT);assert not row['bad'] and not row['overflow'] and not row['errors'],(width,scale,selector,row)
  evidence=js('''(()=>{const p=document.querySelector('#welcome-offer'),code=p.querySelector('.promo-code').getBoundingClientRect(),b=p.querySelector('.first-actions .btn'),button=b.getBoundingClientRect();return{short:b.hasAttribute('data-short-label'),gap:button.top-code.bottom,accessible:b.getAttribute('aria-label'),tablet:getComputedStyle(document.querySelector('.visit-copy')).gridRowStart==='1'}})()''')
  assert evidence['gap']>=7.9 and evidence['accessible']=='Записаться со скидкой',evidence
  if scale==1:assert not evidence['short'],evidence
  report.append({'width':width,'scale':scale,**evidence})
 print('PASS promo/ticket at 100/150/200 percent text',width,flush=True)
save('iteration38-text',report)
