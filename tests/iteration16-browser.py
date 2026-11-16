"""Current owner contract: native story layers, news hero, linear certificates."""
import json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ['AGENT_BROWSER_SOCKET_DIR']=str(ROOT/'.local/browser-qa')
CLI=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuzfinal','--json']
def call(*args,script=None):
    p=subprocess.run(CLI+list(args),input=script,text=True,encoding='utf-8',capture_output=True,timeout=45)
    assert p.returncode==0,p.stdout+p.stderr
    d=json.loads(p.stdout);assert d['success'],d;return d['data']
def js(s):return call('eval','--stdin',script=s)['result']
def settle():js('(async()=>{await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));await Promise.allSettled(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity&&a.animationName!=="hero-photo-zoom").map(a=>a.finished));return true})()')
def center(s):js('document.querySelector('+json.dumps(s)+').scrollIntoView({behavior:"instant",block:"center"})');settle()

call('open','http://127.0.0.1:4321/');call('set','media','light');settle()
js('window.__qaErrors=[];addEventListener("error",e=>window.__qaErrors.push(e.message));addEventListener("unhandledrejection",e=>window.__qaErrors.push(String(e.reason)))')
report={'geometry':[],'story':[],'certificates':[],'externalSubmission':False}
for width in [320,360,390,540,600,650,651,768,800,960,1024,1280,1440,1920]:
    call('set','viewport',str(width),'1000');settle()
    m=js('''(()=>{const r=e=>e.getBoundingClientRect(),range=document.createRange(),h=document.querySelector('.hero-heading'),n=document.querySelector('.hero-nav'),hero=document.querySelector('.hero-scene'),s=getComputedStyle(n,'::before');return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,titleLines:[...h.children].map(e=>{range.selectNodeContents(e);return range.getClientRects().length}),pultCenter:r(n).left+r(n).width/2-(r(hero).left+r(hero).width/2),pultShadow:s.boxShadow,pultBackground:s.backgroundColor,icon:!!document.querySelector('.hero-news-toggle svg'),gap:[...document.querySelectorAll('.section')].map(e=>parseFloat(getComputedStyle(e).paddingTop)),cards:[...document.querySelectorAll('.about-card')].map(e=>r(e).height),layers:[...document.querySelectorAll('.about-layer')].map(e=>parseFloat(getComputedStyle(e).top)),buttonIssues:[...document.querySelectorAll('button,.btn,.hero-news-link')].flatMap(e=>{const b=r(e),c=getComputedStyle(e);if(!b.width||!b.height||e.closest('dialog:not([open]),[inert]')||!e.textContent.trim()||e.querySelector('img'))return [];return b.height<43.9||parseFloat(c.paddingLeft)<12||parseFloat(c.paddingRight)<12||e.scrollWidth>e.clientWidth+1?[e.className]:[]})}})()''')
    assert not m['overflow'] and m['titleLines']==[1,1,1],m
    assert abs(m['pultCenter'])<1 and m['pultShadow']=='none' and not m['icon'],m
    assert all(p==(96 if width<=800 else 128) for p in m['gap']) and not m['buttonIssues'],m
    assert max(m['cards'])-min(m['cards'])<1,m
    assert all(abs(m['layers'][i+1]-m['layers'][i]-(8 if width<=800 else 12))<.1 for i in range(3)),m
    report['geometry'].append(m)
print('PASS: 14 widths; three-line hero headline, centered flat indicator, no icon/overflow, shared section gaps, button labels and equal story surfaces.',flush=True)

