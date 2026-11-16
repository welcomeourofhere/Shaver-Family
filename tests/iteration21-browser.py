from iteration18_browser_helpers import *
report={'widths':[],'frames':[],'scroll':[],'seo':{}}
call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/');settle()
report['seo']=js('''(()=>({title:document.title,description:document.querySelector('meta[name=description]').content,h1:document.querySelectorAll('h1').length,footerHeadings:document.querySelectorAll('footer h2').length,missingAlt:[...document.images].filter(e=>!e.hasAttribute('alt')).length,schema:JSON.parse(document.querySelector('script[type="application/ld+json"]').textContent)}))()''');assert report['seo']['h1']==1 and report['seo']['missingAlt']==0 and report['seo']['footerHeadings']==0
for w in [320,390,540,650,800,960,1024,1080,1280,1440,1920]:
 call('set','viewport',str(w),'1000');settle();m=js(MEASURE);assert not m['overflow'] and not m['issues'],m;report['widths'].append(m)
 if w in [390,800,1024,1440]:
  center('.of-rail');call('focus','.of-rail');call('press','Home');settle();call('mouse','move','0','0')
  result=js('''(async()=>{const rail=document.querySelector('.of-rail'),cards=[...rail.querySelectorAll('[data-offer-id]')],frames=[];for(const direction of ['next','prev','prev','next']){document.querySelector(`[data-of-${direction}]`).dispatchEvent(new MouseEvent('click',{bubbles:true,detail:1}));for(let i=0;i<120;i++){await new Promise(r=>requestAnimationFrame(r));const r=rail.getBoundingClientRect(),over=parseFloat(rail.style.getPropertyValue('--offer-left-overflow')),active=cards.find(c=>c.dataset.offerActive==='true'),x=active.getBoundingClientRect().left-r.left;frames.push({direction,over,x,bad:cards.some(c=>getComputedStyle(c).clipPath!=='none'),previousLeak:cards.some(c=>c!==active&&getComputedStyle(c).visibility==='visible'&&c.getBoundingClientRect().right<r.left)});} }return{frames,clip:getComputedStyle(rail).clipPath}})()''')
  assert all(not r['bad'] and not r['previousLeak'] and 0<=r['over']<=33 for r in result['frames']),w
  assert all(r['over']<.1 or abs(r['x']+r['over'])<.15 for r in result['frames']),w
  report['frames'].append({'width':w,'samples':len(result['frames']),'maxOverlay':max(r['over'] for r in result['frames'])})
  call('screenshot',str(ROOT/f'docs/previews/round21-offers-{w}.png'))
  # Native scroll travels without cancellation above service content.
  center('.sd-stack');call('hover','.sd-stack');before=js('scrollY');call('scroll','down','360');after=js('scrollY');assert after>before+300,(w,before,after);report['scroll'].append({'width':w,'delta':after-before})
  print('PASS: rounded cards / one viewport / forward-back loops / native wheel',w,flush=True)
report['reveal']=js('''[...document.querySelectorAll('.of-slider,.sd-stack,.team-grid,.gifts-layout')].map(e=>({class:e.className,mode:e.dataset.revealMode,transform:getComputedStyle(e).transform}))''');assert all(e['mode']=='fade' and e['transform']=='none' for e in report['reveal'])
save('iteration21-qa',report);print('PASS: 11 responsive widths; 1920 animation frames; metadata, heading structure and alt attributes.',flush=True)
call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/#offers')
