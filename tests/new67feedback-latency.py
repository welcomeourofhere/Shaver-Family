"""Accepted input to play()/playing timing; native browser media, not hardware audible latency."""
import argparse,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321/');parser.add_argument('--engine',choices=['chromium','webkit'],default='chromium');parser.add_argument('--label',required=True);parser.add_argument('--baseline',action='store_true');args=parser.parse_args();assert re.fullmatch(r'[\w-]+',args.label)
OUT=ROOT/'tmp/planning/iteration67/feedback'/args.label;OUT.mkdir(parents=True,exist_ok=False);host=urlsplit(args.origin).netloc
config=json.loads((ROOT/'src/config/feedback.json').read_text(encoding='utf-8'))
def hashes():return{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()for f in ['src/scripts/feedback.ts','src/config/feedback.json','scripts/prepare-feedback.py','content/feedback-sources.json',*['public'+s['url']for s in config['tones'].values()]]}
SPY="""(()=>{if(top!==window)return;localStorage.setItem('soyuz.analytics.v1','denied');window.__feedback=[];window.__feedbackPlayers=[];window.__preparedAudio=[];const load=HTMLMediaElement.prototype.load;HTMLMediaElement.prototype.load=function(){if(this.src.includes('/audio/'))__preparedAudio.push(this);return load.call(this)};window.__accepted=[];window.__haptics=[];window.__frames=0;const frame=()=>{__frames++;requestAnimationFrame(frame)};requestAnimationFrame(frame);const play=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){if(this.src.includes('/audio/')){const accepted=__accepted.at(-1),row={src:new URL(this.src).pathname,at:performance.now(),readyState:this.readyState,volume:this.volume,accepted:accepted?.at,frame:__frames,acceptedFrame:accepted?.frame};__feedback.push(row);__feedbackPlayers.push(this);row.events=[];for(const event of ['waiting','ended','pause','error','loadeddata','canplay'])this.addEventListener(event,()=>row.events.push({type:event,at:performance.now(),time:this.currentTime,paused:this.paused,ended:this.ended}),{once:true});this.addEventListener('playing',()=>row.playingAt=performance.now(),{once:true});const promise=play.call(this);row.playReturnedAt=performance.now();promise?.then(()=>row.fulfilledAt=performance.now(),e=>row.error=e.name);return promise}return play.call(this)};Object.defineProperty(navigator,'vibrate',{configurable:true,value:p=>{__haptics.push({pattern:p,at:performance.now()});return true}})})()"""
start=hashes();rows=[];errors=[]
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome','args':['--mute-audio']}if args.engine=='chromium'else{}))
 for tone in config['tones']:
  c=browser.new_context(viewport={'width':800,'height':900});c.route('**/*',lambda r:r.continue_()if urlsplit(r.request.url).netloc==host else r.abort());c.add_init_script(SPY);page=c.new_page();page.on('pageerror',lambda e:errors.append(e.stack or str(e)));page.goto(args.origin,wait_until='domcontentloaded');page.wait_for_timeout(450);page.wait_for_function('__preparedAudio.length===4&&__preparedAudio.every(a=>a.readyState>=2)',timeout=5000)
  page.evaluate("""tone=>{const b=document.createElement('button');b.id='feedback-latency-probe';b.textContent='Проверка действия';b.style='position:fixed;top:100px;left:50px;z-index:9999;min-height:48px;padding:12px;background:#ffcc29';b.dataset.uiKind=tone==='select'?'selection':tone==='open'||tone==='close'?'disclosure':'filled';if(tone==='open'||tone==='close')b.setAttribute('aria-expanded',String(tone==='close'));b.addEventListener('click',e=>{if(b.hasAttribute('aria-expanded'))b.setAttribute('aria-expanded',String(b.getAttribute('aria-expanded')!=='true'));__accepted.push({at:performance.now(),frame:__frames,type:e.type,trusted:e.isTrusted})});document.body.append(b)}""",tone)
  assert page.evaluate('__feedback.length')==0,'Preloading must never unlock by playing an inaudible cue'
  for repeat in range(3):
   # Keep the intended disclosure role stable for each repetition.
   if tone in ['open','close']:page.locator('#feedback-latency-probe').evaluate('(e,t)=>e.setAttribute("aria-expanded",String(t==="close"))',tone)
   q=page.locator('#feedback-latency-probe').bounding_box();page.mouse.move(q['x']+q['width']/2,q['y']+q['height']/2);page.mouse.down();page.wait_for_timeout(20);page.mouse.up();page.wait_for_function('window.__feedback.length>'+str(repeat));page.wait_for_timeout(280)
   (OUT/f'{args.engine}-latest.json').write_text(json.dumps({'tone':tone,'repeat':repeat,'values':page.evaluate('__feedback'),'pageErrors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
   try:page.wait_for_function('i=>!!(__feedback[i]?.playingAt&&__feedback[i]?.fulfilledAt)',arg=repeat,timeout=1500)
   finally:(OUT/f'{args.engine}-latest.json').write_text(json.dumps({'tone':tone,'repeat':repeat,'values':page.evaluate('__feedback'),'pageErrors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
  values=page.evaluate('__feedback.map((r,i)=>({...r,stateAfter:{readyState:__feedbackPlayers[i].readyState,paused:__feedbackPlayers[i].paused,ended:__feedbackPlayers[i].ended,currentTime:__feedbackPlayers[i].currentTime,duration:__feedbackPlayers[i].duration,error:__feedbackPlayers[i].error?.code}}))');
  (OUT/f'{args.engine}-latest.json').write_text(json.dumps({'tone':tone,'values':values,'pageErrors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
  assert len(values)==3 and all(v['src']==config['tones'][tone]['url']and v['volume']==config['volume']for v in values),values
  assert all('playingAt'in v and'fulfilledAt'in v for v in values),'Native media never confirmed playback'
  if not args.baseline:assert values[0]['readyState']>=2,'The first accepted cue must already have playable data in the normal local delivery probe'
  for v in values:
   v['acceptedToPlayMs']=v['at']-v['accepted'];v['acceptedToPlayingMs']=v.get('playingAt',v['at'])-v['accepted'];v['framesToPlay']=v['frame']-v['acceptedFrame'];assert v['framesToPlay']==0 and 0<=v['acceptedToPlayMs']<16 and'error'not in v,v
  assert page.evaluate('__haptics')==[]
  rows.append({'tone':tone,'samples':values,'audioResources':page.evaluate("performance.getEntriesByType('resource').filter(r=>r.name.includes('/audio/')).map(r=>({url:new URL(r.name).pathname,start:r.startTime,duration:r.duration,bytes:r.transferSize}))")});c.close()
 browser.close()
assert errors==[],errors
end=hashes();assert start==end,'Feedback sources changed during timing probe'
(OUT/f'{args.engine}.json').write_text(json.dumps({'engine':args.engine,'baseline':args.baseline,'sourceStart':start,'sourceEnd':end,'rows':rows,'pageErrors':errors,'hardwareAudibleLatency':False,'mutedBrowserOutput':args.engine=='chromium'},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'PASS {args.engine}:12 native media timings; accepted→play same frame, no mouse haptic; hardware latency not measured')
