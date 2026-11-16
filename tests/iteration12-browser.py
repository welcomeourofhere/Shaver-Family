"""Owner facts, shared contacts, brand palette and intentional overlay geometry."""
import json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ['AGENT_BROWSER_SOCKET_DIR']=str(ROOT/'.local/browser-qa')
CLI=['node','node_modules/agent-browser/bin/agent-browser.js','--session',os.environ.get('SOYUZ_QA_SESSION','soyuzfinal'),'--json']
def call(*a,script=None):
    r=subprocess.run(CLI+list(a),input=script,text=True,encoding='utf-8',capture_output=True,timeout=45)
    assert r.returncode==0,r.stdout+r.stderr
    d=json.loads(r.stdout);assert d['success'],d;return d['data']
def js(s):return call('eval','--stdin',script=s)['result']
def settle():js('(async()=>{await document.fonts.ready;await Promise.allSettled(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity&&a.animationName!=="hero-photo-zoom").map(a=>a.finished));return true})()')
call('open','http://127.0.0.1:4321/');call('set','media','light','no-preference')
js('window.__localErrors=[];addEventListener("error",e=>window.__localErrors.push(e.message));addEventListener("unhandledrejection",e=>window.__localErrors.push(String(e.reason)))')
report={'geometry':[],'contacts':[],'externalSubmission':False}
for width in [320,360,390,540,600,650,651,768,800,960,1024,1280,1440,1920]:
    call('set','viewport',str(width),'1000');settle()
    js('document.querySelector(".certificate-scene").scrollIntoView({behavior:"instant",block:"center"})');settle()
    m=js('''(()=>{const r=e=>e.getBoundingClientRect(),g=[...document.querySelectorAll('.gift-visual')],c=document.querySelector('.certificates'),s=document.querySelector('.certificate-scene'),t=document.querySelector('.certificate-copy'),p=document.querySelector('.certificate-description'),b=document.querySelector('.certificate-buy'),cards=[...document.querySelectorAll('.certificate-object')],h=document.querySelector('.hero-scene'),n=document.querySelector('.hero-nav'),a=document.querySelector('.cashback-illustration'),over=parseFloat(getComputedStyle(s).getPropertyValue('--certificate-overhang'));return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,colors:g.map(x=>getComputedStyle(x).backgroundColor),square:g.every(x=>Math.abs(r(x).width-r(x).height)<1),icon:r(g[0].querySelector('.gift-icon')).width/r(g[0]).width,aligned:Math.abs(r(c).bottom-r(g.at(-1)).bottom),order:r(t).top>=r(s).bottom-1&&r(p).top>=r(t).bottom-1&&r(b).top>=r(p).bottom-1,cardsFit:cards.every(x=>r(x).top>=r(s).top-over*2-1&&r(x).bottom<=r(s).bottom+1),peek:r(c).top-Math.min(...cards.map(x=>r(x).top)),photoBottom:r(h).bottom,flagTop:r(a).top,navRight:r(n).right,photoRight:r(h).right,description:parseFloat(getComputedStyle(document.querySelector('.sd-description')).fontSize),name:parseFloat(getComputedStyle(document.querySelector('.sd-summary')).fontSize),timeOpacity:getComputedStyle(document.querySelector('.sd-duration')).opacity}})()''')
    assert not m['overflow'] and m['square'] and m['order'] and m['cardsFit'],m
    assert abs(m['icon']-.7/1.61803398875)<.001 and len(set(m['colors']))==4,m
    for i,color in enumerate(m['colors']):
        if i%3<2:assert color!=m['colors'][i+1]
        if i+3<6:assert color!=m['colors'][i+3]
    if width>960:assert m['aligned']<1,m
    if 651<=width<=800:assert m['flagTop']<m['photoBottom']-10 and m['photoRight']-m['navRight']>=59,m
    assert m['description']<m['name'] and float(m['timeOpacity'])==.6,m
    assert m['peek']>0,m
    report['geometry'].append(m)
print('PASS: 14 widths, overlay certificate/copy order, primary gift colors, 30% smaller icons, subtle service type and flag/photo overlap.',flush=True)
# Actual header phone opens the shared chooser; narrow screens use the same chooser.
for width in [320,390,1440]:
    call('set','viewport',str(width),'1000');settle()
    selector='.header-phone' if width>960 else '.certificate-buy'
    js(f'document.querySelector("{selector}").scrollIntoView({{behavior:"instant",block:"center"}})');settle()
    call('click',selector);settle()
    chooser='.header-contact' if width>960 else '.contact-dialog'
    state=js('''(()=>{const d=document.querySelector('CHOOSER');return {open:d.open,overflow:d.scrollWidth>d.clientWidth+1,channels:[...d.querySelectorAll('[data-contact-channel]')].map(x=>({id:x.dataset.contactChannel,href:x.getAttribute('href'),disabled:x.matches(':disabled'),height:x.getBoundingClientRect().height,wrap:x.scrollWidth>x.clientWidth+1,icon:x.querySelector('use')?.getAttribute('href')}))}})()'''.replace('CHOOSER',chooser))
    assert state['open'] and not state['overflow'],state
    assert [c['id'] for c in state['channels']]==['telegram','max','vk','phone'],state
    assert state['channels'][0]['href']=='https://t.me/+79229090043'
    assert state['channels'][1]['disabled'] and state['channels'][1]['href'] is None
    assert state['channels'][2]['href']=='https://vk.me/soyuz_kirov'
    assert state['channels'][3]['href']=='tel:+79229090043'
    assert all(c['height']>=44 and not c['wrap'] and c['icon'] for c in state['channels']),state
    call('press','Escape');settle();assert js(f'!document.querySelector("{chooser}").open')
    assert js(f'document.activeElement.matches("{selector}")')
    report['contacts'].append({'width':width,**state})
print('PASS: real phone/CTA chooser, four original logos, MAX placeholder, keyboard close/return focus, one-line labels.',flush=True)
call('set','viewport','1440','1000');js('scrollTo({top:0,behavior:"instant"})');settle()
call('hover','.header-nav > a:first-child');settle()
assert js('getComputedStyle(document.querySelector(".header-nav > a:first-child")).borderRadius')=='999px 12px 12px 999px'
for i in range(5):
    call('hover',f'[data-sd-tab="{i}"]');settle()
    assert js(f'getComputedStyle(document.querySelector("[data-sd-tab=\\"{i}\\"]")).backgroundColor===getComputedStyle(document.querySelector("[data-sd-panel=\\"{i}\\"]")).backgroundColor')
people=js('[...document.querySelectorAll(".team-card")].map(x=>({id:x.querySelector("[data-master]").dataset.master,hobby:x.querySelector(".team-hobby").textContent,reviews:x.querySelector(".team-facts p:last-child").textContent,label:x.querySelector(".team-discover").textContent.trim()}))')
expected=['37 отзывов','41 отзыв','99 отзывов','114 отзывов','213 отзывов','544 отзыва']
assert [p['reviews'] for p in people]==expected,people
assert all(p['hobby'] and p['label']=='О мастере' for p in people)
report['people']=people
assert js('window.__localErrors')==[]
(ROOT/'tmp/planning/iteration12-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: left-only full rounding, category-specific hover colors, six review/hobby matches, clear interview action; no page JS errors.',flush=True)
