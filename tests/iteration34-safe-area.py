"""Exercise shared safe-area tokens with simulated inset values in Chromium."""
from iteration33_browser_helpers import *

call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz34-text','--json']
report={'simulatedInsets':True,'hardware':False,'rows':[],'externalSubmission':False}
def rect(selector):
 return js('(()=>{const r=document.querySelector('+json.dumps(selector)+').getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}})()')
def safe_dialog(selector,width,height,top,right,bottom,left):
 bounds=rect(selector)
 assert bounds['top']>=top+7.9 and bounds['bottom']<=height-bottom-7.9,bounds
 assert bounds['left']>=max(left,7.9) and bounds['right']<=width-max(right,7.9),bounds
 return bounds

try:
 for width,height,top,right,bottom,left in [(390,844,47,0,34,0),(320,568,47,0,34,0),(844,390,0,0,21,47)]:
  call('open','http://127.0.0.1:4321/?qa=34-safe');call('set','viewport',str(width),str(height));call('set','media','light','reduced-motion');settle()
  js('for(const [edge,value] of Object.entries('+json.dumps(dict(top=top,right=right,bottom=bottom,left=left))+'))document.documentElement.style.setProperty("--safe-"+edge,value+"px");dispatchEvent(new Event("resize"));scrollTo({top:0,behavior:"instant"})')
  settle()
  dock=rect('.mobile-nav');brand=rect('.hero-brand');lead=rect('.hero-heading')
  assert dock['left']>=left+11.9 and dock['right']<=width-right-11.9 and dock['bottom']<=height-bottom-11.9,dock
  assert brand['top']>=top+15.9 and brand['left']>=left,brand
  assert lead['left']>=left and lead['right']<=width-right,lead
  case={'width':width,'height':height,'insets':dict(top=top,right=right,bottom=bottom,left=left),'dock':dock,'dialogs':{}}
  call('click','[data-open-menu]');settle();case['dialogs']['menu']=safe_dialog('#mobile-menu',width,height,top,right,bottom,left);call('press','Escape');settle()
  center('.sd-stack');call('click','[data-dock-secondary]');settle();case['dialogs']['categories']=safe_dialog('#service-categories',width,height,top,right,bottom,left);call('press','Escape');settle()
  center('.team-grid');call('click','.team-card:first-child .team-discover');settle();case['dialogs']['profile']=safe_dialog('.team-dialog[open]',width,height,top,right,bottom,left);call('press','Escape');settle()
  call('click','[data-dock-primary]');settle();close=rect('.booking-close');assert close['top']>=top and close['left']>=left,close;call('press','Escape');settle()
  report['rows'].append(case)
  print('PASS simulated safe-area',width,height,flush=True)
 report['status']='passed'
finally:
 js('for(const edge of ["top","right","bottom","left"])document.documentElement.style.removeProperty("--safe-"+edge);dispatchEvent(new Event("resize"))')
 save('iteration34-safe-area',report)
