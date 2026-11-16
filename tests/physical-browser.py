"""SF-derived physical interaction and mobile presence regression in real Chrome."""
import os,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ['AGENT_BROWSER_SOCKET_DIR']=str(ROOT/'.local/browser-qa')
CLI=['node','node_modules/agent-browser/bin/agent-browser.js','--session',os.environ.get('SOYUZ_QA_SESSION','soyuzqa'),'--json']
def call(*args,script=None):
 r=subprocess.run(CLI+list(args),input=script,text=True,encoding='utf-8',capture_output=True,timeout=45)
 assert r.returncode==0,r.stdout+r.stderr
 data=json.loads(r.stdout);assert data['success'],data
 return data['data']
def js(script):return call('eval','--stdin',script=script)['result']
def settle():js('(async()=>{await document.fonts.ready;await Promise.allSettled(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity&&a.animationName!=="hero-photo-zoom").map(a=>a.finished));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return true})()')
call('open','http://127.0.0.1:4321/');call('set','media','light');call('set','viewport','1440','1000');settle()
js('window.__localErrors=[];addEventListener("error",e=>window.__localErrors.push(e.message));addEventListener("unhandledrejection",e=>window.__localErrors.push(String(e.reason)))')
report={'deck':[],'navigation':[],'interviews':[],'externalSubmission':False}
# Five fixed colour roles; actual surfaces all share top/bottom, even after reordering.
for category in [3,4,2,1,0]:
 previous=js('Number(document.querySelector(".sd-card[aria-hidden=false]").dataset.sdPanel)')
 js(f'document.querySelectorAll("[data-sd-tab]")[{category}].click()');settle()
 state=js('(()=>{const p=[...document.querySelectorAll(".sd-card")],r=p.map(x=>x.getBoundingClientRect()),a=document.querySelector(".sd-card[aria-hidden=false]"),t=document.querySelector(".sd-tab[aria-selected=true]");return {count:p.length,colors:new Set(p.map(x=>getComputedStyle(x).backgroundColor)).size,top:Math.max(...r.map(x=>x.top))-Math.min(...r.map(x=>x.top)),bottom:Math.max(...r.map(x=>x.bottom))-Math.min(...r.map(x=>x.bottom)),levels:p.map(x=>Number(x.style.getPropertyValue("--card-level"))),match:getComputedStyle(a).backgroundColor===getComputedStyle(t).backgroundColor,buttons:a.querySelectorAll("button").length}})()')
 assert state['count']==5 and state['colors']==4 and state['top']<.1 and state['bottom']<.1 and state['match'] and state['buttons']==0,state
 assert state['levels'][previous]>0 and state['levels'][category]==0,state
 report['deck'].append(state)
assert js('!document.querySelector(".sd-backs,.sd-book")')
js('document.querySelector(".sd-card[aria-hidden=false] .sd-service-area").scrollIntoView({block:"center",behavior:"instant"})');settle()
call('hover','.sd-card[aria-hidden=false] .sd-service:first-child .sd-summary');js('window.__wheelStart=scrollY');call('mouse','wheel','360');call('wait','--fn','scrollY>window.__wheelStart+100')
assert js('getComputedStyle(document.querySelector(".sd-service-area")).overflowY') not in ['auto','scroll']
assert js('parseFloat(getComputedStyle(document.querySelector(".sd-service-area")).rowGap)')>=8
# Real profile/ interview content opens, and its CTA opens the same right-side drawer.
for width in [1440,390]:
 call('set','viewport',str(width),'900');settle()
 for index in range(6):
  selector=f'.team-card:nth-child({index+1}) .team-discover'
  js(f'document.querySelector({json.dumps(selector)}).scrollIntoView({{behavior:"instant",block:"center"}})');settle()
  call('click',selector);settle()
  state=js('(()=>{const d=document.querySelector(".team-dialog[open]");return {name:d.querySelector("h2").textContent,blocks:d.querySelectorAll(".team-interview-block").length,overflow:d.scrollWidth>d.clientWidth+1}})()')
  assert state['blocks']>0 if index<3 else state['blocks']==0
  assert not state['overflow'],state
  call('click','.team-dialog[open] [data-booking]');settle();assert js('document.querySelector("[data-booking-drawer]").open')
  assert js('document.querySelector("[data-booking-selection]").textContent.includes("Запись к мастеру")')
  call('press','Escape');settle();report['interviews'].append({'width':width,**state})
