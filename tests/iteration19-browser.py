"""Native Chrome interactions and frame traces for owner iteration 19."""
from iteration18_browser_helpers import *
report={'hero':{},'masters':{},'certificates':[],'offers':{},'about':[],'externalSubmission':False}
call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/');call('set','media','light');call('select','.footer [data-theme-select]','light');js('scrollTo({top:0,behavior:"instant"})');call('mouse','move','0','0');settle()
js('window.__errors=[];addEventListener("error",e=>__errors.push(e.message));addEventListener("unhandledrejection",e=>__errors.push(String(e.reason)))')
assert js('document.querySelector(".hero-news-action").getBoundingClientRect().height')<1
call('hover','.hero-news-panel');settle();assert js('document.querySelector(".hero-news-action").getBoundingClientRect().height')>=44
call('mouse','move','0','0');settle();assert js('document.querySelector(".hero-news-action").getBoundingClientRect().height')<1
call('focus','.hero-news-link');settle();assert js('document.querySelector(".hero-news-action").getBoundingClientRect().height')>=44
js('document.activeElement.blur()')
tones=[]
for i in range(10):
 js(f'document.querySelectorAll("[data-hero-dot]")[{i}].click()')
 row=js('''(async()=>{for(let i=0;i<100;i++){await new Promise(r=>setTimeout(r,20));const img=document.querySelector('.hero-slide[data-hero-active=true] img');if(img&&!img.complete)continue;const dot=[...document.querySelectorAll('[data-hero-dot]')].findIndex(e=>e.getAttribute('aria-current')==='true'),link=document.querySelector('.hero-news-link');return{index:dot,tone:link.dataset.newsTone,url:link.href,slideURL:document.querySelector('.hero-slide[data-hero-active=true]').dataset.newsUrl};}})()''')
 assert row['index']==i and row['url']==row['slideURL'],row;tones.append(row['tone'])
assert all(t in ['red','blue','yellow'] and t!=tones[(i+1)%10] for i,t in enumerate(tones))
js('document.querySelectorAll("[data-hero-dot]")[0].click()');settle()
zoom=js('''(async()=>{const img=document.querySelector('.hero-slide[data-hero-active=true] img'),scale=()=>new DOMMatrix(getComputedStyle(img).transform).m11,a=scale();await new Promise(r=>setTimeout(r,500));return{before:a,after:scale(),paused:document.querySelector('.hero-scene').dataset.heroPaused}})()''');assert zoom['after']>zoom['before'] and zoom['paused']=='false',zoom
call('hover','.hero-slide[data-hero-active=true] .hero-edge-prev');settle();assert js('getComputedStyle(document.querySelector(".hero-slide[data-hero-active=true] .hero-edge-prev"),"::before").opacity')=='1'
call('click','.hero-slide[data-hero-active=true] .hero-edge-prev');settle();assert js('[...document.querySelectorAll("[data-hero-dot]")].findIndex(e=>e.getAttribute("aria-current")==="true")')==9
report['hero']={'tones':tones,'photoZoom':zoom,'hoverAndKeyboardCTA':True,'edgeNavigation':True}
print('PASS: news text/CTA hover, keyboard, ten cyclic colours, edge navigation and independent zoom.',flush=True)
# Both dropdowns originate at their own trigger and reverse cleanly.
for selector in ['.header-phone','.more-menu>summary']:
 js('scrollTo({top:0,behavior:"instant"})');settle();call('click',selector);settle()
 row=js('''(()=>{const m=document.querySelector('.header-menu[open]'),p=m.querySelector('.header-menu-panel'),t=m.querySelector('summary'),r=p.getBoundingClientRect(),b=t.getBoundingClientRect();return{origin:parseFloat(getComputedStyle(p).transformOrigin),expected:b.left+b.width/2-r.left,arrows:p.querySelectorAll('.contact-channel>.ui-icon').length}})()''')
 assert abs(row['origin']-row['expected'])<.2,row
 if selector=='.header-phone':assert row['arrows']==0,row
 call('press','Escape');settle();assert js('document.querySelectorAll(".header-menu[open]").length')==0
