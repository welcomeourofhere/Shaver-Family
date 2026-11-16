from iteration18_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuzprint28','--json']
report={'states':[],'externalSubmission':False}
call('open','http://127.0.0.1:4321/?qa=rays29');call('reload');call('set','media','light');settle()
js('window.__errors=[];addEventListener("error",e=>__errors.push(e.message));addEventListener("unhandledrejection",e=>__errors.push(String(e.reason)))')
READ=r'''(()=>{const t=document.querySelector('.visit-ticket'),p=t.querySelector('.visit-copy'),i=t.querySelector('.visit-art img'),f=t.querySelector('.visit-rays'),s=getComputedStyle(f),r=e=>e.getBoundingClientRect();return{notch:parseFloat(getComputedStyle(t).getPropertyValue('--ticket-notch')),opacity:s.opacity,animation:s.animationName,duration:s.animationDuration,copy:[r(p).width,r(p).height],image:[r(i).width,r(i).height],heading:r(document.querySelector('#visit-title')).top,overflow:document.documentElement.scrollWidth>innerWidth,transform:getComputedStyle(i).transform}})()'''
for theme in ['light','dark']:
 call('select','.footer [data-theme-select]',theme)
 for width in [320,390,800,1024,1440]:
  call('set','viewport',str(width),'1000');center('.visit-ticket');call('mouse','move','0','0');settle();a=js(READ)
  assert a['notch']==24 and not a['overflow'] and a['opacity']=='1' and a['animation']=='soyuz-rays' and a['duration']=='100s',a
  call('hover','.visit-ticket');settle();b=js(READ)
  assert a==b,(a,b)
  report['states'].append({'width':width,'theme':theme,**a})
  if width in [390,1440]:call('screenshot',str(ROOT/f'docs/previews/round29-rays-{theme}-{width}.png'))
 print('PASS permanent print / stable hover / no overflow',theme,flush=True)
center('.visit-ticket')
r=js('''(()=>{const a=document.querySelector('.visit-rays').getAnimations()[0];a.pause();a.currentTime=0;const x=getComputedStyle(document.querySelector('.visit-rays')).transform;a.currentTime=25000;const y=getComputedStyle(document.querySelector('.visit-rays')).transform;a.play();return{x,y}})()''')
assert r['x']!=r['y'],r
call('set','media','light','reduced-motion');settle();assert js(READ)['animation']=='none'
call('set','media','light');call('select','.footer [data-theme-select]','light');call('set','viewport','1440','1000');center('.visit-ticket')
report['errors']=js('__errors');assert not report['errors'];save('iteration29-rays',report)
print('PASS background movement / reduced motion / clean JS',flush=True)


