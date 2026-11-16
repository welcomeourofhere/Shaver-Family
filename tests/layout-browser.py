"""Actual responsive composition, team adjacency and automatic hero behavior."""
import json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ['AGENT_BROWSER_SOCKET_DIR']=str(ROOT/'.local/browser-qa')
CLI=['node','node_modules/agent-browser/bin/agent-browser.js','--session',os.environ.get('SOYUZ_QA_SESSION','soyuzfinal'),'--json']
def call(*args,script=None):
    r=subprocess.run(CLI+list(args),input=script,text=True,encoding='utf-8',capture_output=True,timeout=45)
    assert r.returncode==0,r.stdout+r.stderr
    d=json.loads(r.stdout);assert d['success'],d;return d['data']
def js(s):return call('eval','--stdin',script=s)['result']
def settle():js('(async()=>{await document.fonts.ready;await Promise.allSettled(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity&&a.animationName!=="hero-photo-zoom").map(a=>a.finished));return true})()')
call('open','http://127.0.0.1:4321/');call('set','media','light','no-preference')
js('window.__localErrors=[];addEventListener("error",e=>window.__localErrors.push(e.message));addEventListener("unhandledrejection",e=>window.__localErrors.push(String(e.reason)))')
report={'geometry':[],'colors':[],'autoplay':[]}
for width in [320,360,390,540,768,800,960,1024,1280,1440,1920]:
    call('set','viewport',str(width),'1000');settle()
    m=js('''(()=>{
      const r=e=>e.getBoundingClientRect(),g=[...document.querySelectorAll('.gift-visual')],c=document.querySelector('.certificates'),s=document.querySelector('.certificate-scene'),d=document.querySelector('.certificate-description'),b=document.querySelector('.certificate-buy'),h=document.querySelector('.hero'),p=document.querySelector('.first-visit');
      return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,columns:new Set(g.map(x=>Math.round(r(x).left))).size,rows:new Set(g.map(x=>Math.round(r(x).top))).size,squares:g.every(x=>Math.abs(r(x).width-r(x).height)<1),colors:new Set(g.map(x=>getComputedStyle(x).backgroundColor)).size,iconRatio:r(g[0].querySelector('.gift-icon')).width/r(g[0]).width,aligned:Math.abs(r(c).bottom-r(g.at(-1)).bottom),scene:r(s).height,descriptionBelow:r(d).top>=r(s).bottom-1,buyBelow:r(b).top>=r(d).bottom-1,promoOverflow:p.scrollHeight>p.clientHeight+1,headerGap:r(h).top-r(document.querySelector('.header-capsule')).bottom,arrows:document.querySelectorAll('[data-hero-prev],[data-hero-next]').length};
    })()''')
    assert not m['overflow'] and not m['promoOverflow'],m
    assert m['columns']==3 and m['rows']==2 and m['squares'] and m['colors']==4,m
    assert abs(m['iconRatio']-.7/1.61803398875)<.001,m
    assert m['descriptionBelow'] and m['buyBelow'] and m['scene']>80 and m['arrows']==0,m
    if width>960: assert m['aligned']<1 and m['headerGap']>=27,m
    report['geometry'].append(m)
