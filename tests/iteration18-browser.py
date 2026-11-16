"""Local owner iteration 18/19: responsive themes and service photos."""
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
def settle():return js('(async()=>{await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));await Promise.allSettled(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity&&a.animationName!=="hero-photo-zoom").map(a=>a.finished));return true})()')
def center(s):js('document.querySelector('+json.dumps(s)+').scrollIntoView({behavior:"instant",block:"center"})');settle()
def save(name,result): (ROOT/f'tmp/planning/{name}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
MEASURE=r'''(()=>{
 const r=e=>e.getBoundingClientRect(),issues=[],range=document.createRange();
 for(const b of document.querySelectorAll('button,.btn')){
  const br=r(b),s=getComputedStyle(b);if(!br.width||!br.height||b.closest('dialog:not([open]),[inert],[hidden]'))continue;
  if(br.height<43.9)issues.push('hit:'+b.className);
  if(b.matches('.hero-edge,.hero-dot,.icon-btn,.certificate-object,.gift-visual')||b.querySelector('img')||!b.textContent.trim())continue;
  if(b.scrollWidth>b.clientWidth+1||parseFloat(s.paddingLeft)<12||parseFloat(s.paddingRight)<12)issues.push('label:'+b.textContent.trim());
  const nodes=document.createTreeWalker(b,NodeFilter.SHOW_TEXT);while(nodes.nextNode()){if(!nodes.currentNode.textContent.trim())continue;range.selectNodeContents(nodes.currentNode);if(range.getClientRects().length>1)issues.push('wrap:'+nodes.currentNode.textContent);}
 }
 const nav=document.querySelector('.header-nav'),logo=document.querySelector('.header-logo'),actions=document.querySelector('.header-actions'),headerVisible=!!r(logo).height;
 const linkRight=Math.max(...[...nav.children].filter(e=>r(e).width).map(e=>r(e).right));
 const actionLeft=Math.min(...[...actions.children].filter(e=>r(e).width).map(e=>r(e).left));
 if(headerVisible&&(linkRight>r(logo).left+1||actionLeft<r(logo).right-1))issues.push('header overlap');
 const cert=document.querySelector('.certificates'),gifts=[...document.querySelectorAll('.gift-visual')];
 return{width:innerWidth,theme:document.documentElement.dataset.theme,overflow:document.documentElement.scrollWidth>innerWidth+1,issues,headerVisible,hours:!!r(document.querySelector('.header-hours')).width,navItems:[...nav.querySelectorAll(':scope>a')].filter(e=>r(e).width).map(e=>e.textContent),giftSquares:gifts.every(e=>Math.abs(r(e).height-r(e).width)<1),certAlign:innerWidth>960?Math.abs(r(cert).bottom-r(gifts.at(-1)).bottom):null};
})()'''
if __name__=='__main__':
 call('open','http://127.0.0.1:4321/');call('set','media','light');settle()
 report={'geometry':[],'services':[],'externalSubmission':False}
 for theme in ['light','dark']:
  call('select','.footer [data-theme-select]',theme)
  for width in [320,360,390,540,600,650,651,768,800,960,1024,1080,1150,1280,1440,1920]:
   call('set','viewport',str(width),'1000');settle();row=js(MEASURE);report['geometry'].append(row)
   assert not row['overflow'] and not row['issues'] and row['giftSquares'],row
   assert row['certAlign'] is None or row['certAlign']<1,row
  print('PASS: responsive geometry / buttons / theme',theme,flush=True)
 save('iteration18-geometry',report)
 for width in [320,390,768,1440]:
  call('set','viewport',str(width),'1000');center('.sd-stack')
  for category in range(5):
   js(f'document.querySelectorAll("[data-sd-tab]")[{category}].click()');settle()
   count=js('document.querySelector(".sd-card[aria-hidden=false]").querySelectorAll(".sd-service").length')
   base=js('document.querySelector(".sd-stack").getBoundingClientRect().height')
   for index in range(count):
    js(f'document.querySelector(".sd-card[aria-hidden=false]").querySelectorAll(".sd-service")[{index}].open=true')
    result=js('''(async()=>{const panel=document.querySelector('.sd-card[aria-hidden=false]'),row=panel.querySelector('details[open]');for(let i=0;i<100;i++){await new Promise(r=>setTimeout(r,30));const img=panel.querySelector('[data-photo-current=true]');if(img?.getAttribute('src')===row.dataset.photoSrc&&img.complete&&img.naturalWidth)return{src:img.getAttribute('src'),id:row.dataset.serviceId,height:document.querySelector('.sd-stack').getBoundingClientRect().height};}return{error:'photo not updated',id:row.dataset.serviceId}})()''')
    assert 'error' not in result,result
    assert abs(result['height']-base)<.1,(width,result,base)
   report['services'].append({'width':width,'category':category,'positions':count,'height':base})
  print('PASS: service photos and fixed heights',width,flush=True)
 save('iteration18-geometry',report)
 print('PASS: 32 theme/viewport combinations and 116 service photo selections.',flush=True)
