"""One geometry state keeps both visible bounds fixed, including interrupted jumps."""
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
call('open','http://127.0.0.1:4321/');call('set','media','light','no-preference')
js('(async()=>{await document.fonts.ready;document.querySelector(".hero-rail").focus();document.querySelectorAll("[data-hero-dot]")[0].click();return true})()')
report=[]
for width in [320,390,1440]:
    call('set','viewport',str(width),'1000')
    for target in [1,9,0]:
        trace=js('''(async()=>{
          const dots=[...document.querySelectorAll('[data-hero-dot]')],out=[],started=performance.now();
          const sample=()=>{const glyphs=dots.map(e=>{const r=e.getBoundingClientRect();return {left:r.left,width:r.width}}),n=document.querySelector('.hero-nav').getBoundingClientRect();return {glyphs,left:glyphs[0].left,right:glyphs.at(-1).left+glyphs.at(-1).width,panel:n.width,gap:glyphs[1].left-glyphs[0].left-glyphs[0].width}};
          out.push(sample());dots[TARGET].click();
          await new Promise(resolve=>{function frame(){out.push(sample());if(performance.now()-started<650)requestAnimationFrame(frame);else resolve()}requestAnimationFrame(frame)});
          return out;
        })()'''.replace('TARGET',str(target)))
        spread=lambda key:max(f[key] for f in trace)-min(f[key] for f in trace)
        metrics={'viewport':width,'target':target,'frames':len(trace),'leftDrift':spread('left'),'rightDrift':spread('right'),'panelDrift':spread('panel')}
        assert all(metrics[k]<.05 for k in ['leftDrift','rightDrift','panelDrift']),metrics
        assert all(abs(f['gap']-6)<.05 for f in trace),metrics
        assert any(6.1<f['glyphs'][target]['width']<19.9 for f in trace),metrics
        report.append({**metrics,'trace':trace})
    geometry=js('''(()=>{const n=document.querySelector('.hero-nav'),r=n.getBoundingClientRect(),s=getComputedStyle(n,'::before'),h=document.querySelector('.hero-scene').getBoundingClientRect(),dots=[...n.querySelectorAll('button')].map(x=>x.getBoundingClientRect());return {width:r.width,height:r.height-2*parseFloat(s.top),leftPad:dots[0].left-r.left,rightPad:r.right-dots.at(-1).right,topPad:(r.height-6)/2-parseFloat(s.top),center:r.left+r.width/2-h.left-h.width/2,bottom:h.bottom-r.bottom+parseFloat(s.bottom)}})()''')
    assert abs(geometry['width']-144)<.05 and abs(geometry['height']-22)<.05,geometry
    assert all(abs(geometry[k]-8)<.05 for k in ['leftPad','rightPad','topPad']),geometry
    assert abs(geometry['center'])<.05 and abs(geometry['bottom']-12)<.05,geometry
    print('PASS: constant visible length and both outer edges; 6px gaps, equal 8px padding, bottom12px and centered:',width,flush=True)
# Press has no translate/scale; pointer padding and keyboard still choose a slide.
js('window.__press=null;document.querySelectorAll("[data-hero-dot]")[1].addEventListener("mousedown",e=>{const s=getComputedStyle(e.currentTarget);window.__press={scale:s.scale,translate:s.translate,transform:s.transform}},{once:true})')
call('click','[data-hero-dot]:nth-child(2)')
state=js('window.__press');assert state=={'scale':'none','translate':'none','transform':'none'},state
call('focus','[data-hero-dot]:nth-child(3)');call('press','Enter')
call('wait','--fn','document.querySelectorAll("[data-hero-dot]")[2].getAttribute("aria-current")==="true"')
print('PASS: no press scaling/shift; actual click and keyboard selection work.',flush=True)
(ROOT/'tmp/planning/hero-bounds-qa.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
