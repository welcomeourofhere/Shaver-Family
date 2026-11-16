"""The remaining shared windows and scaled header popovers, with native scrollbars visible."""
from iteration18_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
call('open','http://127.0.0.1:4321/?qa=32-surfaces');settle()
report={'windows':[],'popovers':[],'externalSubmission':False}
for theme in ['light','dark']:
 call('select','.footer [data-theme-select]',theme)
 call('set','viewport','390','700')
 for trigger,dialog in [('[data-open-menu]','.mobile-menu'),('[data-open-promo]','.promo-dialog'),('.footer-phone','.contact-dialog')]:
  center(trigger);call('click',trigger);settle()
  row=js('''(()=>{const d=document.querySelector('dialog[open]'),v=d.querySelector('.surface-viewport'),c=d.querySelector('.surface-content');return{dialog:d.className,thin:getComputedStyle(c).scrollbarWidth,clip:getComputedStyle(v).overflow,radius:getComputedStyle(v).borderRadius,overflow:c.scrollWidth>c.clientWidth+1,bottom:d.getBoundingClientRect().bottom,height:innerHeight}})()''')
  assert row['thin']=='thin' and row['clip']=='hidden' and not row['overflow'] and row['bottom']<=row['height'],row
  assert not js(MEASURE)['issues'],js(MEASURE)
  report['windows'].append({'theme':theme,**row})
  call('press','Escape');settle()
 call('set','viewport','1280','400');js('scrollTo({top:34,behavior:"instant"})');settle()
 for menu in ['.more-menu','.header-contact']:
  call('focus',menu+' summary');settle()
  if not js('document.querySelector('+json.dumps(menu)+').open'):call('press','Enter');settle()
  row=js('''(()=>{const d=document.querySelector('.header-menu[open] .header-menu-panel'),v=d.querySelector('.surface-viewport'),c=d.querySelector('.surface-content'),r=d.getBoundingClientRect();return{thin:getComputedStyle(c).scrollbarWidth,clip:getComputedStyle(v).overflow,left:r.left,right:r.right,bottom:r.bottom,screen:innerWidth,height:innerHeight,overflow:c.scrollWidth>c.clientWidth+1}})()''')
  assert row['thin']=='thin' and row['clip']=='hidden' and not row['overflow'] and row['left']>=0 and row['right']<=row['screen'] and row['bottom']<=row['height'],row
  report['popovers'].append({'theme':theme,'menu':menu,**row})
  call('press','Escape');settle()
 print('PASS remaining dialogs and short-screen floating header popovers',theme,flush=True)
call('set','viewport','320','1000');call('select','.footer [data-theme-select]','light')
center('.team-discover[data-team-open="souz-sofya-shalaginova"]');call('click','.team-discover[data-team-open="souz-sofya-shalaginova"]');settle()
js('(()=>{const c=document.querySelector(".team-story-dialog .surface-content");c.scrollTop=c.scrollHeight})()');settle()
call('screenshot',str(ROOT/'docs/previews/round32-story-dialog-end-final-320.png'))
assert not js(MEASURE)['issues'],js(MEASURE)
call('click','.team-story-dialog [data-dismiss]');settle()
assert not js('document.querySelector(".team-story-dialog").open')
call('open','http://127.0.0.1:4321/masters/sofya-shalaginova/');settle();call('set','viewport','390','844')
call('click','[data-open-menu]');settle();call('click','.mobile-menu a[href="/#services"]');settle()
assert js('location.pathname==="/"&&location.hash==="#services"')
report['articleHomeNavigation']=True
save('iteration32-surfaces',report)
print('PASS opaque sticky close rail, Escape, and article-to-home mobile navigation',flush=True)
