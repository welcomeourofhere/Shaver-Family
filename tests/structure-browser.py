"""Story stacking, offer composition, FAQ and personal booking routing in Chromium."""
import json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ['AGENT_BROWSER_SOCKET_DIR']=str(ROOT/'.local/browser-qa')
CLI=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuzfinal','--json']
def call(*args,script=None):
    p=subprocess.run(CLI+list(args),input=script,text=True,encoding='utf-8',capture_output=True,timeout=45)
    assert p.returncode==0,p.stdout+p.stderr
    result=json.loads(p.stdout);assert result['success'],result;return result['data']
def js(s):return call('eval','--stdin',script=s)['result']
def settle():js('(async()=>{await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));await Promise.allSettled(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity&&a.animationName!=="hero-photo-zoom").map(a=>a.finished));return true})()')
def center(s):js('document.querySelector('+json.dumps(s)+').scrollIntoView({behavior:"instant",block:"center"})');settle()
call('open','http://127.0.0.1:4321/');call('set','media','light','no-preference')
js('window.__errors=[];addEventListener("error",e=>window.__errors.push(e.message));addEventListener("unhandledrejection",e=>window.__errors.push(String(e.reason)))')
report={'geometry':[],'stack':[],'bookings':[],'externalSubmission':False}
for width in [320,360,390,540,600,650,651,768,800,960,1024,1280,1440,1920]:
    call('set','viewport',str(width),'1000');settle();center('#about')
    m=js('''(()=>{const r=e=>e.getBoundingClientRect(),cards=[...document.querySelectorAll('.about-card')],tops=cards.map(x=>parseFloat(getComputedStyle(x.parentElement).top)),copies=cards.map(x=>r(x.querySelector('.about-copy')).height),offers=[...document.querySelectorAll('.of-card')],faq=document.querySelector('.faq-list'),title=document.querySelector('.faq-title'),visit=document.querySelector('#first-visit'),team=document.querySelector('#masters');return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,heights:cards.map(x=>r(x).height),copies,tops,step:parseFloat(getComputedStyle(document.querySelector('.about-stack')).getPropertyValue('--about-stack-step')),photoInset:cards.map(c=>({top:r(c.querySelector('.about-media')).top-r(c).top,right:r(c).right-r(c.querySelector('.about-media')).right})),buttons:document.querySelectorAll('.about-card button,.about-card a').length,offerActions:offers.every(x=>x.querySelectorAll('.of-action').length===1),offerFull:offers.every(x=>{const b=x.querySelector('.of-action'),p=x.querySelector('.of-card-copy'),s=getComputedStyle(p);return Math.abs(r(b).width-(r(p).width-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight)))<1}),offerPhotos:document.querySelectorAll('.of-photo').length,oldOffers:document.querySelectorAll('.of-eyebrow,.of-icon,[data-of-open]').length,faqAside:r(title).right<=r(faq).left+1,visitAfter:team.nextElementSibling===visit,photoOverlay:r(visit.querySelector('.visit-photo')).top<r(visit.querySelector('.visit-ticket')).top,faqCount:document.querySelectorAll('.faq-item').length}})()''')
    assert not m['overflow'] and m['buttons']==0,m
    assert max(m['heights'])-min(m['heights'])<1 and max(m['copies'])-min(m['copies'])<1,m
    assert all(abs(m['tops'][i+1]-m['tops'][i]-m['step'])<.1 for i in range(3)),m
    assert all(abs(x['top']-12)<1 and abs(x['right']-12)<1 for x in m['photoInset']),m
    assert m['offerActions'] and m['offerFull'] and m['offerPhotos']==10 and m['oldOffers']==0,m
    assert m['visitAfter'] and m['photoOverlay'] and m['faqCount']==8,m
    if width>800:assert m['faqAside'],m
    if width==1440:assert m['tops'][0]>=(1000-m['heights'][0])/2,m
    report['geometry'].append(m)
