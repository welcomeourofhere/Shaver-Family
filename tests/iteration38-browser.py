"""Promo hierarchy, a separate tablet ticket and actual mouse dragging of native rails."""
from iteration33_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
BASE='http://127.0.0.1:4321/'
report={'layouts':[],'drag':[],'published':False}
call('open',BASE);call('set','media','light','reduced-motion');settle()
js('window.__qaErrors=[];addEventListener("error",e=>__qaErrors.push(e.message));addEventListener("unhandledrejection",e=>__qaErrors.push(String(e.reason)))')
MEASURE=r'''(()=>{
 const rect=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height,bottom:r.bottom,right:r.right}},ticket=document.querySelector('.visit-ticket'),promo=document.querySelector('#welcome-offer');
 const rules=['fontFamily','fontSize','fontWeight','lineHeight','color','backgroundColor','borderRadius','padding','display','gridTemplateColumns','columnGap','rowGap','boxShadow','textAlign'];
 const style=e=>{const s=getComputedStyle(e);return Object.fromEntries(rules.map(n=>[n,s[n]]))};
 return {width:innerWidth,promo:{rect:rect(promo),heading:style(promo.querySelector('h2')),paragraph:style(promo.querySelector('p')),code:rect(promo.querySelector('.promo-code')),button:rect(promo.querySelector('.first-actions .btn')),actions:getComputedStyle(promo.querySelector('.first-actions')).display,centered:getComputedStyle(promo).textAlign,label:promo.querySelector('.first-actions .btn').hasAttribute('data-short-label')?'short':'full'},ticket:{rect:rect(ticket),copy:rect(ticket.querySelector('.visit-copy')),art:rect(ticket.querySelector('.visit-art')),print:rect(ticket.querySelector('.visit-print')),heading:rect(ticket.querySelector('h3')),paragraph:rect(ticket.querySelector('.visit-copy>p')),alignment:getComputedStyle(ticket.querySelector('h3')).textAlign},overflow:document.documentElement.scrollWidth>innerWidth+1};
})()'''
for theme in ['light','dark']:
 call('select','.footer [data-theme-select]',theme)
 for width in [320,360,390,540,650,699,700,720,768,800,834,960]:
  call('set','viewport',str(width),'1000');settle();center('#welcome-offer');row=js(MEASURE)
  p=row['promo'];assert p['actions']=='grid' and p['centered']=='center',p
  assert p['button']['y']>=p['code']['bottom']+7.9,p
  assert abs(p['code']['x']-p['button']['x'])<.1 and abs(p['code']['w']-p['button']['w'])<.1,p
  assert p['label']=='full',p
  assert not row['overflow'],row
  t=row['ticket'];r=t['rect']
  if js('document.querySelector(".visit-section").clientWidth')<660:
   midpoint=r['y']+r['h']/2
   assert abs(t['art']['bottom']-midpoint)<.2 and abs(t['copy']['y']-midpoint)<.2,t
  else:
   assert abs(r['w']-js('document.querySelector(".visit-section").clientWidth'))<.5,t
   assert t['copy']['w']<=r['w']*.51 and abs(t['copy']['h']-r['h'])<.2,t
   assert t['art']['x']>r['x']+r['w']*.4 and t['art']['bottom']<=r['bottom']+.2,t
   assert t['paragraph']['right']<t['art']['right'] and r['h']<r['w']*.65,t
  center('.visit-ticket');js('document.querySelector(".visit-art img").decode().then(()=>true)');audit=js(AUDIT);assert not audit['bad'] and not audit['overflow'] and not audit['errors'],audit
  report['layouts'].append({'theme':theme,**row})
  if theme=='light' and width in [390,700,768,834,960]:
   call('screenshot',str(ROOT/f'docs/previews/round38-fair-{width}.png'))
 print('PASS promo PC hierarchy, phone halves and full-width tablet ticket',theme,flush=True)