# Read positions before any sticky displacement, then sample the native scroll path.
for width in [390,1440]:
    call('set','viewport',str(width),'1000');js('scrollTo({top:0,behavior:"instant"})');settle()
    trace=js('''(async()=>{const layers=[...document.querySelectorAll('.about-layer')],cards=[...document.querySelectorAll('.about-card')],title=document.querySelector('#about-title'),stack=document.querySelector('.about-stack'),stops=layers.map(e=>e.getBoundingClientRect().top+scrollY-parseFloat(getComputedStyle(e).top)),out=[];for(let y=stops[1];y<=stops[2];y+=(stops[2]-stops[1])/12){scrollTo({top:y,behavior:'instant'});await new Promise(r=>requestAnimationFrame(r));out.push(title.getBoundingClientRect().top)}const end=stack.getBoundingClientRect().bottom+scrollY-cards[3].getBoundingClientRect().height-parseFloat(getComputedStyle(layers[3]).top),sample=()=>({title:title.getBoundingClientRect().top,tops:cards.map(c=>c.getBoundingClientRect().top)});scrollTo({top:end-1,behavior:'instant'});await new Promise(r=>requestAnimationFrame(r));const before=sample();scrollTo({top:end+120,behavior:'instant'});await new Promise(r=>requestAnimationFrame(r));return{trace:out,before,after:sample(),step:parseFloat(getComputedStyle(stack).getPropertyValue('--about-stack-step')),stops}})()''')
    assert max(trace['trace'])-min(trace['trace'])<1,(width,trace)
    for state in [trace['before'],trace['after']]:
        assert all(abs(state['tops'][i+1]-state['tops'][i]-trace['step'])<1 for i in range(3)),(width,trace)
    assert abs((trace['after']['title']-trace['before']['title'])-(trace['after']['tops'][3]-trace['before']['tops'][3]))<1,(width,trace)
    report['story'].append({'width':width,**trace})
    js('scrollTo({top:'+str(trace['stops'][3])+',behavior:"instant"})');settle()
    call('screenshot',str(ROOT/'docs/previews'/f'round17-about-{width}.png'))
print('PASS: native heading stays fixed while stacking; all four visible layer offsets survive release and heading leaves with final card on phone/PC.',flush=True)

for width in [320,390,800,960,1024,1440]:
    call('set','viewport',str(width),'1000');settle();center('.certificate-scene');call('mouse','move','0','0');settle()
    js('document.querySelectorAll("[data-certificate]").forEach(e=>{e.classList.remove("is-front");e.setAttribute("aria-pressed","false")});dispatchEvent(new Event("resize"))');settle()
    row=js('''(()=>{const c=[...document.querySelectorAll('[data-certificate]')],r=e=>e.getBoundingClientRect();return{values:c.map(e=>e.dataset.certificateValue),centers:c.map(e=>r(e).top+r(e).height/2),left:c.map(e=>r(e).left),right:c.map(e=>r(e).right),scene:r(document.querySelector('.certificate-scene')).toJSON()}})()''')
    assert row['values']==['front','1000','2000','3000'],row
    assert max(row['centers'])-min(row['centers'])<1,row
    assert all(row['right'][i]<=row['left'][i+1]+1 for i in range(3)),row
    for value in row['values']:
        selector=f'[data-certificate-value="{value}"]';call('focus',selector);call('press','Enter');settle()
        assert js('document.querySelectorAll("[data-certificate][aria-pressed=true]").length')==1
        assert js('document.querySelector("[data-certificate].is-front").dataset.certificateValue')==value
    report['certificates'].append({'width':width,**row})
    if width in [390,1440]:call('screenshot',str(ROOT/'docs/previews'/f'round17-certificate-{width}.png'))
print('PASS: four certificates form one non-overlapping baseline at six widths; all four keyboard selections come to front exclusively.',flush=True)

call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/');settle();call('mouse','move','0','0')
js('window.__qaErrors=[];addEventListener("error",e=>window.__qaErrors.push(e.message));addEventListener("unhandledrejection",e=>window.__qaErrors.push(String(e.reason)))')
assert js('document.querySelectorAll(".hero-slide").length===10&&document.querySelectorAll("[data-hero-dot]").length===10')
assert js('getComputedStyle(document.querySelector(".header-nav>a")).borderRadius')=='24px 12px 12px 24px'
js('document.querySelector(".hero-scene").scrollIntoView({block:"center",behavior:"instant"})');settle()
call('wait','--fn','document.querySelectorAll("[data-hero-dot]")[1].getAttribute("aria-current")==="true"')
call('hover','.hero-slide[data-hero-active=true]');settle()
assert js('document.querySelector(".hero-slide[data-hero-active=true]").dataset.newsExpanded')=='true'
current=js('document.querySelector(".hero-slide[data-hero-active=true]").dataset.newsId')
js('(async()=>{await new Promise(r=>setTimeout(r,6200));return true})()')
assert js('document.querySelector(".hero-slide[data-hero-active=true]").dataset.newsId')==current
call('click','.hero-slide[data-hero-active=true] .hero-edge-next');settle()
call('wait','--fn','document.querySelectorAll("[data-hero-dot]")[2].getAttribute("aria-current")==="true"')
call('click','.hero-slide[data-hero-active=true] .hero-edge-prev');settle()
call('wait','--fn','document.querySelectorAll("[data-hero-dot]")[1].getAttribute("aria-current")==="true"')
call('focus','.hero-rail')
for i in range(10):call('press','ArrowRight');settle()
assert js('document.querySelectorAll("[data-hero-dot]")[1].getAttribute("aria-current")')=='true'
assert js('[...document.querySelectorAll(".hero-photo")].every(i=>i.complete&&i.naturalWidth>0)')
assert js('![...document.querySelectorAll("[data-news-text]")].some(e=>/Показать (ещ[её]|полностью)/.test(e.textContent))')
print('PASS: ten real news slides, image decoding, autoplay/hover-pause, native edge clicks and keyboard wrap; provider UI labels excluded from post text.',flush=True)

