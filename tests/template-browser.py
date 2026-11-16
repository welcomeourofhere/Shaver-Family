"""Actual Chrome geometry, fixed deck height and keyboard checks via agent-browser."""
import json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.environ['AGENT_BROWSER_SOCKET_DIR']=str(ROOT/'.local/browser-qa')
CLI=['node','node_modules/agent-browser/bin/agent-browser.js','--session',os.environ.get('SOYUZ_QA_SESSION','soyuzqa'),'--json']
OUT=ROOT/'tmp/planning';OUT.mkdir(parents=True,exist_ok=True)
def call(*args,script=None):
    result=subprocess.run(CLI+list(args),input=script,text=True,encoding='utf-8',capture_output=True,timeout=45)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    response=json.loads(result.stdout);assert response['success'],response
    return response['data']
def evaluate(script):return call('eval','--stdin',script=script)['result']
def settle():evaluate('(async()=>{await document.fonts.ready;await Promise.allSettled(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity&&a.animationName!=="hero-photo-zoom").map(a=>a.finished));return true})()')
MEASURE=r'''(()=>{
 const issues=[];
 if(document.documentElement.scrollWidth>innerWidth+1)issues.push('page overflow');
 for(const el of document.querySelectorAll('button,.btn')){
  const rect=el.getBoundingClientRect(),style=getComputedStyle(el);
  if(!rect.width||!rect.height||el.closest('[hidden],dialog:not([open]),[inert]'))continue;
  if(rect.height<43.9)issues.push('hit height '+el.className);
  if(el.matches('.icon-btn,.burger,.certificate-object,.gift-visual,.sd-arrow,.hero-arrow,.hero-dot,.hero-rotation,.hero-news-toggle,.hero-edge')||el.querySelector('img'))continue;
  if(parseFloat(style.paddingLeft)<12||parseFloat(style.paddingRight)<12)issues.push('padding '+el.className);
  if(el.scrollWidth>el.clientWidth+1)issues.push('button overflow '+el.textContent.trim());
  const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
  while(w.nextNode()){if(!w.currentNode.textContent.trim())continue;const r=document.createRange();r.selectNodeContents(w.currentNode);if(r.getClientRects().length>1)issues.push('wrapped button '+w.currentNode.textContent)}
 }
 return {width:innerWidth,issues};
})()'''
call('open','http://127.0.0.1:4321/')
geometry=[];heights=[]
for width in [320,360,390,540,768,800,960,1024,1280,1440,1920]:
    call('set','viewport',str(width),'900');settle()
    geometry.append(evaluate(MEASURE))
    if width in [390,1440]:call('screenshot',str(OUT/f'reference-template-{width}.png'))
print(json.dumps(geometry,ensure_ascii=False),flush=True)
assert not any(item['issues'] for item in geometry)
for width in [320,390,768,1440]:
    call('set','viewport',str(width),'900')
    for category in range(5):
        # Deliberate rapid DOM activations also exercise cancellation of a previous deal.
        evaluate(f'document.querySelector("[data-sd-tab=\\"{category}\\"]").click()')
        settle()
        before=evaluate('document.querySelector(".sd-card[aria-hidden=false]").getBoundingClientRect().height')
        next_top=evaluate('document.querySelector("#offers").getBoundingClientRect().top + scrollY')
        count=evaluate('document.querySelector(".sd-card[aria-hidden=false]").querySelectorAll(".sd-summary").length')
        for index in range(count):
            evaluate(f'document.querySelector(".sd-card[aria-hidden=false]").querySelectorAll(".sd-summary")[{index}].click()')
            after=evaluate('document.querySelector(".sd-card[aria-hidden=false]").getBoundingClientRect().height')
            assert abs(before-after)<.1,(width,category,index,before,after)
            assert abs(next_top-evaluate('document.querySelector("#offers").getBoundingClientRect().top + scrollY'))<1,(width,category,index,'next section moved')
        heights.append({'width':width,'category':category,'height':before,'accordions':count})
    print('fixed heights PASS',width,flush=True)
evaluate('for(const n of [0,3,1,4,2])document.querySelectorAll("[data-sd-tab]")[n].click()')
settle()
assert evaluate('document.querySelectorAll(".sd-card[aria-hidden=false]").length===1 && document.querySelector("[data-sd-tab=\\"2\\"]").getAttribute("aria-selected")==="true"')
call('set','viewport','390','900')
call('click','[data-open-menu]');assert evaluate('document.querySelector("#mobile-menu").open')
call('press','Escape');settle();assert evaluate('document.activeElement.matches("[data-open-menu]")')
call('focus','.certificate-back');call('press','Enter');settle()
assert evaluate('document.querySelector(".certificate-back").getAttribute("aria-pressed")==="true"')
call('focus','[data-gift][data-has-photo="true"]');call('press','Enter')
assert evaluate('document.querySelector("[data-gift][data-has-photo=\\"true\\"]").getAttribute("aria-pressed")==="true"')
call('click','.mobile-nav-book');assert evaluate('document.querySelector("[data-booking-drawer]").open')
call('press','Escape');settle()
report={'geometry':geometry,'fixedHeights':heights,'interactions':'menu, rapid dealing, gift tap, certificate keyboard, contact dialog passed','externalSubmission':False}
(OUT/'reference-template-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: 11 widths, 20 category/viewport combinations, every accordion, rapid switching and keyboard controls.',flush=True)