for width in [320,390,768,960]:
 call('set','viewport',str(width),'1000');settle()
 for rail,action in [('.team-grid','.team-card:first-child .team-book'),('.about-stack','.about-layer:first-child [data-about-more]')]:
  js(f'document.querySelector({json.dumps(rail)}).scrollTo({{left:0,behavior:"instant"}})');center(rail)
  point=js('''(()=>{const e=document.querySelector(SELECTOR),r=e.getBoundingClientRect(),width=e.firstElementChild.getBoundingClientRect().width;return{x:Math.round(r.left+width*.85),y:Math.round(Math.max(110,Math.min(innerHeight-160,r.top+r.height*.3))),distance:Math.round(width*.72)}})()'''.replace('SELECTOR',json.dumps(rail)))
  call('mouse','move',str(point['x']),str(point['y']));call('mouse','down')
  distance=point['distance']
  for step in range(1,13):call('mouse','move',str(point['x']-round(distance*step/12)),str(point['y']))
  during=js(f'({{left:document.querySelector({json.dumps(rail)}).scrollLeft,dragging:document.querySelector({json.dumps(rail)}).classList.contains("is-dragging")}})')
  assert during['left']>40 and during['dragging'],(width,rail,during)
  call('mouse','up');settle();after=js(f'document.querySelector({json.dumps(rail)}).scrollLeft');assert after>20,(width,rail,after)
  assert not js('!!document.querySelector("dialog:modal")')
  assert not js(f'document.querySelector({json.dumps(rail)}).classList.contains("is-dragging")')
  point['x']=js(f'Math.round(document.querySelector({json.dumps(rail)}).getBoundingClientRect().left+60)')
  call('mouse','move',str(point['x']),str(point['y']));call('mouse','down')
  for step in range(1,13):call('mouse','move',str(point['x']+round(distance*step/12)),str(point['y']))
  call('mouse','up');settle();assert js(f'document.querySelector({json.dumps(rail)}).scrollLeft')<after-20,(width,rail,'reverse')
  # Starting on a control must drag the same rail without invoking that control.
  js(f'document.querySelector({json.dumps(rail)}).scrollTo({{left:0,behavior:"instant"}})');center(action)
  point=js('''(()=>{const e=document.querySelector(SELECTOR),r=e.getBoundingClientRect();return{x:Math.round(r.left+r.width*.85),y:Math.round(r.top+r.height/2),distance:Math.round(e.closest('.team-card,.about-layer').getBoundingClientRect().width*.72)}})()'''.replace('SELECTOR',json.dumps(action)))
  call('mouse','move',str(point['x']),str(point['y']));call('mouse','down')
  for step in range(1,13):call('mouse','move',str(point['x']-round(point['distance']*step/12)),str(point['y']))
  call('mouse','up');settle();assert not js('!!document.querySelector("dialog:modal")')
  if rail=='.about-stack':assert js('document.querySelector(".about-layer:first-child [data-about-more]").getAttribute("aria-expanded")')=='false'
  assert js(f'document.querySelector({json.dumps(rail)}).scrollLeft')>20,(width,rail,'action drag')
  report['drag'].append({'width':width,'rail':rail,'during':during,'after':after,'actionDrag':True})
 print('PASS native mouse drag follows cursor and suppresses accidental action',width,flush=True)

# A short genuine click remains an action after dragging.
call('set','viewport','390','1000');js('document.querySelector(".about-stack").scrollTo({left:0,behavior:"instant"})');center('.about-layer:first-child [data-about-more]');call('click','.about-layer:first-child [data-about-more]');settle()
assert js('document.querySelector(".about-layer:first-child [data-about-more]").getAttribute("aria-expanded")')=='true'
call('click','.about-layer:first-child [data-about-more]');settle()
center('.team-grid');js('document.querySelector(".team-grid").scrollTo({left:0,behavior:"instant"})');settle();call('click','.team-card:first-child .team-book');settle()
assert js('document.querySelector("[data-booking-drawer]").open');call('press','Escape');settle()
print('PASS genuine disclosure and booking clicks remain independent',flush=True)
save('iteration38-ui',report)