# Docked reserves actual page width and must not collide header columns.
call('set','viewport','1440','1000');js('scrollTo({top:0,behavior:"instant"})');settle();call('click','.header-book');settle()
state=js('(()=>{const n=document.querySelector(".header-nav").getBoundingClientRect(),l=document.querySelector(".header-logo").getBoundingClientRect(),a=document.querySelector(".header-actions").getBoundingClientRect();return {mode:document.documentElement.dataset.bookingLayout,page:document.querySelector("[data-booking-page]").getBoundingClientRect().width,left:n.right<=l.left,right:a.left>=l.right}})()')
assert state['mode']=='docked' and state['page']==960 and state['left'] and state['right'],state
call('press','Escape');settle()
for width in [320,390,768,960]:
 call('set','viewport',str(width),'900');settle()
 assert js('getComputedStyle(document.querySelector(".site-header")).display')=='none'
 js('document.querySelector("#contacts").scrollIntoView({behavior:"instant",block:"start"})');settle()
 state=js('(()=>{const n=document.querySelector(".mobile-nav"),r=n.getBoundingClientRect(),b=n.querySelector(".mobile-nav-book-icon").getBoundingClientRect();return {width:innerWidth,count:n.children.length,bottom:r.bottom,bookCenter:b.left+b.width/2,round:getComputedStyle(n.querySelector(".mobile-nav-book-icon")).borderRadius,mask:getComputedStyle(n,"::before").maskImage,current:n.querySelector("[aria-current]")?.getAttribute("href"),overflow:document.documentElement.scrollWidth>innerWidth+1}})()')
 assert js('[...document.querySelectorAll(".mobile-nav-item span:last-child")].every(e=>e.getBoundingClientRect().bottom<=innerHeight-4)'),'Navigation labels outside viewport'
 assert state['count']==5 and abs(state['bottom']-900)<1 and abs(state['bookCenter']-width/2)<1 and state['round']=='50%' and 'radial-gradient' in state['mask'] and state['current']=='#contacts' and not state['overflow'],state
 call('click','[data-open-promo]');settle();call('click','.promo-dialog [data-copy-promo]')
 call('wait','--fn','document.querySelector("[data-toast]").classList.contains("is-visible")')
 toast=js('(()=>{const e=document.querySelector("[data-toast]");return {text:e.textContent,popover:e.matches(":popover-open")}})()')
 assert 'Скопировано' in toast['text'] and toast['popover'],toast
 call('press','Escape');settle()
 call('click','.mobile-nav-book');settle();assert js('document.documentElement.dataset.bookingLayout')=='overlay'
 call('press','Escape');settle();report['navigation'].append(state)
# Shared hero carousel, gift composition and sun/portrait coordinate binding.
call('set','viewport','1440','1000');js('scrollTo({top:0,behavior:"instant"})');settle()
call('click','[data-hero-dot]:nth-child(2)');settle();assert js('document.querySelectorAll("[data-hero-dot]")[1].getAttribute("aria-current")')=='true'
call('focus','.hero-rail');call('press','ArrowRight');settle();assert js('document.querySelector(".hero-position").textContent.startsWith("3")')
assert js('new Set([...document.querySelectorAll(".gift-visual")].map(e=>Math.round(e.getBoundingClientRect().left))).size')==3
assert js('document.querySelector("#certificates").parentElement.classList.contains("gifts-layout")')
assert js('[...document.querySelectorAll(".gift-visual")].every(e=>Math.abs(e.offsetWidth-e.offsetHeight)<1)')
assert js('Math.abs(document.querySelector("#certificates").getBoundingClientRect().bottom-document.querySelector(".gift:last-child .gift-visual").getBoundingClientRect().bottom)<1')
assert js('getComputedStyle(document.querySelector(".cashback-surface")).backgroundColor')=='rgb(196, 47, 42)'
assert js('getComputedStyle(document.querySelector(".first-visit")).backgroundColor')=='rgb(82, 101, 140)'
for width in [320,390,768,1440]:
 call('set','viewport',str(width),'900');settle()
 sun=js('(()=>{const [r,p]=document.querySelectorAll(".cashback-art-stage"),a=r.getBoundingClientRect(),b=p.getBoundingClientRect();return Math.max(Math.abs(a.left-b.left),Math.abs(a.top-b.top),Math.abs(a.width-b.width),Math.abs(a.height-b.height))})()')
 assert sun<.1,(width,sun)
call('set','media','light','reduced-motion');settle();assert js('getComputedStyle(document.querySelector(".cashback-rays")).animationName')=='none'
call('set','media','light');assert js('window.__localErrors')==[],js('window.__localErrors')
report['status']='PASS: deck colours/gaps/wheel, profiles/interviews, docked header, round navigation, toast, carousel, gifts and anchored rays'
(ROOT/'tmp/planning/physical-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(report['status'],flush=True)
