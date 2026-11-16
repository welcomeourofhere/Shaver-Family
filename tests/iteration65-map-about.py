"""Real wheel/resize verification of map startup and the complete About stack."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--origin',default='http://127.0.0.1:4321/')
parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium')
args=parser.parse_args()
OUT=ROOT/'tmp/planning/iteration65/map';OUT.mkdir(parents=True,exist_ok=True)
rows=[];errors=[]
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 for motion in ['no-preference','reduce']:
  for theme in ['light','dark']:
   context=browser.new_context(viewport={'width':1440,'height':900},reduced_motion=motion,color_scheme=theme)
   # Provider bootstrap is tested separately; About does not depend on its network.
   context.route('https://yandex.ru/map-widget/**',lambda r:r.abort())
   page=context.new_page();page.on('pageerror',lambda e:errors.append(e.stack))
   page.goto(args.origin,wait_until='domcontentloaded');page.wait_for_function('document.readyState==="complete"&&document.fonts.status==="loaded"');page.wait_for_timeout(350)
   for width,height,text_scale in [(961,720,1),(1024,900,1),(1280,720,1),(1440,900,1),(1440,1080,1),(1920,1080,1),(1440,900,2)]:
    page.set_viewport_size({'width':width,'height':height})
    page.evaluate('''scale=>{for(const [e,value]of window.__mapTextZoom||[])e.style.fontSize=value;window.__mapTextZoom=[];if(scale===1)return;const nodes=[...document.body.querySelectorAll('*')].filter(e=>!e.closest('script,style,svg')&&[...e.childNodes].some(n=>n.nodeType===Node.TEXT_NODE&&n.textContent.trim()));const values=nodes.map(e=>[e,e.style.fontSize,parseFloat(getComputedStyle(e).fontSize)]);window.__mapTextZoom=values.map(([e,value])=>[e,value]);for(const [e,,size]of values)e.style.fontSize=`${size*scale}px`;}''',text_scale)
    page.wait_for_timeout(250)
    initial=page.locator('#about').evaluate('e=>({mode:e.dataset.stackMode,headingTop:parseFloat(getComputedStyle(e).getPropertyValue("--about-heading-top")),headingHeight:document.querySelector("#about-title").getBoundingClientRect().height,layers:[...e.querySelectorAll("[data-about-layer]")].map(x=>{const r=x.getBoundingClientRect();return{top:r.top+scrollY,height:r.height,sticky:parseFloat(getComputedStyle(x).top)}})})')
    poses=[]
    for layer in initial['layers']:
     y=layer['top']-layer['sticky']+10 if initial['mode']=='stack'else layer['top']-100
     page.evaluate('y=>scrollTo({top:y,behavior:"instant"})',y);page.wait_for_timeout(80)
     page.mouse.wheel(0,80);page.wait_for_timeout(90)
     sample=page.evaluate('''async()=>{const poses=[];for(let i=0;i<5;i++){await new Promise(requestAnimationFrame);const h=document.querySelector('#about-title').getBoundingClientRect();poses.push({y:scrollY,top:h.top,bottom:h.bottom});}return poses}''')
     poses.append(sample)
    if initial['mode']=='stack':
     assert motion=='no-preference'
     for sample in poses:
      assert all(abs(s['top']-initial['headingTop'])<1 for s in sample),(args.engine,width,height,text_scale,initial,sample)
     assert max(s['top']for sample in poses for s in sample)-min(s['top']for sample in poses for s in sample)<1
    else:
     assert page.locator('#about-title').evaluate('e=>getComputedStyle(e).position')!='sticky'
    assert page.locator('#about').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
    rows.append({'engine':args.engine,'motion':motion,'theme':theme,'width':width,'height':height,'textScale':text_scale,'mode':initial['mode'],'poses':poses})
   context.close()
 browser.close()
(OUT/f'about-{args.engine}.json').write_text(json.dumps({'origin':args.origin,'cases':rows,'errors':errors,'physicalDevice':False,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
assert not errors,errors
print('PASS',args.engine,len(rows),'About complete-card cycles, wheel intermediate frames, both themes/motion modes, 200% text')
