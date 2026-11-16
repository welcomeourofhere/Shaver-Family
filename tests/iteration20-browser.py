"""Built-site motion, theme persistence, overlay isolation and visual acceptance."""
from iteration18_browser_helpers import *
report={'externalSubmission':False,'screenshots':[],'geometry':[]}
call('set','viewport','1440','1000');call('open','http://127.0.0.1:4323/');call('set','media','light');call('select','.footer [data-theme-select]','auto');call('set','media','dark');settle();assert js('document.documentElement.dataset.theme')=='dark'
call('open','http://127.0.0.1:4323/');settle();assert js('document.documentElement.dataset.theme')=='dark'
call('select','.footer [data-theme-select]','light');call('open','http://127.0.0.1:4323/');settle();assert js('document.documentElement.dataset.theme')=='light'
report['themePersistence']=True
for theme in ['light','dark']:
 call('select','.footer [data-theme-select]',theme)
 for width in [320,390,800,960,1024,1440]:
  call('set','viewport',str(width),'1000');settle()
  for name,selector in [('hero',None),('fair','.visit-ticket'),('gifts','.gifts-layout'),('offers','.of-slider')]:
   if selector:center(selector)
   else:js('scrollTo({top:0,behavior:"instant"})');settle()
   call('mouse','move','0','0')
   assert not js('document.documentElement.scrollWidth>innerWidth+1'),(theme,width,name)
   if width in [390,1440]:
    path=ROOT/f'docs/previews/round20-{name}-{theme}-{width}.png';call('screenshot',str(path));report['screenshots'].append(str(path.relative_to(ROOT)))
  center('.certificate-scene');call('focus','[data-certificate-value="2000"]');js('(async()=>{await new Promise(r=>setTimeout(r,1000));return true})()')
  bottom=js('[...document.querySelectorAll(".certificate-art")].map(e=>e.getBoundingClientRect().bottom)');assert max(bottom)-min(bottom)<.1,(width,bottom)
  center('.visit-ticket');row=js('''(()=>{const a=document.querySelector('.visit-art').getBoundingClientRect(),i=document.querySelector('.visit-art img').getBoundingClientRect(),p=document.querySelector('.visit-copy').getBoundingClientRect();return{width:innerWidth,leftClip:a.left-i.left,stacked:i.bottom<=p.top+13}})()''');assert row['leftClip']<=0,row
  if width<=960:assert row['stacked'],row
  report['geometry'].append({'theme':theme,**row,'certificateBottomSpread':max(bottom)-min(bottom)})
 print('PASS: final artwork, bottom-aligned certificate wave and screenshots',theme,flush=True)
call('set','viewport','1440','1000');center('.sd-stack');call('hover','.sd-stack');before=js('scrollY');call('scroll','down','350');after=js('scrollY');assert after>before+250,(before,after);report['nativeWheelDelta']=after-before
# At rest, no previous card is allowed in the left overlay; during bounce only the active one is.
center('.of-rail');call('focus','.of-rail');call('press','Home');settle()
report['overlay']=js('''(async()=>{const rail=document.querySelector('.of-rail'),r=rail.getBoundingClientRect();const resting=[...rail.querySelectorAll('[data-offer-id]')].filter(c=>c.getBoundingClientRect().right<=r.left).map(c=>({visibility:getComputedStyle(c).visibility,clip:c.style.clipPath}));document.querySelector('[data-of-next]').click();const rows=[];for(let i=0;i<130;i++){await new Promise(r=>requestAnimationFrame(r));for(const c of rail.querySelectorAll('[data-offer-id]')){const x=c.getBoundingClientRect().left-r.left;if(x<0&&getComputedStyle(c).visibility==='visible')rows.push({x,active:c.dataset.offerActive,overlay:c.dataset.offerOverlay,clip:c.style.clipPath});}}return{resting,rows}})()''')
assert all(c['visibility']=='hidden' for c in report['overlay']['resting'])
assert all(c['clip']=='none' for c in report['overlay']['rows'])
# Built version scroll profile, not dev/HMR. This is a lab trace, not a physical-phone claim.
report['scroll']=js('''(async()=>{scrollTo({top:0,behavior:'instant'});await new Promise(r=>setTimeout(r,150));const long=[],obs=new PerformanceObserver(l=>long.push(...l.getEntries().map(e=>({duration:e.duration,start:e.startTime}))));obs.observe({type:'longtask'});let previous=performance.now();const times=[];for(let i=0;i<360;i++){scrollBy({top:48,behavior:'instant'});await new Promise(r=>requestAnimationFrame(r));const now=performance.now();times.push(now-previous);previous=now;}obs.disconnect();times.sort((a,b)=>a-b);return{frames:times.length,median:times[180],p95:times[342],p99:times[356],over32:times.filter(v=>v>32).length,long}})()''');save('iteration18-scroll-after',report['scroll'])
call('set','media','light','reduced-motion');call('open','http://127.0.0.1:4323/');call('set','viewport','390','1000');settle();call('click','[data-open-menu]');assert js('document.querySelector("#mobile-menu").open');assert js('document.querySelector("#mobile-menu").getAnimations().length')==0;call('press','Escape');settle()
center('#about');assert js('getComputedStyle(document.querySelector("#about-title")).position')=='relative';assert js('[...document.querySelectorAll("[data-about-card]")].every(e=>new DOMMatrix(getComputedStyle(e).transform).isIdentity)')
report['reducedMotion']=True
call('set','media','light');call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/#top');settle();save('iteration20-final',report)
print('PASS: theme persistence/system, native wheel, isolated offer overlay, reduced motion and built-site frame profile.',flush=True);print(report['scroll'],flush=True)
