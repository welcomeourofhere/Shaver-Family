"""Integration checks for shared geometry, states, promotions and feedback."""
import json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.environ['AGENT_BROWSER_SOCKET_DIR']=str(ROOT/'.local/browser-qa')
CLI=['node','node_modules/agent-browser/bin/agent-browser.js','--session',os.environ.get('SOYUZ_QA_SESSION','soyuzfinal'),'--json']
def call(*args,script=None):
    r=subprocess.run(CLI+list(args),input=script,text=True,encoding='utf-8',capture_output=True,timeout=45)
    if r.returncode: raise RuntimeError(r.stdout+r.stderr)
    result=json.loads(r.stdout)
    assert result['success'],result
    return result['data']
def js(script): return call('eval','--stdin',script=script)['result']
def settle(): js('(async()=>{await document.fonts.ready;await Promise.allSettled(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity&&a.animationName!=="hero-photo-zoom").map(a=>a.finished));return true})()')
call('open','http://127.0.0.1:4321/')
call('set','media','light')
report={'geometry':[],'states':[],'offers':[]}
for width in [320,360,390,540,768,800,960,1024,1280,1440,1920]:
    call('set','viewport',str(width),'900');settle()
    data=js('''(()=>{
      const base=document.querySelector('.hero').getBoundingClientRect();
      const selectors=['.site-header','.sd-section .shell','.of-layout','#masters','#about','#gifts','#reviews','#contacts','.footer .shell'];
      const edges=selectors.map(selector=>{const r=document.querySelector(selector).getBoundingClientRect();return {selector,left:r.left,width:r.width}});
      return {width:innerWidth,edges:edges.filter(r=>r.width&&(Math.abs(r.left-base.left)>1||Math.abs(r.width-base.width)>1)),header:document.querySelector('.header-capsule').getBoundingClientRect().height,giftColumns:new Set([...document.querySelectorAll('.gift-visual')].map(e=>Math.round(e.getBoundingClientRect().left))).size,offerWidth:document.querySelector('.of-card').getBoundingClientRect().width,overflow:document.documentElement.scrollWidth>innerWidth+1};
    })()''')
    assert not data['edges'],data
    assert data['header']==(0 if width<=960 else 64),data
    assert data['giftColumns']==3,data
    assert data['offerWidth']>=250 and not data['overflow'],data
    report['geometry'].append(data)
print('PASS: common section edges and responsive layout at 11 widths.',flush=True)
call('set','viewport','1440','900')
call('hover','h1');settle()
for selector in ['.header-nav > a:first-child','.header-phone','.header-book','.first-actions .btn','.of-card:not([inert]):first-child .of-action','[data-of-prev]']:
    call('scroll','up','100') if selector.startswith('.header') else None
    call('hover',selector);settle()
    state=js(f'(()=>{{const s=getComputedStyle(document.querySelector({json.dumps(selector)}));return {{translate:s.translate,transition:s.transitionProperty,duration:s.transitionDuration,shadow:s.boxShadow}}}})()')
    assert state['translate'] in ['none','0px','0px 0px'],(selector,state)
    assert 'color' in state['transition'],(selector,state)
    assert state['shadow']=='none',(selector,state)
    report['states'].append({'selector':selector,**state})
# The CLI's separate mouse-down command resets to (0,0). Capture native
# mousedown from a real click instead, with transition timing frozen for measurement.
js('window.__press=[];window.__pressStyle=document.createElement("style");window.__pressStyle.textContent=":is(button,a,summary){transition-duration:0s!important}";document.head.append(window.__pressStyle)')
try:
    for selector in ['.header-nav > a:first-child','.header-phone']:
        js(f'(()=>{{const el=document.querySelector({json.dumps(selector)});el.addEventListener("mousedown",()=>window.__press.push({{active:el.matches(":active"),scale:getComputedStyle(el).scale}}),{{once:true}});el.addEventListener("click",e=>e.preventDefault(),{{once:true}})}})()')
        call('scroll','up','100')
        call('click',selector)
        state=js('window.__press.at(-1)')
        assert state['active'] and state['scale']=='0.97',(selector,state)
        report['states'].append({'selector':selector,'press':state})
