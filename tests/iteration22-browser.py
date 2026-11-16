from iteration18_browser_helpers import *
report={'geometry':[],'motion':[],'interruptions':[]}
call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/');settle()
js('window.__errors=[];addEventListener("error",e=>__errors.push(e.message));addEventListener("unhandledrejection",e=>__errors.push(String(e.reason)))')
for w in [320,390,540,650,800,960,1024,1280,1440,1920]:
 call('set','viewport',str(w),'1000');settle();row=js(MEASURE);assert not row['overflow'] and not row['issues'],row;report['geometry'].append(row)
 if w not in [390,800,1440]:continue
 center('.of-rail');call('focus','.of-rail');call('press','Home');settle()
 result=js('''(async()=>{const rail=document.querySelector('.of-rail'),cards=[...rail.querySelectorAll('[data-offer-id]')],rows=[];for(const direction of ['next','prev','prev','next']){
 document.querySelector(`[data-of-${direction}]`).dispatchEvent(new MouseEvent('click',{bubbles:true,detail:1}));
 for(let i=0;i<110;i++){await new Promise(r=>requestAnimationFrame(r));const r=rail.getBoundingClientRect();rows.push({direction,moving:document.querySelector('[data-offers]').dataset.offersMoving,clip:getComputedStyle(rail).clipPath,cards:cards.filter(c=>getComputedStyle(c).visibility==='visible').map(c=>{const s=getComputedStyle(c),m=new DOMMatrix(s.transform);return{id:c.dataset.offerId,x:m.m41,scale:m.m11,opacity:parseFloat(s.opacity),clip:s.clipPath}})});}
 }return rows})()''')
 assert all(r['clip']=='none' and all(c['x']>=-.01 and c['clip']=='none' for c in r['cards']) for r in result),(w,result[:2])
 assert any(c['scale']<.98 and 0<c['opacity']<1 for r in result for c in r['cards']),w
 report['motion'].append({'width':w,'frames':len(result),'foldObserved':True})
 call('screenshot',str(ROOT/f'docs/previews/round22-offers-{w}.png'))
 print('PASS: stable left edge / folding / reverse / cyclic seam',w,flush=True)
call('set','viewport','1440','1000');center('.of-rail');call('focus','.of-rail');call('press','Home');settle()
result=js('''(async()=>{const cards=[...document.querySelectorAll('[data-offer-id]')],rows=[];const poses=()=>cards.map(c=>{const s=getComputedStyle(c);return{matrix:new DOMMatrix(s.transform).toFloat64Array(),opacity:parseFloat(s.opacity),visible:s.visibility==='visible'&&parseFloat(s.opacity)>.01}});
 for(const direction of ['next','next','prev','next','prev','prev','next','next','next']){const before=poses();document.querySelector(`[data-of-${direction}]`).dispatchEvent(new MouseEvent('click',{bubbles:true,detail:1}));const after=poses();rows.push({direction,maxDelta:Math.max(...before.flatMap((p,i)=>p.visible?Array.from(p.matrix).map((v,j)=>Math.abs(v-after[i].matrix[j])):[0])),opacityDelta:Math.max(...before.map((p,i)=>p.visible?Math.abs(p.opacity-after[i].opacity):0))});await new Promise(r=>setTimeout(r,65));}await new Promise(r=>setTimeout(r,600));return{rows,active:document.querySelector('[data-offers]').dataset.offerIndex,moving:document.querySelector('[data-offers]').dataset.offersMoving}})()''')
assert all(r['maxDelta']<.2 and r['opacityDelta']<.005 for r in result['rows']),result
assert result['active']=='3' and result['moving']=='false',result
report['interruptions']=result;print('PASS: nine interrupted/reversed transitions preserve current poses.',flush=True)
# Real neighbour click and keyboard still select and expose the right actions.
call('focus','.of-rail');call('press','Home');settle();call('click','.of-card[data-offer-id="first-visit"] .of-photo');settle();assert js('document.querySelector("[data-offers]").dataset.offerIndex')=='1'
call('focus','.of-rail');call('press','ArrowLeft');settle();assert js('document.querySelector("[data-offers]").dataset.offerIndex')=='0'
call('set','viewport','390','1000');center('.of-rail');call('mouse','move','260','400');call('mouse','down');call('mouse','move','90','400');call('mouse','up');settle()
# Vertical native scrolling stays available above the rail.
center('.of-rail');call('hover','.of-rail');before=js('scrollY');call('scroll','down','300');assert js('scrollY')>before+200
call('set','media','light','reduced-motion');center('.of-rail');call('click','[data-of-next]');assert js('document.querySelector(".of-rail").getAnimations({subtree:true}).filter(a=>a.effect.target.matches(".of-card")).length')==0
report['errors']=js('__errors');assert not report['errors'],report['errors'];save('iteration22-qa',report)
call('set','media','light');call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/#offers')
print('PASS: real neighbour click, keyboard, reduced motion, native vertical wheel; no local JS errors.',flush=True)
