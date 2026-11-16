"""Causal A/B of the map approach on one frozen build, real Yandex and CPU x4.

The baseline restores only the three fixes at delivery time. No artifact is edited.
Paint clip bounds are diagnostic invalidation bounds, not raster bytes or field FPS.
"""
import argparse
import importlib.util
import json
import re
import statistics
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reg',ROOT/'tests/device-regression.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,default=ROOT/'.local/map65-dist');parser.add_argument('--runs',type=int,default=3);args=parser.parse_args()
folder=args.folder.resolve();before=reg.digest(folder);server,url=reg.serve(folder);OUT=ROOT/'tmp/planning/iteration65/map';OUT.mkdir(parents=True,exist_ok=True);rows=[]
owner=[f for f in(folder/'_astro').glob('*.js')if'.classList.contains("is-floating")'in f.read_text(encoding='utf-8')];assert len(owner)==1
INIT='''window.mapLab={frames:[],long:[],scrolls:[],writes:0,record:false,visibleAt:null,srcAssignedAt:null,visibility:[]};new PerformanceObserver(l=>mapLab.long.push(...l.getEntries().map(e=>({t:e.startTime,d:e.duration})))).observe({type:'longtask',buffered:true});addEventListener('scroll',()=>{if(mapLab.record)mapLab.scrolls.push(performance.now())},{passive:true});addEventListener('visibilitychange',()=>mapLab.visibility.push({t:performance.now(),hidden:document.hidden}));addEventListener('DOMContentLoaded',()=>{new MutationObserver(ms=>{if(mapLab.record)mapLab.writes+=ms.length}).observe(document.querySelector('.site-header'),{attributes:true,attributeFilter:['class']});const host=document.querySelector('.contact-map'),frame=host.querySelector('iframe');new IntersectionObserver(es=>{if(es[0].isIntersecting&&!mapLab.visibleAt)mapLab.visibleAt=performance.now()}).observe(host);new MutationObserver(()=>{if(frame.hasAttribute('src')&&!mapLab.srcAssignedAt)mapLab.srcAssignedAt=performance.now()}).observe(frame,{attributes:true,attributeFilter:['src']})});let prev;function frame(t){if(mapLab.record&&prev)mapLab.frames.push(t-prev);prev=t;requestAnimationFrame(frame)}requestAnimationFrame(frame);'''
INIT=INIT.replace('srcAssignedAt:null,','srcAssignedAt:null,loadedAt:null,').replace("new MutationObserver(()=>{if(frame.hasAttribute('src')", "host.addEventListener('load',e=>{if(e.target===frame&&frame.hasAttribute('src'))mapLab.loadedAt=performance.now()},true);new MutationObserver(()=>{if(frame.hasAttribute('src')")
INIT=INIT.replace('if(mapLab.record&&prev)mapLab.frames.push(t-prev);','if(mapLab.record&&prev>=mapLab.start)mapLab.frames.push({t,gap:t-prev});')
INIT='(()=>{if(window.top!==window)return;'+INIT+'})();'
try:
 with sync_playwright()as p:
  for run in range(args.runs):
   for label in (['baseline','candidate']if run%2==0 else['candidate','baseline']):
    browser=p.chromium.launch(channel='chrome')
    context=browser.new_context(viewport={'width':1440,'height':900});context.add_init_script(INIT);patched=[]
    if label=='baseline':
     def old_header(route):
      response=route.fetch();body=response.text();match=re.search(r'const ([\w$]+)=([\w$]+)\.classList\.contains\("is-floating"\);',body)
      if match:
       flag,header=match.groups();body=body[:match.start()]+body[match.end():];old=body;body=body.replace(f'&&{flag}?{header}.classList.remove("is-floating")',f'?{header}.classList.remove("is-floating")').replace(f'&&!{flag}&&{header}.classList.add("is-floating")',f'&&{header}.classList.add("is-floating")');assert old!=body;patched.append(True)
      route.fulfill(response=response,body=body)
     context.route(url+'_astro/'+owner[0].name,old_header)
    page=context.new_page();requests=[];errors=[];page.on('pageerror',lambda e:errors.append(e.stack));page.on('request',lambda r:requests.append(page.evaluate('performance.now()'))if r.is_navigation_request()and'yandex.ru/map-widget/'in r.url else None)
    page.bring_to_front();page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.readyState==="complete"&&document.fonts.status==="loaded"');page.wait_for_timeout(250)
    if label=='baseline':
     assert len(patched)==1,patched
     page.add_style_tag(content='@media(min-width:961px){.about-layer{contain:none}}.contact-map iframe{transition:none!important;opacity:1!important;pointer-events:auto!important}')
    geometry=page.locator('.contact-map').evaluate('e=>({top:e.getBoundingClientRect().top+scrollY,width:e.offsetWidth,height:e.offsetHeight})')
    page.evaluate('top=>scrollTo({top:top-innerHeight-300,behavior:"instant"})',geometry['top']);page.wait_for_timeout(300)
    cdp=context.new_cdp_session(page);done=[];cdp.on('Tracing.tracingComplete',lambda data:done.append(data));cdp.send('Emulation.setCPUThrottlingRate',{'rate':4});cdp.send('Tracing.start',{'categories':'devtools.timeline,blink.user_timing','transferMode':'ReturnAsStream'})
    page.bring_to_front();page.evaluate('mapLab.start=performance.now();mapLab.record=true')
    for _ in range(12):page.mouse.wheel(0,80);page.wait_for_timeout(35)
    page.wait_for_timeout(4000)
    # A slow provider is retained as a slow sample; no new scroll, retry or replacement.
    try:page.wait_for_function('mapLab.loadedAt!==null',timeout=70000)
    except Exception:pass
    page.evaluate('mapLab.record=false;mapLab.end=performance.now()');state=page.evaluate('mapLab');bootstrap=page.locator('.contact-map').evaluate('e=>({src:e.querySelector("iframe").getAttribute("src"),busy:e.getAttribute("aria-busy"),hidden:document.hidden,rect:e.getBoundingClientRect().toJSON()})');cdp.send('Tracing.end')
    while not done:page.wait_for_timeout(40)
    chunks=[];stream=done[0]['stream']
    while True:
     chunk=cdp.send('IO.read',{'handle':stream});chunks.append(chunk.get('data',''))
     if chunk.get('eof'):break
    cdp.send('IO.close',{'handle':stream});trace=json.loads(''.join(chunks));main=cdp.send('Page.getFrameTree')['frameTree']['frame']['id'];areas=[]
    for event in trace['traceEvents']:
     data=event.get('args',{}).get('data',{});clip=data.get('clip',[])
     if event.get('name')=='Paint'and data.get('frame')==main and len(clip)==8:
      area=(max(clip[::2])-min(clip[::2]))*(max(clip[1::2])-min(clip[1::2]))
      if area<1e8:areas.append(area)
    final=page.locator('.contact-map').evaluate('e=>({top:e.getBoundingClientRect().top+scrollY,width:e.offsetWidth,height:e.offsetHeight})');assert geometry==final
    gaps=sorted(v['gap']for v in state['frames']);long=[v for v in state['long']if state['start']<=v['t']<=state['end']];assert max(gaps)<=state['end']-state['start']
    row={'label':label,'run':run+1,'frameCount':len(gaps),'observationMs':state['end']-state['start'],'gapP95':gaps[int((len(gaps)-1)*.95)],'gapMax':max(gaps),'gapsOver50ms':sum(g>50 for g in gaps),'longTasks':long,'headerClassWrites':state['writes'],'hugePaintBounds':sum(a>5e7 for a in areas),'paintClipAreaSum':sum(areas),'geometry':geometry,'mapRequests':requests,'lastScroll':max(state['scrolls'],default=0),'visibleAt':state['visibleAt'],'srcAssignedAt':state['srcAssignedAt'],'loadedAt':state['loadedAt'],'visibility':state['visibility'],'bootstrap':bootstrap,'errors':errors};rows.append(row)
    assert requests and requests[0]>=row['lastScroll']+120,(requests,row['lastScroll']);assert not errors,errors
    print(label,run+1,'p95',round(row['gapP95'],1),'max',round(row['gapMax'],1),'huge paints',row['hugePaintBounds'],'header writes',row['headerClassWrites'],flush=True);context.close();browser.close()
finally:
 server.shutdown();server.server_close();after=reg.digest(folder)
 summary={label:{key:statistics.median(r[key]for r in rows if r['label']==label)for key in['gapP95','gapMax','gapsOver50ms','headerClassWrites','hugePaintBounds','paintClipAreaSum']}for label in['baseline','candidate']}if len(rows)==args.runs*2 else{}
 (OUT/'map-performance.json').write_text(json.dumps({'buildHash':before,'afterHash':after,'unchanged':before==after,'rows':rows,'summary':summary,'conditions':'One frozen private build; baseline restores only About paint containment, header state guard and map ready fade at delivery time; Chrome Windows, CPU x4, real wheel and real Yandex network; alternating order; no concurrent browser jobs. Paint clip bounds are not raster work or field FPS.','published':False,'physicalDevice':False},ensure_ascii=False,indent=2),encoding='utf-8')
assert before==after and len(rows)==args.runs*2