for width in [320,390]:
    call('set','viewport',str(width),'1000');settle();center('.hero-scene');call('mouse','move','0','0')
    call('press','Tab');call('focus','.hero-slide[data-hero-active=true] [data-news-toggle]');settle()
    assert js('''(()=>{const c=document.querySelector('.hero-slide[data-hero-active=true]'),p=c.querySelector('.hero-news-details'),a=c.querySelector('.hero-news-link'),s=getComputedStyle(a),ps=getComputedStyle(p),r=a.getBoundingClientRect(),pr=p.getBoundingClientRect();return !p.inert&&a.scrollWidth<=a.clientWidth+1&&r.height>=44&&parseFloat(s.paddingLeft)>=12&&r.left>=pr.left+parseFloat(ps.paddingLeft)-1&&r.right<=pr.right-parseFloat(ps.paddingRight)+1})()''')
    call('click','.hero-slide[data-hero-active=true] .hero-edge-next');settle()
print('PASS: narrow news text actions keep one line and 44px targets; the edge remains clickable beside the text panel.',flush=True)

call('set','viewport','1440','1000');settle();center('.of-rail');call('focus','.of-rail');call('press','Home');settle();call('mouse','move','0','0');settle()
base=js('getComputedStyle(document.querySelector("#offer-coffee")).backgroundColor')
call('hover','#offer-coffee .of-title');settle()
assert js('getComputedStyle(document.querySelector("#offer-coffee")).backgroundColor')==base
assert abs(float(js('getComputedStyle(document.querySelector("#offer-coffee img")).scale'))-1.035*1.025)<.0001
call('hover','#offer-first-visit .of-title');settle()
assert abs(float(js('getComputedStyle(document.querySelector("#offer-first-visit img")).scale'))-1.025)<.0001
if js('document.querySelector(".footer [data-feedback-toggle]").getAttribute("aria-pressed")')!='true':
    center('.footer [data-feedback-toggle]');call('click','.footer [data-feedback-toggle]');settle()
js('window.__played=[];HTMLMediaElement.prototype.play=function(){window.__played.push(this.src);return Promise.resolve()}')
center('[data-of-next]');call('click','[data-of-next]');settle()
call('focus','.of-rail');call('press','ArrowRight');settle()
assert js('window.__played.map(s=>new URL(s).pathname)')==['/audio/select.wav','/audio/select.wav']
print('PASS: offer backgrounds stay fixed, active/hover scales compose, and each trusted offer change requests one shared sound.',flush=True)

call('mouse','move','0','0');call('focus','.header-logo');settle()
font=js('''(()=>{const c=document.createElement('canvas').getContext('2d');c.font='64px Molot,monospace';const a=c.measureText('%').width;c.font='64px Molot,serif';return{a,b:c.measureText('%').width,selection:getComputedStyle(document.body,'::selection').backgroundColor}})()''')
assert font['a']==font['b'] and font['a']>0 and font['selection']=='rgb(196, 47, 42)',font
js('(()=>{const p=document.createElement("p");p.dataset.qaTypography="";p.append("В ");const a=document.createElement("a");a.textContent="Кирове";p.append(a," и в СОЮЗЕ");document.body.append(p)})()')
call('wait','--fn','document.querySelector("[data-qa-typography]").textContent.includes("В\\u00a0Кирове")')
assert js('document.querySelector("[data-qa-typography] a").textContent')=='Кирове'
js('document.querySelector("[data-qa-typography]").remove()')
call('set','media','light','reduced-motion');settle()
assert js('matchMedia("(prefers-reduced-motion:reduce)").matches&&getComputedStyle(document.querySelector(".about-layer")).position!=="sticky"')
assert js('getComputedStyle(document.querySelector(".of-photo img")).scale')=='none'
call('set','media','light');settle()
assert js('window.__qaErrors')==[]
report['font']=font
(ROOT/'tmp/planning/iteration16-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: native Molot percent, branded selection, dynamic nonbreaking prepositions, real reduced-motion emulation and no local JavaScript errors.',flush=True)