finally:
    js('window.__pressStyle.remove()')
call('focus','.header-phone')
call('press','Tab');call('press','Shift+Tab')
assert js('document.querySelector(".header-phone").matches(":focus-visible")')
assert js('getComputedStyle(document.querySelector(".header-phone")).outlineStyle')!='none'
call('set','media','light','reduced-motion')
call('hover','.header-phone');settle()
assert js('getComputedStyle(document.querySelector(".header-phone")).translate')=='none'
# Ten original cards loop without clone IDs; each action is a contextual booking.
call('set','media','light','reduced-motion')
js('document.querySelector(".of-rail").scrollIntoView({behavior:"instant",block:"center"})');settle()
call('focus','.of-rail');call('press','Home');settle()
ids=[]
for index in range(10):
    offer_id=js('document.querySelector(".of-rail").firstElementChild.dataset.offerId')
    ids.append(offer_id)
    selector=f'[data-offer-id="{offer_id}"] .of-action'
    call('click',selector);settle()
    contact=offer_id in ['coffee','waxing','referral']
    assert js('document.querySelector(".contact-dialog").open') if contact else js('document.querySelector("[data-booking-drawer]").open')
    if not contact:assert js('document.querySelector("[data-booking-selection]").textContent.startsWith("Акция: ")')
    call('press','Escape');settle()
    call('focus','.of-rail');call('press','ArrowRight');settle()
assert len(set(ids))==10,ids
assert js('document.querySelector("[data-offers]").dataset.offerIndex')=='0'
call('press','ArrowLeft');settle()
assert js('document.querySelector("[data-offers]").dataset.offerIndex')=='9'
assert js('!document.querySelector("[data-of-next]").disabled&&!document.querySelector("[data-of-prev]").disabled')
report['offers']=ids
print('PASS: 10 full-width contextual actions, infinite keyboard wrap both ways, no condition dialogs.',flush=True)
for width in [390,1440]:
    call('set','viewport',str(width),'900');settle()
    js('document.querySelector(".cashback").scrollIntoView({behavior:"instant",block:"center"})');settle()
    call('click','.cashback');settle()
    assert js('document.querySelector(".of-rail").firstElementChild.id')=='offer-cashback'
    assert js('!document.querySelector("#offer-cashback").inert')
print('PASS: cashback link activates its offer at both layouts.',flush=True)
# Trusted activation only, one preference reflected in both locations and reload.
js('localStorage.removeItem("soyuz_feedback_enabled")')
call('open','http://127.0.0.1:4321/')
js('window.__played=[];HTMLMediaElement.prototype.play=function(){window.__played.push(this.src);return Promise.resolve()};')
call('click','.header-book');call('press','Escape');settle()
assert js('window.__played.length')==1
js('document.querySelector(".header-book").click()')
call('press','Escape');settle()
assert js('window.__played.length')==1
call('click','.footer [data-feedback-toggle]')
assert js('[...document.querySelectorAll("[data-feedback-toggle]")].every(b=>b.getAttribute("aria-pressed")==="false")')
call('click','.header-book');call('press','Escape');settle()
assert js('window.__played.length')==1
call('open','http://127.0.0.1:4321/')
assert js('[...document.querySelectorAll("[data-feedback-toggle]")].every(b=>b.getAttribute("aria-pressed")==="false")')
call('set','viewport','390','900');call('click','[data-open-menu]')
call('click','#mobile-menu [data-feedback-toggle]')
assert js('[...document.querySelectorAll("[data-feedback-toggle]")].every(b=>b.getAttribute("aria-pressed")==="true")')
call('press','Escape');settle()
call('set','media','light')
report['feedback']='trusted click only; toggle off suppresses; both controls sync; preference persists; no physical audio/haptics claim'
(ROOT/'tmp/planning/unification-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: feedback activation, synchronization and persistence.',flush=True)
