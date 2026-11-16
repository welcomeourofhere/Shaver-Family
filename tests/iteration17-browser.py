"""Owner iteration: permanent news panel, fair price, individual springs and depth."""
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
def settle():js('(async()=>{await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));await Promise.allSettled(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity&&a.animationName!=="hero-photo-zoom").map(a=>a.finished));await new Promise(r=>setTimeout(r,500));return true})()')
def center(s):js('document.querySelector('+json.dumps(s)+').scrollIntoView({behavior:"instant",block:"center"})');settle()
report={'geometry':[],'certificates':[],'story':[],'externalSubmission':False}
call('open','http://127.0.0.1:4321/');call('set','media','light');settle()
js('window.__qaErrors=[];addEventListener("error",e=>window.__qaErrors.push(e.message));addEventListener("unhandledrejection",e=>window.__qaErrors.push(String(e.reason)))')
for width in [320,360,390,540,600,650,651,768,800,960,1024,1280,1440,1920]:
    call('set','viewport',str(width),'1000');call('mouse','move','0','0');settle()
    m=js('''(()=>{const r=e=>e.getBoundingClientRect(),panel=document.querySelector('.hero-news-panel'),h=document.querySelector('.hero-scene'),p=r(panel),hr=r(h),active=document.querySelector('.hero-news-details[data-news-active=true]'),range=document.createRange(),issues=[];for(const b of document.querySelectorAll('button,.btn')){const br=r(b),s=getComputedStyle(b);if(!br.width||!br.height||b.closest('dialog:not([open]),[inert],[hidden]'))continue;if(br.height<43.9)issues.push('hit:'+b.className);if(!b.textContent.trim()||b.querySelector('img,svg')&&!b.classList.contains('btn'))continue;if(b.scrollWidth>b.clientWidth+1||parseFloat(s.paddingLeft)<12||parseFloat(s.paddingRight)<12)issues.push('label:'+b.textContent.trim());const w=document.createTreeWalker(b,NodeFilter.SHOW_TEXT);while(w.nextNode()){if(!w.currentNode.textContent.trim())continue;range.selectNodeContents(w.currentNode);if(range.getClientRects().length>1)issues.push('wrap:'+w.currentNode.textContent)}}return{width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,issues,panelEdges:[p.left-hr.left,hr.right-p.right,hr.bottom-p.bottom],panelFraction:p.height/hr.height,bodyActive:!active.inert,navInside:!!document.querySelector('.hero-news-panel .hero-nav'),oldToggle:!!document.querySelector('[data-news-toggle]'),blur:getComputedStyle(panel).backdropFilter,headline:[...document.querySelector('.hero-heading').children].map(e=>{range.selectNodeContents(e);return range.getClientRects().length}),gaps:[...document.querySelectorAll('main>.section')].map(e=>parseFloat(getComputedStyle(e).paddingTop)),fairLinks:[...document.querySelectorAll('.visit-actions [data-booking]')].map(e=>e.dataset.bookingUrl),fairPhoto:document.querySelector('.visit-art img').complete,spring:CSS.supports('animation-timing-function',getComputedStyle(document.documentElement).getPropertyValue('--ease-spring'))}})()''')
    assert not m['overflow'] and not m['issues'],m
    assert m['headline']==[1,1,1] and m['bodyActive'] and m['navInside'] and not m['oldToggle'] and m['spring'],m
    assert all(abs(v-12)<1 for v in m['panelEdges']) and m['panelFraction']<.5 and 'blur' in m['blur'],m
    assert m['gaps']==[96 if width<=800 else 128]+[128 if width<=800 else 160]*(len(m['gaps'])-1),m
    assert m['fairLinks']==['https://n2266404.yclients.ru/','https://n2440449.yclients.ru/'],m
    report['geometry'].append(m)
print('PASS: 14 widths, permanent compact glass panel, three-line headline, shared spring, longer section rhythm and single-line button labels.',flush=True)

call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/');call('mouse','move','0','0');settle()
js('window.__qaErrors=[];addEventListener("error",e=>window.__qaErrors.push(e.message));addEventListener("unhandledrejection",e=>window.__qaErrors.push(String(e.reason)))')
call('wait','--fn','document.querySelectorAll("[data-hero-dot]")[1].getAttribute("aria-current")==="true"')
call('hover','.hero-slide[data-hero-active=true] .hero-edge-next');settle()
assert js('getComputedStyle(document.querySelector(".hero-slide[data-hero-active=true] .hero-edge-next"),"::before").opacity')=='1'
assert 'blur' in js('getComputedStyle(document.querySelector(".hero-slide[data-hero-active=true] .hero-edge-next"),"::before").backdropFilter')
call('click','.hero-slide[data-hero-active=true] .hero-edge-next');settle()
assert js('document.querySelectorAll("[data-hero-dot]")[2].getAttribute("aria-current")')=='true'
call('click','.hero-slide[data-hero-active=true] .hero-edge-prev');settle()
assert js('document.querySelectorAll("[data-hero-dot]")[1].getAttribute("aria-current")')=='true'
js('window.__indicatorFrames=[];window.__indicatorUntil=performance.now()+1000;(function sample(){const n=document.querySelector(".hero-nav"),r=n.getBoundingClientRect();window.__indicatorFrames.push({left:r.left,width:r.width,sum:[...n.children].reduce((s,e)=>s+e.getBoundingClientRect().width,0)});if(performance.now()<window.__indicatorUntil)requestAnimationFrame(sample)})()')
call('click','.hero-dot:nth-child(9)');settle()
trace=js('window.__indicatorFrames');assert max(x['width'] for x in trace)-min(x['width'] for x in trace)<.1
assert max(x['sum'] for x in trace)-min(x['sum'] for x in trace)<.1
assert js('document.querySelectorAll(".hero-news-details:not([inert])").length')==1
report['indicatorFrames']=len(trace)
print('PASS: real autoplay, both edge clicks and edge blur; spring indicator preserves total width, one accessible news body.',flush=True)

