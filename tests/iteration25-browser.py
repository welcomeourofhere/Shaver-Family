from iteration18_browser_helpers import *
report={'cases':[], 'errors':[], 'externalSubmission':False}
call('set','viewport','1440','1000');call('set','media','light');call('open','http://127.0.0.1:4321/');settle()
js('window.__errors=[];addEventListener("error",e=>__errors.push(e.message));addEventListener("unhandledrejection",e=>__errors.push(String(e.reason)))')
CAPTURE=r'''(async()=>{
 const root=document.querySelector(__target),content=root.querySelector(':scope>.surface-content'),shell=root.querySelector(':scope>.surface-shell');
 const leaves=[...content.querySelectorAll('a,button,p,h2,h3,h4,select,img')].filter(e=>e.getBoundingClientRect().width),rows=[];
 for(let start=performance.now();performance.now()-start<550;){await new Promise(r=>requestAnimationFrame(r));const r=root.getBoundingClientRect(),m=new DOMMatrix(getComputedStyle(root).transform),s=new DOMMatrix(getComputedStyle(shell).transform);
 rows.push({rootX:m.m11,rootY:m.m22,shapeX:s.m11,shapeY:s.m22,width:root.offsetWidth,height:root.offsetHeight,client:content.clientWidth,scroll:content.scrollWidth,leaves:leaves.map(e=>{const b=e.getBoundingClientRect();return[e.offsetWidth,e.offsetHeight,b.left-r.left,b.top-r.top,b.width,b.height]})});}
 const first=rows[0],maxDelta=Math.max(...rows.flatMap(row=>row.leaves.flatMap((leaf,i)=>leaf.map((v,j)=>Math.abs(v-first.leaves[i][j])))));
 return{frames:rows.length,maxDelta,widths:[...new Set(rows.map(r=>r.width))],heights:[...new Set(rows.map(r=>r.height))],clients:[...new Set(rows.map(r=>r.client))],rootFixed:rows.every(r=>r.rootX===1&&r.rootY===1),materialObserved:rows.some(r=>Math.abs(r.shapeX-r.shapeY)>.01),settled:rows.at(-1).shapeX===1&&rows.at(-1).shapeY===1};})()'''
def capture(target,open_script):
 js('window.__target='+json.dumps(target))
 # Opening and measurement share a browser task so the material impulse is sampled from frame one.
 value=js(CAPTURE.replace(' const root=', ' '+open_script+'; const root=',1))
 assert value['maxDelta']<.05 and len(value['widths'])==1 and len(value['heights'])==1 and len(value['clients'])==1,value
 assert value['rootFixed'] and value['materialObserved'] and value['settled'],value
 report['cases'].append({'width':js('innerWidth'),'theme':js('document.documentElement.dataset.theme'),'target':target,**value})
for theme in ['light','dark']:
 call('select','.footer [data-theme-select]',theme)
 for width,height in [(320,800),(390,844),(800,1000),(1024,390),(1440,1000)]:
  call('set','viewport',str(width),str(height));js('document.activeElement?.blur();scrollTo({top:0,behavior:"instant"})');settle()
  if width>960:
   for menu in ['.more-menu','.header-contact']:
    capture(menu+' .header-menu-panel','document.querySelector('+json.dumps(menu)+').dispatchEvent(new PointerEvent("pointerleave",{pointerType:"mouse"}));document.querySelector('+json.dumps(menu)+').dispatchEvent(new PointerEvent("pointerenter",{pointerType:"mouse"}))')
    call('press','Escape');call('mouse','move','0','500');js('document.activeElement?.blur()');settle()
  else:
   capture('#mobile-menu','document.querySelector("[data-open-menu]").click()');assert not js(MEASURE)['issues'];call('press','Escape');settle()
   capture('.promo-dialog','document.querySelector("[data-open-promo]").click()');assert not js(MEASURE)['issues'];call('press','Escape');settle()
  center('.footer');capture('.contact-dialog','document.querySelector(".footer-phone").click()');assert not js(MEASURE)['issues'];call('press','Escape');settle()
  center('.team-grid');capture('.team-dialog','document.querySelector(".team-portrait").click()');assert not js(MEASURE)['issues'];call('press','Escape');settle()
 print('PASS stable text/buttons/images and stable scroll widths',theme,flush=True)
report['errors']=js('__errors');assert not report['errors'],report['errors'];save('iteration25-content-stability',report)
call('set','viewport','1440','1000');call('select','.footer [data-theme-select]','auto');js('document.activeElement?.blur();scrollTo({top:0,behavior:"instant"})');settle();call('hover','.more-menu>summary');settle();call('screenshot',str(ROOT/'docs/previews/round25-more-stable.png'));call('press','Escape')
print('PASS all material surfaces keep content layout and text scale unchanged through completion',flush=True)
