from iteration18_browser_helpers import *
report={'header':[],'panels':[],'interruptions':[],'externalSubmission':False}
call('set','viewport','1440','1000');call('set','media','light');call('open','http://127.0.0.1:4321/');settle();call('mouse','move','0','500')
js('window.__errors=[];addEventListener("error",e=>__errors.push(e.message));addEventListener("unhandledrejection",e=>__errors.push(String(e.reason)))')
for width in [1024,1440]:
 call('set','viewport',str(width),'1000');js('document.activeElement?.blur();scrollTo({top:0,behavior:"instant"})');settle()
 rows=js('''(async()=>{const h=document.querySelector('.site-header'),b=h.querySelector('.header-shape'),nav=h.querySelector('.header-nav'),rows=[];for(const y of [500,400]){scrollTo({top:y,behavior:'instant'});for(let start=performance.now();performance.now()-start<500;){await new Promise(r=>requestAnimationFrame(r));const m=new DOMMatrix(getComputedStyle(b).transform),n=new DOMMatrix(getComputedStyle(h).transform),r=b.getBoundingClientRect();rows.push({x:m.m11,y:m.m22,nav:getComputedStyle(nav).transform,outerX:n.m11,outerY:n.m22,left:r.left,right:r.right});}}return rows})()''')
 assert any(r['y']>1.07 for r in rows) and any(r['y']<.93 for r in rows),width
 assert all(r['nav']=='none' and r['outerX']==1 and r['outerY']==1 and r['left']>=0 and r['right']<=width for r in rows),width
 report['header'].append({'width':width,'minY':min(r['y'] for r in rows),'maxY':max(r['y'] for r in rows),'frames':len(rows),'textStable':True})
 js('document.activeElement?.blur();scrollTo({top:0,behavior:"instant"})');settle()
 for target in ['.more-menu','.header-contact']:
  js('window.__menuTarget='+json.dumps(target))
  rows=js('''(async()=>{const menu=document.querySelector(__menuTarget);menu.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));menu.dispatchEvent(new PointerEvent('pointerenter',{pointerType:'mouse'}));const p=menu.querySelector('.header-menu-panel'),rows=[];for(let start=performance.now();performance.now()-start<320;){await new Promise(r=>requestAnimationFrame(r));const m=new DOMMatrix(getComputedStyle(p.querySelector('.surface-shell')).transform),root=new DOMMatrix(getComputedStyle(p).transform),r=p.getBoundingClientRect();rows.push({x:m.m11,y:m.m22,rootX:root.m11,rootY:root.m22,left:r.left,right:r.right,bottom:r.bottom});}return rows})()''')
  assert any(abs(r['x']-r['y'])>.015 for r in rows),(width,target,rows[:2])
  assert all(r['left']>=0 and r['right']<=width and r['bottom']<=1000 for r in rows),(width,target)
  assert abs(rows[-1]['x']-1)<.0001 and abs(rows[-1]['y']-1)<.0001
  assert all(r['rootX']==1 and r['rootY']==1 for r in rows)
  report['panels'].append({'width':width,'target':target,'maxAnisotropy':max(abs(r['x']-r['y']) for r in rows),'settled':True})
  call('press','Escape');call('mouse','move','0','500');js('document.activeElement?.blur()');settle()
# Interrupted closing/reopening preserves the exact nonuniform pose.
report['interruptions']=js('''(async()=>{const menu=document.querySelector('.more-menu'),trigger=menu.querySelector('summary'),panel=menu.querySelector('.header-menu-panel'),pose=()=>{const s=getComputedStyle(panel),m=new DOMMatrix(s.transform),b=new DOMMatrix(getComputedStyle(panel.querySelector('.surface-shell')).transform);return[m.m11,m.m22,m.m41,m.m42,parseFloat(s.opacity),b.m11,b.m22]},rows=[];for(let i=0;i<8;i++){const visible=menu.open,before=visible?pose():null;trigger.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,detail:0}));const after=pose();if(before)rows.push(Math.max(...before.map((v,j)=>Math.abs(v-after[j]))));await new Promise(r=>setTimeout(r,55));}await new Promise(r=>setTimeout(r,300));return{rows,open:menu.open}})()''')
assert all(d<.0002 for d in report['interruptions']['rows']),report['interruptions']
call('press','Escape');call('mouse','move','0','500');js('document.activeElement?.blur()');settle()
for w in [390,800,1440]:
 call('set','viewport',str(w),'1000');center('.footer')
 rows=js('''(async()=>{document.querySelector('.footer-phone').click();const p=document.querySelector('.contact-dialog'),rows=[];for(let start=performance.now();performance.now()-start<400;){await new Promise(r=>requestAnimationFrame(r));const m=new DOMMatrix(getComputedStyle(p.querySelector('.surface-shell')).transform),r=p.getBoundingClientRect();rows.push({x:m.m11,y:m.m22,left:r.left,right:r.right,top:r.top,bottom:r.bottom});}return rows})()''')
 assert any(abs(r['x']-r['y'])>.003 for r in rows),(w,rows[:3])
 assert all(r['left']>=0 and r['right']<=w and r['top']>=0 and r['bottom']<=1000 for r in rows),w
 call('press','Escape');settle()
call('set','media','light','reduced-motion');call('set','viewport','1440','1000');js('document.activeElement?.blur();scrollTo({top:0,behavior:"instant"})');settle();call('hover','.more-menu>summary');report['reduced']=js('document.querySelector(".more-panel").getAnimations().length===0&&document.querySelector(".header-shape").getAnimations().length===0');assert report['reduced'];call('press','Escape');call('set','media','light')
report['errors']=js('__errors');assert not report['errors'];save('iteration24-material',report);print('PASS geometric strain, stationary header text, bounds, precise interruptions, dialogs and reduced motion',flush=True)