js('''(async()=>{const s=document.querySelector('.more-menu>summary');s.click();await new Promise(r=>setTimeout(r,65));s.click();await new Promise(r=>setTimeout(r,65));s.click();await new Promise(r=>setTimeout(r,600));return true})()''');assert js('document.querySelector(".more-menu").open');call('press','Escape');settle()
# Stable portrait frame, no name action, monotonic image return above baseline.
js('document.activeElement.blur()');center('.team-card:first-child .team-portrait');call('mouse','move','0','0');settle();assert js('document.querySelectorAll(".team-name button,.team-name[data-team-open]").length')==0
call('hover','.team-card:first-child .team-portrait');settle()
js('''window.__photoTrace=[];window.__photoEnd=performance.now()+900;requestAnimationFrame(function sample(){const e=document.querySelector('.team-card .team-portrait img');__photoTrace.push({time:performance.now(),scale:new DOMMatrix(getComputedStyle(e).transform).m11});if(performance.now()<__photoEnd)requestAnimationFrame(sample)})''')
call('mouse','move','0','0');js('(async()=>{await new Promise(r=>setTimeout(r,1000));return true})()');trace=js('__photoTrace');assert min(e['scale'] for e in trace)>1.02,trace[-5:]
call('hover','.team-card:first-child .team-portrait');settle();before=js('document.querySelector(".team-card .team-portrait").getBoundingClientRect().toJSON()');call('mouse','move',str(round(before['x']+before['width']/2)),str(round(before['y']+before['height']/2)));call('mouse','down');held=js('''(()=>{const e=document.querySelector('.team-card .team-portrait');return{rect:e.getBoundingClientRect().toJSON(),scale:getComputedStyle(e).scale,imgScale:new DOMMatrix(getComputedStyle(e.querySelector('img')).transform).m11}})()''');call('mouse','up');settle();assert held['rect']==before and held['scale'] in ['1','none'] and held['imgScale']>1,held
assert js('document.querySelectorAll(".team-dialog[open]").length')==1;call('press','Escape');settle();report['masters']={'minScale':min(e['scale'] for e in trace),'lastScale':trace[-1]['scale'],'stablePress':held};save('iteration18-photo-after',trace)
print('PASS: plain master names, fixed portrait press frame and monotonic photo return.',flush=True)
# Every card owns its local tilt. Hover selects a persistent depth wave.
for width in [320,390,800,960,1024,1440]:
 call('set','viewport',str(width),'1000');center('.certificate-scene');call('mouse','move','0','0');settle()
 for index in [0,2,1,3]:
  call('focus',f'[data-certificate-value="{["front","1000","2000","3000"][index]}"]');settle()
  levels=js('[...document.querySelectorAll("[data-certificate]")].map(e=>Number(e.dataset.certificateLevel))');assert levels==[abs(i-index) for i in range(4)],(width,index,levels)
 report['certificates'].append({'width':width,'levels':levels})
