"""Explore all main sections through the installed native agent-browser CLI."""
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/iteration61/dogfood';(OUT/'screenshots').mkdir(parents=True,exist_ok=True)
CLI=ROOT/'node_modules/agent-browser/bin/agent-browser-win32-x64.exe'
ENV={**os.environ,'AGENT_BROWSER_SOCKET_DIR':str(ROOT/'.local/browser-qa61')}
def call(*args,source=None):
    run=subprocess.run([str(CLI),'--session','soyuz61-exploration','--json',*map(str,args)],cwd=ROOT,env=ENV,input=source,capture_output=True,text=True,encoding='utf-8',timeout=25)
    value=json.loads(run.stdout)
    if run.returncode or not value['success']:raise RuntimeError(value.get('error')or run.stderr)
    return value.get('data',{})
def evaluate(source):return call('eval','--stdin',source=source).get('result')
scan=r'''(()=>{
 const bad=[],range=document.createRange();
 for(const e of document.querySelectorAll('button,.btn')){
  const r=e.getBoundingClientRect(),s=getComputedStyle(e);
  if(!r.width||!r.height||r.bottom<0||r.top>innerHeight||s.visibility==='hidden'||e.closest('[hidden],[inert],[aria-hidden="true"],dialog:not([open])'))continue;
  const name=e.getAttribute('aria-label')||e.textContent.trim();
  if(r.height<43.8)bad.push({type:'hit-height',name,height:r.height});
  if(e.matches('.hero-edge,.hero-dot,.icon-btn,.info-trigger,.certificate-object,.gift-visual,.dock-menu')||e.querySelector('img')||!e.textContent.trim())continue;
  if(e.scrollWidth>e.clientWidth+1)bad.push({type:'label-overflow',name,client:e.clientWidth,scroll:e.scrollWidth});
  const walk=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);
  while(walk.nextNode()){
   const node=walk.currentNode;if(!node.textContent.trim()||!node.parentElement.getClientRects().length||node.parentElement.closest('[aria-hidden="true"]'))continue;
   range.selectNodeContents(node);const rects=[...range.getClientRects()].filter(r=>r.width>0&&r.height>0);
   if(rects.length>1)bad.push({type:'label-wrap',name,text:node.textContent});
  }
 }
 return{overflow:document.documentElement.scrollWidth>innerWidth+1,bad,scroll:scrollY,dock:{section:document.querySelector('[data-mobile-nav]')?.dataset.section,height:document.querySelector('[data-mobile-nav]')?.getBoundingClientRect().height}};
})()'''
results=[]
try:
 for width,height in [(280,600),(320,480),(390,844),(844,390),(768,600),(960,540),(1024,600),(1440,800),(1920,1080)]:
  call('set','viewport',width,height);call('open','http://127.0.0.1:4321/')
  evaluate('(async()=>{await document.fonts.ready;return true})()');time.sleep(.6)
  ids=evaluate("[...document.querySelectorAll('main>section')].map(e=>e.id)")
  for theme in ['light','dark']:
   evaluate("(()=>{const e=document.querySelector('[data-theme-select]');e.value="+json.dumps(theme)+";e.dispatchEvent(new Event('change',{bubbles:true}));return true})()")
   for section in ids:
    evaluate("(()=>{if("+json.dumps(section)+"==='top')scrollTo({top:0,behavior:'instant'});else{document.getElementById("+json.dumps(section)+").scrollIntoView({block:'start',behavior:'instant'});scrollBy(0,-24);}return true})()")
    time.sleep(.45);state=evaluate(scan);state.update(width=width,height=height,theme=theme,section=section)
    if width in [390,768,1024,1440] or state['bad'] or state['overflow']:
     path=OUT/'screenshots'/f'{width}x{height}-{theme}-{section}.png';call('screenshot',path);state['screenshot']=str(path.relative_to(ROOT))
    results.append(state)
   print(width,height,theme,'sections',len(ids),'findings',sum(bool(row['bad']or row['overflow'])for row in results if row['width']==width and row['theme']==theme),flush=True)
finally:
 (OUT/'survey.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
