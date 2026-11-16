from iteration18_browser_helpers import *
report={'geometry':[], 'menus':[], 'header':{}, 'actions':{}, 'externalSubmission':False}
call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/');settle()
js('window.__errors=[];addEventListener("error",e=>__errors.push(e.message));addEventListener("unhandledrejection",e=>__errors.push(String(e.reason)))')
for theme in ['light','dark']:
 call('select','.footer [data-theme-select]',theme)
 for w in [320,360,390,540,650,651,768,800,960,1024,1100,1101,1280,1440,1920]:
  call('set','viewport',str(w),'1000');center('.footer');row=js(MEASURE)
  extra=js('''(()=>{const footer=document.querySelector('.footer'),r=e=>e.getBoundingClientRect(),issues=[],range=document.createRange();
  for(const el of footer.querySelectorAll('a,button,select')){const b=r(el);if(!b.width||!b.height)continue;if(b.height<43.9)issues.push('short hit:'+el.textContent);if(b.left<-.5||b.right>innerWidth+.5)issues.push('out of bounds:'+el.textContent);if(el.matches('button,select')){const s=getComputedStyle(el);if(parseFloat(s.paddingLeft)<12||parseFloat(s.paddingRight)<12)issues.push('small padding:'+el.textContent);if(el.scrollWidth>el.clientWidth+1)issues.push('clipped:'+el.textContent);}if(el.matches('select,.footer-address'))continue;for(const text of el.childNodes)if(text.nodeType===3&&text.textContent.trim()){range.selectNode(text);if(range.getClientRects().length>1)issues.push('wrapped:'+text.textContent);}}
  const targets=[...footer.querySelectorAll('a[href^="#"]')].map(a=>({id:a.hash,exists:!!document.querySelector(a.hash)}));return{issues,targets,height:r(footer).height,footerBottom:r(footer).bottom};})()''')
  assert not row['overflow'] and not row['issues'],row
  assert not extra['issues'] and all(a['exists'] for a in extra['targets']),extra
  report['geometry'].append({**row,**extra})
  if w in [390,800,1440]:call('screenshot',str(ROOT/f'docs/previews/round23-footer-{theme}-{w}.png'))
 print('PASS footer layout/buttons/targets',theme,flush=True)
call('set','viewport','844','390');center('.footer');assert not js(MEASURE)['issues'];call('screenshot',str(ROOT/'docs/previews/round23-footer-landscape.png'))
call('set','viewport','1440','1000');call('select','.footer [data-theme-select]','light');js('document.activeElement?.blur();scrollTo({top:0,behavior:"instant"})');settle();call('mouse','move','0','500')
for selector in ['.more-menu','.header-contact']:
 call('hover',selector+' > summary');settle()
 assert js(f'document.querySelector({json.dumps(selector)}).open'),selector
 bounds=js(f'(()=>{{const r=document.querySelector({json.dumps(selector+" .header-menu-panel")}).getBoundingClientRect();return{{x:Math.round(r.x+r.width/2),top:Math.round(r.top),bottom:Math.round(r.bottom)}}}})()')
 call('mouse','move',str(bounds['x']),str(bounds['top']-5));settle();assert js(f'document.querySelector({json.dumps(selector)}).open'),'gap'
 call('mouse','move',str(bounds['x']),str(bounds['top']+30));settle();assert js(f'document.querySelector({json.dumps(selector)}).open'),'panel'
 call('mouse','move','0','500');call('wait','--fn',f'!document.querySelector({json.dumps(selector)}).open')
 report['menus'].append({'selector':selector,'hover':True,'gap':True,'leave':True})