print('PASS: 14 widths; equal story/copy heights and stack steps, 12px photo frame, no story actions, ten photo slots/full-width actions, first-visit order and FAQ.',flush=True)
# Check actual sticky positions while each subsequent card reaches its resting level.
for width in [390,1440]:
    call('set','viewport',str(width),'1000');settle()
    js('scrollTo({top:0,behavior:"instant"})');settle()
    stops=js('[...document.querySelectorAll(".about-layer")].map(e=>e.getBoundingClientRect().top+scrollY-parseFloat(getComputedStyle(e).top))')
    for index in [1,2,3]:
        js(f'scrollTo({{top:{stops[index]},behavior:"instant"}})');settle()
        m=js(f'''(()=>{{const cards=[...document.querySelectorAll('.about-card')],selected=cards[{index}],r=selected.getBoundingClientRect();return {{index:{index},width:innerWidth,top:r.top,target:parseFloat(getComputedStyle(selected.parentElement).top),bottom:r.bottom,previous:cards.slice(0,{index}).map(c=>({{top:c.getBoundingClientRect().top,target:parseFloat(getComputedStyle(c.parentElement).top)}})),safeBottom:Math.min(...[...document.querySelectorAll('.mobile-nav,.mobile-nav-book')].filter(e=>e.offsetHeight).map(e=>e.getBoundingClientRect().top),innerHeight)}}}})()''')
        assert abs(m['top']-m['target'])<1,m
        assert all(abs(x['top']-x['target'])<1 for x in m['previous']),m
        assert m['bottom']<m['safeBottom'],m
        report['stack'].append(m)
    tail=js('parseFloat(getComputedStyle(document.querySelector(".about-stack")).getPropertyValue("--about-stack-tail"))')
    js(f'scrollBy({{top:{min(8,tail/2)},behavior:"instant"}})');settle()
    assert js('Math.abs(document.querySelectorAll(".about-card")[3].getBoundingClientRect().top-parseFloat(getComputedStyle(document.querySelectorAll(".about-card")[3].parentElement).top))<1')
print('PASS: equal actual sticky levels and readable bottom on phone and PC.',flush=True)
# Native FAQ keyboard disclosure, exclusive opening and close.
for width in [390,1440]:
    call('set','viewport',str(width),'1000');settle()
    for i in range(8):
        selector=f'.faq-item:nth-child({i+1}) summary';center(selector);call('focus',selector);call('press','Enter');settle()
        assert js(f'document.querySelectorAll(".faq-item[open]").length===1&&document.querySelectorAll(".faq-item")[{i}].open')
    call('press','Enter');assert js('document.querySelectorAll(".faq-item[open]").length')==0
print('PASS: eight FAQ items by keyboard at both layouts.',flush=True)
# Only verify drawer navigation. No provider forms or real appointment submissions.
people=json.loads((ROOT/'content/team.json').read_text(encoding='utf-8'))['masters']
call('set','viewport','1440','1000');settle()
for p in people:
    selector=f'.team-book[data-booking-url="{p["bookingUrl"]}"]';center(selector);call('click',selector);settle()
    state=js('''(()=>{const d=document.querySelector('[data-booking-drawer]');return {open:d.open,url:d.dataset.bookingUrl,frame:d.querySelector('iframe').getAttribute('src'),external:d.querySelector('[data-booking-external]').getAttribute('href')}})()''')
    expected=p['bookingUrl'].replace('https://n','https://b')
    assert state['open'] and state['url']==expected and state['frame']==expected and state['external']==p['bookingUrl'],(p['id'],state)
    call('press','Escape');settle();report['bookings'].append({'id':p['id'],**state})
center('.header-book');call('click','.header-book');settle()
assert js('document.querySelector("[data-booking-frame]").getAttribute("src")')=='https://b2763199.yclients.ru/'
call('press','Escape');settle()
assert js('window.__errors')==[]
(ROOT/'tmp/planning/structure-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: six individual destinations and general booking reset; no local JS errors.',flush=True)
