from iteration18_browser_helpers import *
report={'geometry':[],'menus':[],'assets':[],'externalSubmission':False}
call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/');settle()
js('window.__errors=[];addEventListener("error",e=>__errors.push(e.message));addEventListener("unhandledrejection",e=>__errors.push(String(e.reason)))')
for theme in ['light','dark']:
 call('select','.footer [data-theme-select]',theme)
 for w in [320,360,390,540,650,768,800,960,1024,1280,1440,1920]:
  call('set','viewport',str(w),'1000');center('.team-grid');row=js(MEASURE);assert not row['overflow'] and not row['issues'],row
  extra=js('''(()=>{const cards=[...document.querySelectorAll('.team-card')],r=e=>e.getBoundingClientRect();return{copyHeights:cards.map(e=>r(e.querySelector('.team-copy')).height),buttonBottoms:cards.map(e=>r(e.querySelector('.team-book')).bottom-r(e).top),allLabelsFit:cards.every(e=>{const b=e.querySelector('.team-book');return b.scrollWidth<=b.clientWidth+1})}})()''')
  assert extra['allLabelsFit'],extra;report['geometry'].append({**row,**extra})
  if theme=='light' and w in [390,1440]:call('screenshot',str(ROOT/f'docs/previews/round26-team-{w}.png'))
 print('PASS compact team cards and one-line booking labels',theme,flush=True)
call('set','viewport','1440','1000');call('select','.footer [data-theme-select]','light');js('document.activeElement?.blur();scrollTo({top:0,behavior:"instant"})');settle();call('mouse','move','0','500')
for menu in ['.more-menu','.header-contact']:
 call('hover',menu+'>summary');settle()
 result=js('''(()=>{const p=document.querySelector('.header-menu[open] .header-menu-panel'),c=p.querySelector('.surface-content'),r=p.getBoundingClientRect(),range=document.createRange(),issues=[];for(const a of c.querySelectorAll('a,button,select')){if(!a.offsetHeight)continue;const s=getComputedStyle(a);if(a.scrollWidth>a.clientWidth+1||a.getBoundingClientRect().height<44)issues.push(a.textContent.trim());if(a.matches('select')){const text=a.options[a.selectedIndex].text,canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');ctx.font=s.font;if(ctx.measureText(text).width+parseFloat(s.paddingLeft)+parseFloat(s.paddingRight)+16>a.clientWidth)issues.push('select text');}else{for(const n of a.childNodes)if(n.nodeType===3&&n.textContent.trim()){range.selectNode(n);if(range.getClientRects().length>1)issues.push('wrap');}}}return{width:r.width,issues,bodyWidth:c.clientWidth}})()''')
 assert result['width']==200 and not result['issues'],result;report['menus'].append(result)
 call('screenshot',str(ROOT/f'docs/previews/round26-{menu[1:]}.png'));call('press','Escape');call('mouse','move','0','500');js('document.activeElement?.blur()');settle()
report['max']=js('''[...document.querySelectorAll('[data-contact-channel=max]')].map(a=>({tag:a.tagName,url:a.href,disabled:a.hasAttribute('disabled'),soon:a.textContent.includes('Скоро')}))''')
assert len(report['max'])==3 and all(a['tag']=='A' and a['url'].startswith('https://max.ru/u/') and not a['disabled'] and not a['soon'] for a in report['max'])
for w in [390,1440]:
 call('set','viewport',str(w),'1000')
 for id,image in [('haircut','staff-celebration'),('beard','staff-harvest'),('team','staff-journey'),('place','staff-aspiration')]:
  js('scrollTo({top:0,behavior:"instant"})');settle()
  js(f'''(()=>{{const e=document.querySelector('#about-{id}-title').closest('.about-layer'),top=e.getBoundingClientRect().top+scrollY;scrollTo({{top:top-240,behavior:'instant'}})}})()''');settle()
  result=js(f'''(async()=>{{const i=document.querySelector('#about-{id}-title').closest('article').querySelector('img');await i.decode();return{{src:i.currentSrc,alt:i.alt,width:i.naturalWidth}}}})()''');assert f'/media/editorial/{image}-' in result['src'] and result['width']>0;report['assets'].append(result)
  call('screenshot',str(ROOT/f'docs/previews/round26-about-{id}-{w}.png'))
 assert js('document.querySelectorAll(".of-photo img[src*=editorial]").length===0')
report['errors']=js('__errors');assert not report['errors'];save('iteration26-qa',report);print('PASS compact menus, active MAX, all four responsive owner photos and JS errors',flush=True)