call('hover','.more-menu > summary');call('hover','.header-contact > summary');settle()
assert js('document.querySelector(".header-contact").open&&!document.querySelector(".more-menu").open'),'exclusive'
call('press','Escape');settle();assert not js('document.querySelector(".header-contact").open'),'escape'
call('mouse','move','0','500');call('hover','.header-contact > summary');settle();assert js('document.querySelector(".header-contact").open'),'reenter'
call('press','Escape');call('mouse','move','0','500');call('focus','.more-menu > summary');settle()
assert js('document.querySelector(".more-menu").open'),'keyboard focus'
call('press','Tab');assert js('document.querySelector(".more-menu").contains(document.activeElement)'),'keyboard panel'
call('press','Escape');settle();assert js('!document.querySelector(".more-menu").open&&document.activeElement.matches(".more-menu>summary")'),'escape focus'
report['touchFallback']=js('''(async()=>{const m=document.querySelector('.more-menu'),t=m.querySelector('summary');const tap=()=>{t.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,pointerType:'touch'}));t.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,detail:1}));};tap();await new Promise(r=>setTimeout(r,260));const opened=m.open;tap();await new Promise(r=>setTimeout(r,260));return{synthetic:true,opened,closed:!m.open};})()''')
assert report['touchFallback']['opened'] and report['touchFallback']['closed'],report['touchFallback']
js('document.activeElement.blur()');call('mouse','move','0','500');settle()
report['header']=js('''(async()=>{const h=document.querySelector('.site-header'),frames=[];scrollTo({top:500,behavior:'instant'});for(let start=performance.now();performance.now()-start<450;){await new Promise(r=>requestAnimationFrame(r));frames.push({phase:'hide',y:new DOMMatrix(getComputedStyle(h).transform).m42,opacity:parseFloat(getComputedStyle(h).opacity),hidden:h.classList.contains('is-hidden')});}scrollTo({top:400,behavior:'instant'});for(let start=performance.now();performance.now()-start<600;){await new Promise(r=>requestAnimationFrame(r));frames.push({phase:'show',y:new DOMMatrix(getComputedStyle(h).transform).m42,opacity:parseFloat(getComputedStyle(h).opacity),hidden:h.classList.contains('is-hidden')});}return{frames,enter:getComputedStyle(document.documentElement).getPropertyValue('--motion-header-enter'),exit:getComputedStyle(document.documentElement).getPropertyValue('--motion-header-exit')}})()''')
assert any(r['hidden'] and r['y']< -50 for r in report['header']['frames'])
save('iteration23-header-debug',report['header'])
assert report['header']['frames'][-1]['y']==0 and not report['header']['frames'][-1]['hidden']
assert any(r['phase']=='show' and r['y']>0 for r in report['header']['frames']),'spring overshoot'
center('.footer');call('click','.footer-booking [data-booking]');settle();assert js('!!document.querySelector("[data-booking-drawer][open]")'),'booking';call('press','Escape');settle()
center('.footer');call('click','.footer-phone');settle();assert js('document.querySelector(".contact-dialog").open'),'contact';call('press','Escape');settle()
report['errorsBeforeReload']=js('__errors');assert not report['errorsBeforeReload']
center('.footer');old=js('document.querySelector(".footer [data-feedback-toggle]").getAttribute("aria-pressed")');call('click','.footer [data-feedback-toggle]');assert js('document.querySelector(".footer [data-feedback-toggle]").getAttribute("aria-pressed")')!=old
call('reload');settle();assert js('document.querySelector(".footer [data-feedback-toggle]").getAttribute("aria-pressed")')!=old;center('.footer');call('click','.footer [data-feedback-toggle]')
report['actions']={'booking':True,'contacts':True,'feedbackPersists':True,'maxEnabled':js('(()=>{const a=document.querySelector(".footer [data-contact-channel=max]");return a.tagName==="A"&&a.href.startsWith("https://max.ru/u/")})()')}
assert report['actions']['maxEnabled']
call('set','media','light','reduced-motion');js('document.activeElement?.blur();scrollTo({top:0,behavior:"instant"})');settle();call('hover','.more-menu > summary');assert js('document.querySelector(".more-menu").open');report['reducedMotion']=js('getComputedStyle(document.querySelector(".site-header")).transitionDuration');assert all(float(t.strip().rstrip('s'))==0 for t in report['reducedMotion'].split(','));call('press','Escape');call('set','media','light')
save('iteration23-qa',report)
print('PASS hover/gap/exclusive/Escape/focus, header spring, booking/contact, preference, reduced motion',flush=True)
