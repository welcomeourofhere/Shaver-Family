"""Final owner refinements: equal indicator padding, fixed certificate hits, routes."""
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
def settle():js('(async()=>{await document.fonts.ready;await new Promise(r=>setTimeout(r,650));return true})()')
def center(selector):js('document.querySelector('+json.dumps(selector)+').scrollIntoView({behavior:"instant",block:"center"})');settle()
report={'indicator':[],'bookings':[],'screenshots':[],'externalSubmission':False}
call('open','http://127.0.0.1:4321/');call('set','media','light')
for width in [320,390,800,1440]:
    call('set','viewport',str(width),'1000');settle()
    m=js('''(()=>{const p=document.querySelector('.hero-news-panel'),a=document.querySelector('.hero-news-details[data-news-active=true] .hero-news-link'),dot=document.querySelector('.hero-dot'),d=dot.getBoundingClientRect(),g=parseFloat(getComputedStyle(dot,'::after').height),r=p.getBoundingClientRect();return{width:innerWidth,top:d.top+(d.height-g)/2-a.getBoundingClientRect().bottom,bottom:r.bottom-(d.top+(d.height+g)/2),hit:d.height}})()''')
    assert abs(m['top']-m['bottom'])<1 and m['top']<=20 and m['hit']>=44,m
    report['indicator'].append(m)
call('set','viewport','1440','1000');center('.certificate-scene');call('mouse','move','0','0');settle()
js('''document.querySelector('[data-certificate-value="front"]').addEventListener('pointerdown',()=>{window.__certificatePress=[];const end=performance.now()+600;(function record(){const c=document.querySelector('[data-certificate-value="front"]'),r=c.getBoundingClientRect();window.__certificatePress.push([r.left,r.top,r.width,r.height,getComputedStyle(c).scale]);if(performance.now()<end)requestAnimationFrame(record)})()},{once:true})''')
call('click','[data-certificate-value="front"]');settle()
frames=js('window.__certificatePress');assert frames and len(frames)>5
for key in range(4):assert max(row[key] for row in frames)-min(row[key] for row in frames)<.01,frames
assert all(row[4]=='none' for row in frames),frames
report['certificatePressFrames']=len(frames)
for index,host in [(1,'b2266404'),(2,'b2440449')]:
    selector=f'.visit-actions button:nth-child({index})';center(selector);call('click',selector);settle()
    state=js('''(()=>{const d=document.querySelector('[data-booking-drawer]');return{open:d.open,url:d.dataset.bookingUrl}})()''')
    assert state['open'] and host+'.yclients.ru' in state['url'],state
    report['bookings'].append(state);call('press','Escape');settle()
call('open','http://127.0.0.1:4321/');call('mouse','move','0','0')
for width in [1440,390]:
    call('set','viewport',str(width),'1100' if width==1440 else '1000');settle()
    for name,selector in [('hero',None),('fair','.visit-ticket'),('gifts','.gifts-layout')]:
        if selector:center(selector)
        else:js('scrollTo({top:0,behavior:"instant"})');settle()
        path=ROOT/'docs/previews'/f'round18-{name}-{width}.png';call('screenshot',str(path));report['screenshots'].append(str(path.relative_to(ROOT)))
    for label,selector in [('fair','.visit-art img'),('gifts','.certificate-scene')]:
        assert not js('document.documentElement.scrollWidth>innerWidth+1')
(ROOT/'tmp/planning/iteration17-controls-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
call('set','viewport','1440','1000');call('open','http://127.0.0.1:4321/#top')
print('PASS: equal compact indicator padding at four widths; native certificate press leaves hit geometry unchanged; both personal booking routes; six final screenshots. No booking submitted.',flush=True)
