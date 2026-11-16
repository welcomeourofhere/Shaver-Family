from iteration18_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuzprint28','--json']
report={'rows':[],'actions':{},'externalSubmission':False}
call('open','http://127.0.0.1:4321/?qa=31-final');call('reload');call('set','media','light');settle()
js('window.__errors=[];addEventListener("error",e=>__errors.push(e.message));addEventListener("unhandledrejection",e=>__errors.push(String(e.reason)))')
CONTACTS=r'''(()=>{const c=document.querySelector('#contacts'),r=e=>e.getBoundingClientRect(),b=r(c),bad=[],range=document.createRange();for(const e of c.querySelectorAll('a,button')){const z=r(e),s=getComputedStyle(e);if(z.height<43.9)bad.push('hit:'+e.textContent);if(z.left<b.left-.5||z.right>b.right+.5||e.scrollWidth>e.clientWidth+1)bad.push('bounds:'+e.textContent);if(e.matches('.btn,.contact-channel')){if(parseFloat(s.paddingLeft)<12||parseFloat(s.paddingRight)<12)bad.push('pad:'+e.textContent);const walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);while(walker.nextNode()){if(!walker.currentNode.textContent.trim())continue;range.selectNodeContents(walker.currentNode);if(range.getClientRects().length>1)bad.push('wrap:'+e.textContent);}}}const map=r(c.querySelector('.contact-map')),visit=r(c.querySelector('.contact-visit')),connect=r(c.querySelector('.contact-connect'));return{width:innerWidth,section:b.width,bad,map:{x:map.x,y:map.y,w:map.width,h:map.height},visit:{x:visit.x,y:visit.y,w:visit.width,h:visit.height},connect:{x:connect.x,y:connect.y,w:connect.width,h:connect.height},channels:[...c.querySelectorAll('[data-contact-channel]')].map(a=>({id:a.dataset.contactChannel,url:a.href,icon:a.querySelector('use')?.getAttribute('href')})),phone:c.querySelector('.contact-phone').getAttribute('href'),text:c.textContent,src:c.querySelector('iframe').src,radii:[...c.querySelectorAll('.contact-card,.contact-map')].map(e=>getComputedStyle(e).borderRadius)}})()'''
VISIT=r'''(async()=>{const r=e=>e.getBoundingClientRect(),t=document.querySelector('#visit-title'),b=document.querySelector('.visit-ticket'),a=document.querySelector('.visit-art'),i=a.querySelector('img');await i.decode();const box=r(i),s=Math.min(box.width/i.naturalWidth,box.height/i.naturalHeight),head=box.bottom-i.naturalHeight*s,before=r(t).top,bt=r(b).top;a.style.setProperty('--visit-overhang','48px');const after=r(t).top,at=r(b).top;a.style.removeProperty('--visit-overhang');return{gap:r(b).top-r(t).bottom,expected:parseFloat(getComputedStyle(t).marginBottom),headClearance:head-r(t).bottom,titleDelta:after-before,bgDelta:at-bt}})()'''
for theme in ['light','dark']:
 call('select','.footer [data-theme-select]',theme)
 for width in [320,360,390,540,650,768,800,960,1024,1280,1440,1920]:
  call('set','viewport',str(width),'1000');center('.visit-ticket');v=js(VISIT)
  assert abs(v['gap']-v['expected'])<.1 and v['headClearance']>=10 and v['titleDelta']==0 and v['bgDelta']==0,v
  center('.contact-layout');c=js(CONTACTS);g=js(MEASURE)
  assert not c['bad'] and not g['overflow'] and not g['issues'],(c,g)
  assert c['phone']=='tel:+79229090043' and 'Владимирская, 132' in c['text'] and 'Свободы' not in c['text']
  assert [x['id'] for x in c['channels']]==['telegram','max','vk'],c
  assert all(x['icon'].startswith('/brand/contact-icons.svg#contact-') for x in c['channels'])
  assert c['src'].startswith('https://yandex.ru/map-widget/') and all(x=='24px' for x in c['radii'])
  report['rows'].append({'theme':theme,**c,'visitSpacing':v})
  if width in [390,1440]:
   center('.contact-visit');call('screenshot',str(ROOT/f'docs/previews/round31-contacts-{theme}-{width}.png'))
   if width==390:center('.contact-connect');call('screenshot',str(ROOT/f'docs/previews/round31-contact-links-{theme}-{width}.png'))
 print('PASS contacts/labels/map and independent visit spacing',theme,flush=True)
for width in [390,1280,1440,1920]:
 call('set','viewport',str(width),'1000');center('.contact-visit');call('click','.contact-visit [data-booking]');settle()
 assert js('document.querySelector("[data-booking-drawer]").open')
 c=js(CONTACTS);g=js(MEASURE);assert not c['bad'] and not g['overflow'] and not g['issues'],(c,g)
 report['actions'][str(width)]={'booking':True,'contacts':c}
 call('press','Escape');settle();assert not js('document.querySelector("[data-booking-drawer]").open')
call('set','media','light','reduced-motion');call('set','viewport','390','844');center('.visit-ticket');v=js(VISIT);assert abs(v['gap']-v['expected'])<.1 and v['headClearance']>=10
center('.contact-layout');assert not js(CONTACTS)['bad'];assert not js(MEASURE)['issues']
call('set','media','light');call('select','.footer [data-theme-select]','light');call('set','viewport','1440','1000');center('.contact-visit')
call('press','Tab');call('focus','.contact-visit [data-booking]');assert js('document.activeElement.matches(".contact-visit [data-booking]") && document.activeElement.matches(":focus-visible")')
report['errors']=js('__errors');assert not report['errors'];save('iteration31-qa',report)
print('PASS booking overlays/docked / reduced motion / keyboard / clean JS',flush=True)
