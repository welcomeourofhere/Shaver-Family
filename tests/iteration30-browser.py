from iteration18_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuzprint28','--json']
call('open','http://127.0.0.1:4321/?qa=30');call('reload');call('set','media','light');settle()
report={'geometry':[],'menus':[],'externalSubmission':False}
js('window.__errors=[];addEventListener("error",e=>__errors.push(e.message));addEventListener("unhandledrejection",e=>__errors.push(String(e.reason)))')
for theme in ['light','dark']:
 call('select','.footer [data-theme-select]',theme)
 for width in [320,390,800,1024,1440]:
  call('set','viewport',str(width),'1000');center('.visit-ticket');r=js(MEASURE);assert not r['overflow'] and not r['issues'],r
  v=js('''(()=>{const p=document.querySelector('.visit-copy>p');return{font:getComputedStyle(p).fontSize,text:p.textContent,x:getComputedStyle(document.querySelector('.visit-rays')).getPropertyValue('--visit-rays-x').trim(),originals:document.querySelectorAll('[data-about-compare],.about-original').length}})()''')
  assert v['font']==('15px' if width<=960 else '16px') and 'Кид' not in v['text'] and v['originals']==0,v
  assert v['x']==('50%' if width<=960 else '72%'),v
  report['geometry'].append({'width':width,'theme':theme,**v})
  if width in [390,1440]:call('screenshot',str(ROOT/f'docs/previews/round30-visit-{theme}-{width}.png'))
 print('PASS smaller description / Sonya / no comparison / responsive geometry',theme,flush=True)
call('set','viewport','1440','1000');call('select','.footer [data-theme-select]','light');js('scrollTo({top:0,behavior:"instant"})');settle()
for name in ['.more-menu','.header-contact']:
 call('hover',name+'>summary');settle()
 r=js('''(()=>{const p=document.querySelector('NAME .header-menu-panel'),r=p.getBoundingClientRect();return{width:r.width,open:document.querySelector('NAME').open,overflow:p.querySelector('.surface-content').scrollWidth>p.querySelector('.surface-content').clientWidth,labels:[...p.querySelectorAll('a,button')].filter(e=>e.getBoundingClientRect().height).map(e=>({text:e.textContent.trim(),fits:e.scrollWidth<=e.clientWidth,hit:e.getBoundingClientRect().height,pad:parseFloat(getComputedStyle(e).paddingLeft)}))}})()'''.replace('NAME',name))
 assert r['open'] and abs(r['width']-180)<.1 and not r['overflow'] and all(x['fits'] and x['hit']>=44 and x['pad']>=12 for x in r['labels']),r
 report['menus'].append(r);call('screenshot',str(ROOT/f'docs/previews/round30-menu-{name[1:]}.png'));call('mouse','move','0','0');call('press','Escape');settle()
center('.of-controls')
a=js('''[...document.querySelectorAll('.of-arrow svg path')].map(e=>{const b=e.getBBox();return{x:b.x+b.width/2,y:b.y+b.height/2}})''')
assert len(a)==2 and all(r=={'x':12,'y':12} for r in a),a
report['arrows']=a
center('.about-media');old=js("document.querySelector('.about-media img').currentSrc");call('hover','.about-media');settle();assert js("document.querySelector('.about-media img').currentSrc")==old
report['errors']=js('__errors');assert not report['errors'];save('iteration30-qa',report)
center('.visit-ticket');print('PASS compact menus / label padding / centered arrows / About unchanged / clean JS',flush=True)