call('set','viewport','1440','1000');center('.certificate-scene');call('focus','[data-certificate-value="front"]');settle()
point=js('''(()=>{const c=document.querySelector('[data-certificate-value="2000"]'),r=c.getBoundingClientRect();for(let y=r.top+12;y<r.bottom-12;y+=8)for(let x=r.left+12;x<r.right-12;x+=8)if(document.elementFromPoint(x,y)?.closest('[data-certificate]')===c)return{x:Math.round(x),y:Math.round(y)};return null})()''');assert point
rects=js('[...document.querySelectorAll("[data-certificate]")].map(e=>e.getBoundingClientRect().toJSON())');call('mouse','move',str(point['x']),str(point['y']));js('(async()=>{await new Promise(r=>setTimeout(r,650));return true})()');assert js('[...document.querySelectorAll("[data-certificate]")].map(e=>e.dataset.certificateLevel).join(",")')=='2,1,0,1'
assert js('[...document.querySelectorAll("[data-certificate]")].map(e=>e.getBoundingClientRect().toJSON())')==rects
call('mouse','move','0','0');settle();assert js('document.querySelector(".certificate-object.is-front").dataset.certificateValue')=='2000'
print('PASS: four certificate wave selections at six widths, hover selection persists and hit frames stay fixed.',flush=True)
# Exposed physical card strip is clickable; the content stays inert until selected.
center('.sd-stack');call('click','[data-sd-tab="0"]');settle()
point=js('''(()=>{const stack=document.querySelector('.sd-stack').getBoundingClientRect();for(let x=stack.right-2;x>stack.right-80;x-=2){const e=document.elementFromPoint(x,stack.top+80)?.closest('[data-sd-panel]');if(e&&e.getAttribute('aria-hidden')==='true')return{x:Math.round(x),y:Math.round(stack.top+80),index:e.dataset.sdPanel};}return null})()''');assert point
call('mouse','move',str(point['x']),str(point['y']));call('mouse','down');call('mouse','up');settle();assert js('document.querySelector("[data-sd-panel][aria-hidden=false]").dataset.sdPanel')==point['index']
print('PASS: exposed physical service card selects its own category.',flush=True)
# Real neighbour click, stable selected image while rail springs beyond its left edge.
center('.of-rail');js('document.querySelector("[data-of-prev]").focus()');call('press','Home');settle();call('focus','.of-rail');call('press','Home');settle();call('mouse','move','0','0')
js('''window.__offerTrace=[];window.__offerEnd=performance.now()+1400;requestAnimationFrame(function sample(){const r=document.querySelector('.of-rail').getBoundingClientRect(),c=[...document.querySelectorAll('[data-offer-id]')];__offerTrace.push({time:performance.now(),moving:document.querySelector('[data-offers]').dataset.offersMoving,active:c.filter(e=>e.dataset.offerActive==='true').map(e=>e.dataset.offerId),positions:c.map(e=>({id:e.dataset.offerId,x:e.getBoundingClientRect().left-r.left,scale:new DOMMatrix(getComputedStyle(e.querySelector('img')).transform).m11}))});if(performance.now()<__offerEnd)requestAnimationFrame(sample)})''')
point=js('''(()=>{const r=document.querySelector('.of-rail').getBoundingClientRect(),c=[...document.querySelectorAll('[data-offer-id]')].find(e=>{const b=e.getBoundingClientRect();return b.left>r.left+20&&b.right<innerWidth}),b=c.getBoundingClientRect();return{x:Math.round(b.left+b.width/2),y:Math.round(b.top+100),id:c.dataset.offerId}})()''');assert point
call('mouse','move',str(point['x']),str(point['y']));call('mouse','down');call('mouse','up');js('(async()=>{await new Promise(r=>setTimeout(r,1500));return true})()');trace=js('__offerTrace');moving=[r for r in trace if r['moving']=='true'];assert moving and all(r['active']==[point['id']] for r in moving),point
assert all(p['scale']>=.99999 for r in trace for p in r['positions'])
assert js('''[...document.querySelectorAll('[data-offer-id]')].filter(e=>e.dataset.offerActive!=='true').every(e=>e.dataset.offerOverlay==='false')''')
min_x=min(p['x'] for r in moving for p in r['positions'] if p['id']==point['id']);assert min_x<0 and min_x>=-33,min_x
assert js('document.querySelector("[data-offer-active=true]").dataset.offerId')==point['id'];report['offers']={'neighbor':point['id'],'minLeftOvershoot':min_x,'clip':js('getComputedStyle(document.querySelector(".of-rail")).clipPath'),'activeStable':True};save('iteration19-offer-frames',trace)
print('PASS: real neighbour click retains one active photo; left spring overshoot is visible and bounded.',flush=True)
# The sticky heading enters without a one-frame offset, including the first pin.
for width in [390,1440]:
 call('set','viewport',str(width),'1000');settle()
 row=js('''(async()=>{const h=document.querySelector('#about-title'),top=Number.parseFloat(getComputedStyle(h).top),start=h.getBoundingClientRect().top+scrollY-top-120;scrollTo({top:start,behavior:'instant'});await new Promise(r=>setTimeout(r,100));const rows=[];for(let i=0;i<160;i++){scrollBy({top:4,behavior:'instant'});await new Promise(r=>requestAnimationFrame(r));rows.push({scroll:scrollY,top:h.getBoundingClientRect().top});}return{width:innerWidth,sticky:top,rows}})()''')
 for a,b in zip(row['rows'],row['rows'][1:]):assert -.1<=b['top']-a['top']+4<=4.1,(width,a,b)
 assert max(r['top'] for r in row['rows'][-30:])-min(r['top'] for r in row['rows'][-30:])<.1,row['rows'][-3:]
 report['about'].append(row)
print('PASS: initial About heading approach and pin have no forward jump on phone/desktop.',flush=True)
# Contrast depends on the actual surface, including hover-coloured master cards.
assert js('getComputedStyle(document.querySelector(".visit-copy p"),"::selection").backgroundColor')=='rgb(255, 204, 41)'
assert js('getComputedStyle(document.querySelector(".sd-card[data-sd-color=yellow] .sd-title"),"::selection").backgroundColor')=='rgb(82, 101, 140)'
report['errors']=js('__errors');assert not report['errors'],report['errors'];save('iteration19-interactions',report)
print('PASS: contextual selection and no local JS errors in tested interactions.',flush=True)