print('PASS: 11 widths, 3x2 square gifts, four brand colors, smaller icon ratio, reduced certificate and correct copy order.',flush=True)
# Check actual computed colors, including every singly hovered card in both grids.
for width in [390,1440]:
    call('set','viewport',str(width),'1000');settle()
    js('document.activeElement.blur();document.querySelector("#masters").scrollIntoView({block:"start",behavior:"instant"})')
    call('mouse','move','0','0');settle()
    base=js('[...document.querySelectorAll(".team-card")].map(x=>getComputedStyle(x).backgroundColor)')
    columns=2 if width<=800 else 3
    for selected in range(-1,6):
        if selected>=0:
            js(f'document.querySelector(".team-card:nth-child({selected+1}) .team-copy").scrollIntoView({{block:"center",behavior:"instant"}})');settle()
            call('hover',f'.team-card:nth-child({selected+1}) .team-copy');settle()
            assert js(f'document.querySelector(".team-card:nth-child({selected+1})").matches(":hover")')
        colors=js('[...document.querySelectorAll(".team-card")].map(x=>getComputedStyle(x).backgroundColor)')
        for i in range(6):
            if i%columns<columns-1:assert colors[i]!=colors[i+1],(width,selected,i,colors)
            if i+columns<6:assert colors[i]!=colors[i+columns],(width,selected,i,colors)
        if selected>=0:assert colors[selected]!=base[selected],(width,selected,colors,base)
        report['colors'].append({'width':width,'selected':selected,'colors':colors})
        if selected>=0:
            js(f'document.querySelector(".team-card:nth-child({selected+1}) .team-book").scrollIntoView({{block:"center",behavior:"instant"}})');settle()
            call('hover',f'.team-card:nth-child({selected+1}) .team-book');settle()
            button=js(f"(()=>{{const e=document.querySelector('.team-card:nth-child({selected+1}) .team-book'),s=getComputedStyle(e);return {{bg:s.backgroundColor,card:getComputedStyle(e.closest('.team-card')).backgroundColor,border:s.borderTopWidth,shadow:s.boxShadow}}}})()")
            assert button['bg']!=button['card'] and button['border']=='0px' and button['shadow']=='none',(width,selected,button)

    # No click-sticky highlight when the mouse leaves a card.
    call('mouse','move','0','0');settle()
    assert js('[...document.querySelectorAll(".team-card")].map(x=>getComputedStyle(x).backgroundColor)')==base
print('PASS: resting and every single hover have no orthogonal color repeats on desktop and phone widths.',flush=True)
# Shorter scene must still contain cards through scroll spread and pointer tilt.
for width in [320,390,960,1024,1440]:
    call('set','viewport',str(width),'1000');settle()
    js('document.querySelector(".certificate-scene").scrollIntoView({block:"center",behavior:"instant"})');settle()
    call('hover','.certificate-scene');settle()
    state=js('''(()=>{const s=document.querySelector('.certificate-scene'),r=s.getBoundingClientRect(),overhang=parseFloat(getComputedStyle(s).getPropertyValue('--certificate-overhang'));return [...document.querySelectorAll('.certificate-object')].every(x=>{const c=x.getBoundingClientRect();return c.top>=r.top-overhang*2-1&&c.bottom<=r.bottom+1})})()''')
    assert state,('certificate escaped scene',width)
print('PASS: certificates fit their reserved overlay bounds on five widths.',flush=True)
# Real timed autoplay, hover pause, explicit pause, manual dots and reduced-motion.
call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/');settle()
js('scrollTo({top:0,behavior:"instant"})');call('mouse','move','0','0')
call('wait','--fn','document.querySelectorAll("[data-hero-dot]")[1].getAttribute("aria-current")==="true"')
call('hover','.hero-scene');settle()
current=js('document.querySelector("[data-hero-dot][aria-current=true]").getAttribute("aria-label")')
js('(async()=>{await new Promise(r=>setTimeout(r,6300));return true})()')
assert js('document.querySelector("[data-hero-dot][aria-current=true]").getAttribute("aria-label")')==current
call('mouse','move','0','0')
call('wait','--fn','document.querySelectorAll("[data-hero-dot]")[2].getAttribute("aria-current")==="true"')
assert js('document.querySelector("[data-hero-rotation]")===null')
call('click','[data-hero-dot]:first-child');settle()
assert js('document.querySelectorAll("[data-hero-dot]")[0].getAttribute("aria-current")')=='true'
call('set','media','light','reduced-motion');settle()
assert js('document.querySelector(".hero-position").getAttribute("aria-live")')=='polite'
assert js('getComputedStyle(document.querySelector(".hero-dot"),"::after").transitionDuration')=='0s'
report['autoplay']=['automatic next','hover pause > interval','resume after leave','no play/pause button','manual selection','reduced motion']
call('set','media','light','no-preference')
print('PASS: real autoplay, hover pause, resume, manual selection pause and reduced-motion.',flush=True)
(ROOT/'tmp/planning/layout-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