for width in [320,390,800,960,1024,1440]:
    call('set','viewport',str(width),'1000');center('.certificate-scene');call('mouse','move','0','0');settle()
    before=js('''(()=>{const c=[...document.querySelectorAll('[data-certificate]')],r=e=>e.getBoundingClientRect();return{values:c.map(e=>e.dataset.certificateValue),rects:c.map(e=>r(e).toJSON()),origins:c.map(e=>getComputedStyle(e).transformOrigin),stackTransform:getComputedStyle(document.querySelector('.certificate-stack')).transform,copyTop:r(document.querySelector('.certificate-copy')).top,sceneTop:r(document.querySelector('.certificate-scene')).top}})()''')
    assert before['values']==['front','1000','2000','3000'] and before['stackTransform']=='none',before
    assert all(before['rects'][i]['right']>before['rects'][i+1]['left'] for i in range(3)),before
    assert max(r['bottom'] for r in before['rects'])<before['copyTop']+1,before
    assert max(r['top'] for r in before['rects'])-min(r['top'] for r in before['rects'])<1,before
    if width==320: assert js('''[...document.querySelectorAll('[data-certificate]')].map(c=>getComputedStyle(c).zIndex).join(',')''')=='4,3,2,1'
    for value in before['values']:
        call('focus',f'[data-certificate-value="{value}"]');call('press','Enter');settle()
        assert js('document.querySelectorAll("[data-certificate][aria-pressed=true]").length')==1
        assert js('document.querySelector("[data-certificate].is-front").dataset.certificateValue')==value
        assert not js('document.documentElement.scrollWidth>innerWidth+1')
    report['certificates'].append({'width':width,**before})
call('set','viewport','1440','1000');center('.certificate-scene');call('mouse','move','0','0');settle()
call('focus','[data-certificate-value="front"]');call('press','Enter');settle()
point=js('''(()=>{const c=document.querySelector('[data-certificate-value="1000"]'),r=c.getBoundingClientRect();for(let y=r.top+12;y<r.bottom-12;y+=8)for(let x=r.left+12;x<r.right-12;x+=8)if(document.elementFromPoint(x,y)?.closest('[data-certificate]')===c)return{x,y};return null})()''');assert point
before=js('[...document.querySelectorAll(".certificate-art")].map(c=>c.style.transform)')
call('mouse','move',str(round(point['x'])),str(round(point['y'])));settle()
after=js('[...document.querySelectorAll(".certificate-art")].map(c=>c.style.transform)')
assert before[1]!=after[1] and before[0]==after[0] and before[2:]==after[2:],(before,after)
call('mouse','move','0','0');settle()
print('PASS: straight overlapping certificates at six widths, all four keyboard selections; stable hit areas, native pointer affects only its own artwork, no group tilt.',flush=True)

for width in [390,1440]:
    call('set','viewport',str(width),'1000');js('scrollTo({top:0,behavior:"instant"})');settle()
    trace=js('''(async()=>{const layers=[...document.querySelectorAll('.about-layer')],cards=[...document.querySelectorAll('.about-card')],stack=document.querySelector('.about-stack'),title=document.querySelector('#about-title'),height=cards[0].offsetHeight,gap=parseFloat(getComputedStyle(stack).rowGap),origin=stack.getBoundingClientRect().top+scrollY+parseFloat(getComputedStyle(stack).paddingTop),stops=layers.map((e,i)=>origin+i*(height+gap)-parseFloat(getComputedStyle(e).top)),out=[];for(const y of [stops[1],(stops[1]+stops[2])/2,stops[2],stops[3]]){scrollTo({top:y,behavior:'instant'});await new Promise(r=>setTimeout(r,700));out.push({title:title.getBoundingClientRect().top,tops:cards.map(c=>c.getBoundingClientRect().top),scale:cards.map(c=>new DOMMatrix(getComputedStyle(c).transform).a)})}return{stops,out,step:parseFloat(getComputedStyle(stack).getPropertyValue('--about-stack-step'))}})()''')
    assert max(x['title'] for x in trace['out'])-min(x['title'] for x in trace['out'])<1,trace
    final=trace['out'][-1]
    assert all(final['scale'][i]<final['scale'][i+1] for i in range(3)) and abs(final['scale'][3]-1)<.001,trace
    assert all(abs(final['tops'][i+1]-final['tops'][i]-trace['step'])<1 for i in range(3)),trace
    report['story'].append({'width':width,**trace})
    call('screenshot',str(ROOT/'docs/previews'/f'round18-about-{width}.png'))
print('PASS: previous story cards shrink progressively while native heading and visible equal steps remain stable on phone/PC.',flush=True)

call('set','media','light','reduced-motion');settle()
assert js('matchMedia("(prefers-reduced-motion:reduce)").matches&&getComputedStyle(document.querySelector(".about-card")).transform==="none"')
assert js('[...document.querySelectorAll(".certificate-art")].every(c=>c.style.transform==="none")')
call('set','media','light');settle()
assert js('window.__qaErrors')==[]
(ROOT/'tmp/planning/iteration17-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: reduced motion and no local JS errors; report saved. No booking or message submitted.',flush=True)
