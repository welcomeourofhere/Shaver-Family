"""The common swipe recognizer preserves desktop mouse, tap and keyboard routes."""
from iteration33_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
call('open','http://127.0.0.1:4321/')
call('set','viewport','1440','1000');call('set','media','light','reduced-motion');settle()

def drag(selector,direction):
 center(selector)
 point=js('''(()=>{const r=document.querySelector(SELECTOR).getBoundingClientRect();return{x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2)}})()'''.replace('SELECTOR',json.dumps(selector)))
 call('mouse','move',str(point['x']),str(point['y']));call('mouse','down')
 for step in range(1,9):call('mouse','move',str(point['x']+direction*20*step),str(point['y']))
 call('mouse','up');settle()

report=[]
drag('.hero-rail',-1)
assert js('document.querySelector(".hero-position").textContent')=='2 / 10'
drag('.hero-rail',1)
assert js('document.querySelector(".hero-position").textContent')=='1 / 10'
report.append('hero mouse forward/back')
center('.of-rail');call('focus','.of-rail');call('press','Home');settle()
drag('.of-card[data-offer-active=true] .of-action',-1)
assert js('document.querySelector("[data-offers]").dataset.offerIndex')=='1'
assert not js('!!document.querySelector("dialog:modal")')
call('click','[data-of-prev]');settle()
call('click','.of-card[data-offer-active=true] .of-action');settle()
assert js('document.querySelector("#review-dialog").open')
call('press','Escape');settle();report.append('offer button drag avoids click; genuine click opens review')
call('focus','.of-rail');call('press','End');settle()
assert js('document.querySelector("[data-offers]").dataset.offerIndex')=='10'
call('press','ArrowRight');settle()
assert js('document.querySelector("[data-offers]").dataset.offerIndex')=='0'
report.append('offer keyboard loop')
center('.sd-stack');before=js('document.querySelector("[data-sd-tab][aria-selected=true]").dataset.sdTab')
drag('.sd-card[aria-hidden=false] .sd-title',-1)
assert js('document.querySelector("[data-sd-tab][aria-selected=true]").dataset.sdTab')==before
report.append('service swipe stays mobile only')
save('iteration37-mouse',report)
print('PASS desktop mouse, independent CTA, keyboard loop and mobile-only services',flush=True)
