"""Decode every poster and verify shared composition after responsive asset delivery."""
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
call('open','http://127.0.0.1:4321/');call('set','media','light','no-preference')
images=js('(async()=>{const images=[...document.querySelectorAll(".of-photo img")];for(const image of images)image.loading="eager";await Promise.all(images.map(i=>i.decode()));return images.map(i=>({url:i.currentSrc,width:i.naturalWidth,height:i.naturalHeight}))})()')
assert len(images)==10 and all(i['width']>0 and '-640.webp?v=' in i['url'] for i in images)
geometry=[]
for width in [320,360,390,540,600,650,651,768,800,960,1024,1280,1440,1920]:
    call('set','viewport',str(width),'1000');settle()
    m=js('''(()=>{const r=e=>e.getBoundingClientRect(),cards=[...document.querySelectorAll('.of-card')];return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,heights:cards.map(c=>r(c).height),bottoms:cards.map(c=>r(c).bottom-r(c.querySelector('.of-action')).bottom),border:getComputedStyle(document.querySelector('.of-photo')).borderBottomWidth,buttons:cards.every(c=>{const b=c.querySelector('.of-action');return b.scrollWidth<=b.clientWidth+1&&getComputedStyle(b).whiteSpace==='nowrap'&&r(b).height>=44})}})()''')
    assert not m['overflow'] and m['border']=='0px' and m['buttons'],m
    assert max(m['heights'])-min(m['heights'])<1 and max(m['bottoms'])-min(m['bottoms'])<1,m
    geometry.append(m)
for width,name,selector in [(1440,'desktop-offers','.of-layout'),(390,'mobile-offers','.of-layout'),(651,'narrow-hero','.hero'),(1440,'desktop-visit','#first-visit'),(390,'mobile-visit','#first-visit')]:
    call('set','viewport',str(width),'1000');settle()
    js('document.querySelector('+json.dumps(selector)+').scrollIntoView({behavior:"instant",block:"start"});scrollBy({top:-28,behavior:"instant"})');settle()
    call('screenshot',str(ROOT/'docs/previews'/('round14-'+name+'.png')))
call('set','viewport','1440','1000');settle()
js('(()=>{const c=document.querySelectorAll(".about-card")[3];scrollTo({top:c.offsetTop-parseFloat(getComputedStyle(c).top)+50,behavior:"instant"})})()');settle()
call('screenshot',str(ROOT/'docs/previews/round14-stacked-about.png'))
js('scrollTo({top:0,behavior:"instant"})');settle();call('click','.header-phone');settle()
call('screenshot',str(ROOT/'docs/previews/round14-header-contacts.png'));call('press','Escape')
(ROOT/'tmp/planning/final-posters-qa.json').write_text(json.dumps({'images':images,'geometry':geometry},indent=2),encoding='utf-8')
print('PASS: ten decoded posters; 14 widths without overflow, aligned equal-height cards and full-width one-line actions; no photo divider. Seven screenshots saved.',flush=True)
