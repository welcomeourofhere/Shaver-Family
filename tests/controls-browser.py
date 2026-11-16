"""Header menus and adjacent offer selection, including native pointer activation."""
import json,os,subprocess
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
call('open','http://127.0.0.1:4321/');call('set','viewport','1440','1000');call('set','media','light','no-preference');settle()
g=js('''(()=>{const r=e=>e.getBoundingClientRect(),c=r(document.querySelector('.header-capsule')),a=r(document.querySelector('.header-nav>a'));return {left:a.left-c.left,top:a.top-c.top,bottom:c.bottom-a.bottom,radius:getComputedStyle(document.querySelector('.header-nav>a')).borderRadius}})()''')
assert max(g['left'],g['top'],g['bottom'])-min(g['left'],g['top'],g['bottom'])<.1,g
assert g['radius']=='24px 12px 12px 24px',g
call('click','.header-phone');settle()
assert js('document.querySelector(".header-contact").open&&!document.querySelector(".contact-dialog").open')
phone=js('''(()=>{const p=document.querySelector('.header-contact-panel'),r=p.getBoundingClientRect(),s=getComputedStyle(p);return {width:r.width,radius:s.borderRadius,padding:s.padding,background:s.backgroundColor}})()''')
call('press','Escape');settle();assert js('document.activeElement.matches(".header-phone")')
call('click','.more-menu>summary');settle()
more=js('''(()=>{const p=document.querySelector('.more-panel'),r=p.getBoundingClientRect(),s=getComputedStyle(p);return {width:r.width,radius:s.borderRadius,padding:s.padding,background:s.backgroundColor}})()''')
assert phone==more,(phone,more)
call('click','.header-phone');settle()
assert js('document.querySelectorAll(".header-menu[open]").length===1&&document.querySelector(".header-contact").open')
call('press','Escape');settle()
print('PASS: equal first-nav insets and asymmetric rounding; phone/More use one anchored menu geometry, exclusive opening and Escape focus.',flush=True)
report=[]
for width in [390,1440]:
    call('set','viewport',str(width),'1000');settle()
    js('document.querySelector(".of-rail").scrollIntoView({behavior:"instant",block:"center"})');settle()
    call('focus','.of-rail');call('press','Home');settle()
    call('mouse','move','0','0')
    # Pick the visible part of the NEXT card, including the narrow mobile preview.
    # The CLI uses an offscreen full-element center for a clipped card. A temporary
    # child supplies the visible hit point without changing product geometry.
    js('(()=>{const hit=document.createElement("span");hit.dataset.qaHit="";hit.style.cssText="position:absolute;left:4px;top:40px;width:6px;height:12px";document.querySelector("#offer-first-visit .of-photo").append(hit)})()')
    call('click','[data-qa-hit]');js('document.querySelector("[data-qa-hit]").remove()')
    call('wait','--fn','document.querySelector(".of-rail").firstElementChild.id==="offer-first-visit"')
    state=js('''(()=>{const r=document.querySelector('.of-rail').getBoundingClientRect(),c=document.querySelector('#offer-first-visit').getBoundingClientRect();return {first:document.querySelector('.of-rail').firstElementChild.id,left:c.left-r.left,dialogs:document.querySelectorAll('dialog[open]').length}})()''')
    assert abs(state['left'])<1 and state['dialogs']==0,(width,state)
    call('click','#offer-first-visit .of-action');settle()
    assert js('document.querySelector("[data-booking-drawer]").open')
    assert js('document.querySelector(".of-rail").firstElementChild.id')=='offer-first-visit'
    call('press','Escape');settle();report.append({'width':width,**state})
(ROOT/'tmp/planning/controls-qa.json').write_text(json.dumps({'header':g,'menus':phone,'offers':report},indent=2),encoding='utf-8')
print('PASS: native click on adjacent card selects it at phone/PC widths; CTA remains independent.',flush=True)
