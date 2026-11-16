"""Paired real-provider approach samples; requests, frame gaps and fixed map geometry."""
import importlib.util
import json
from pathlib import Path
import statistics
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('regression',ROOT/'tests/device-regression.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
folders={'baseline':ROOT/'tmp/baseline62/dist','candidate':ROOT/'dist'}
hashes={k:reg.digest(v)for k,v in folders.items()};servers={k:reg.serve(v)for k,v in folders.items()};rows=[]
try:
 with sync_playwright()as p:
  browser=p.chromium.launch(channel='chrome')
  for width,runs in [(1440,3),(390,1)]:
   for run in range(runs):
    for label in (['baseline','candidate']if run%2==0 else['candidate','baseline']):
     context=browser.new_context(viewport={'width':width,'height':900},reduced_motion='no-preference')
     context.add_init_script("window.mapLab={requests:[],frames:[],long:[],scrolls:[],recording:false};new PerformanceObserver(list=>mapLab.long.push(...list.getEntries().map(e=>({time:e.startTime,duration:e.duration,name:e.name})))).observe({type:'longtask',buffered:true});addEventListener('scroll',()=>{if(mapLab.recording)mapLab.scrolls.push(performance.now())},{passive:true});let previous=0;function frame(t){if(mapLab.recording&&previous)mapLab.frames.push(t-previous);previous=t;requestAnimationFrame(frame)}requestAnimationFrame(frame)")
     page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));requests=[]
     page.on('request',lambda r:requests.append({'url':r.url.split('?')[0],'time':page.evaluate('performance.now()')})if 'yandex.ru/map-widget/'in r.url else None)
     page.goto(servers[label][1],wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(350)
     cdp=context.new_cdp_session(page);cdp.send('Performance.enable');cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
     # Start far enough away that the preserved native-lazy map has not loaded yet.
     geometry=page.locator('.contact-map').evaluate("e=>{const r=e.getBoundingClientRect();return{top:r.top+scrollY,width:r.width,height:r.height}}")
     page.evaluate("top=>scrollTo({top:top-innerHeight-1800,behavior:'instant'})",geometry['top']);page.wait_for_timeout(180)
     page.evaluate('mapLab.frames=[];mapLab.scrolls=[];mapLab.recording=true;mapLab.start=performance.now()')
     for step in range(25):page.mouse.wheel(0,100);page.wait_for_timeout(35)
     page.wait_for_timeout(500)
     page.evaluate('mapLab.end=performance.now();mapLab.recording=false')
     try:page.wait_for_function("document.querySelector('.contact-map iframe').src.includes('yandex.ru/map-widget')&&document.querySelector('.contact-map').getAttribute('aria-busy')!=='true'",timeout=18000)
     except Exception:pass
     state=page.evaluate("({...mapLab,src:document.querySelector('.contact-map iframe').src,transform:getComputedStyle(document.querySelector('.contact-layout')).transform})")
     final=page.locator('.contact-map').evaluate("e=>{const r=e.getBoundingClientRect();return{top:r.top+scrollY,width:r.width,height:r.height}}")
     gaps=sorted(state['frames']);long=[v for v in state['long']if state['start']<=v['time']<=state['end']]
     last_scroll=max(state['scrolls'],default=state['start'])
     row={'label':label,'width':width,'run':run+1,'mapRequests':requests,'lastScroll':last_scroll,'start':state['start'],'end':state['end'],'frameCount':len(gaps),'gapP95':gaps[int((len(gaps)-1)*.95)]if gaps else None,'gapMax':max(gaps,default=0),'gapsOver50ms':sum(v>50 for v in gaps),'longTasks':long,'geometryBefore':geometry,'geometryAfter':final,'contactTransform':state['transform'],'errors':errors}
     assert geometry==final,(label,width,geometry,final)
     assert requests and 'yandex.ru/map-widget'in state['src'],(label,width,state['src'])
     if label=='candidate':
      assert state['transform']=='none'
      assert requests[0]['time']>=last_scroll+120,(requests,last_scroll)
     rows.append(row);context.close();print(label,width,run+1,'map starts',round(requests[0]['time']-last_scroll),'ms after scroll; p95 gap',row['gapP95'],flush=True)
  browser.close()
finally:
 for server,_ in servers.values():server.shutdown();server.server_close()
 after={k:reg.digest(v)for k,v in folders.items()}
 summary={label:{'desktopGapP95Median':statistics.median(r['gapP95']for r in rows if r['label']==label and r['width']==1440),'desktopGapsOver50msMedian':statistics.median(r['gapsOver50ms']for r in rows if r['label']==label and r['width']==1440)}for label in folders}if len(rows)==8 else{}
 (ROOT/'tmp/planning/iteration62/map-performance.json').write_text(json.dumps({'buildHashes':hashes,'unchanged':hashes==after,'rows':rows,'summary':summary,'conditions':'Real Yandex iframe, Chrome on Windows, CPU x4, real wheel approach, alternating runs. Network/provider content is uncontrolled; local frame gaps are not field FPS.','fieldData':False,'physicalDevice':False,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
assert hashes==after and len(rows)==8
