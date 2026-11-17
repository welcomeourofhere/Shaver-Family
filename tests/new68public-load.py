"""Read-only public cold-load diagnosis; no SDK/network fixtures or form actions."""
import argparse,gzip,hashlib,json,re,time
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args();assert re.fullmatch(r'[\w-]+',a.label)
OUT=ROOT/'artifacts/iteration68'/a.label;OUT.mkdir(parents=True,exist_ok=False)
BUILD=json.loads((ROOT/'deploy/tilda-pages.json').read_text(encoding='utf-8'))['build']
PROFILES=[dict(name='phone-returning',width=390,height=844,phone=True,cpu=4,latency=150,bandwidth=200000,consent='denied'),dict(name='phone-first-visit',width=390,height=844,phone=True,cpu=4,latency=150,bandwidth=200000,consent=None),dict(name='desktop-returning',width=1440,height=900,phone=False,cpu=1,latency=0,bandwidth=-1,consent='denied')]
INIT="""(() => {if(top!==window)return;localStorage.setItem('soyuz_theme','light');%s
 window.loadProbe={lcp:[],shifts:[],long:[]};
 for(const [type,key] of [['largest-contentful-paint','lcp'],['layout-shift','shifts'],['longtask','long']])if(PerformanceObserver.supportedEntryTypes.includes(type))new PerformanceObserver(list=>{for(const e of list.getEntries())loadProbe[key].push({time:e.startTime,duration:e.duration,value:e.value,input:e.hadRecentInput,size:e.size,renderTime:e.renderTime,loadTime:e.loadTime,url:e.url,element:e.element?{tag:e.element.tagName,id:e.element.id,class:e.element.className,text:e.element.textContent.slice(0,180)}:null})}).observe({type,buffered:true});})();"""
def clean(url):
 u=urlsplit(url);return urlunsplit((u.scheme,u.netloc,u.path,'','')) if u.scheme in ['http','https']else url[:150]
def scrub(value):
 if isinstance(value,dict):return {k:scrub(v)for k,v in value.items()if k.lower()not in ['headers','requestheaders','responseheaders','postdata','cookies','authorization']}
 if isinstance(value,list):return[scrub(v)for v in value]
 if isinstance(value,str)and value.startswith(('http://','https://')):return clean(value)
 return value
def cls(entries):
 best=score=0;start=previous=-1
 for e in entries:
  if e['input']:continue
  if start<0 or e['time']-previous>1000 or e['time']-start>5000:start=e['time'];score=0
  score+=e['value'];previous=e['time'];best=max(best,score)
 return best
rows=[]
with sync_playwright()as pw:
 browser=pw.chromium.launch(channel='chrome',headless=True,args=['--mute-audio'])
 try:
  for profile in PROFILES:
   for run in range(1,4):
    c=browser.new_context(viewport={'width':profile['width'],'height':profile['height']},is_mobile=profile['phone'],has_touch=profile['phone'],device_scale_factor=1,color_scheme='light',reduced_motion='no-preference',service_workers='block')
    c.add_init_script(INIT% ("localStorage.setItem('soyuz.analytics.v1','denied');"if profile['consent']else''));page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    d=c.new_cdp_session(page);d.send('Network.enable');d.send('Network.setCacheDisabled',{'cacheDisabled':True});d.send('Network.clearBrowserCache');d.send('Emulation.setCPUThrottlingRate',{'rate':profile['cpu']});d.send('Network.emulateNetworkConditions',{'offline':False,'latency':profile['latency'],'downloadThroughput':profile['bandwidth'],'uploadThroughput':93750 if profile['phone']else-1,'connectionType':'cellular4g'if profile['phone']else'ethernet'})
    requests={};trace=[];complete=[]
    def requested(e):requests[e['requestId']]={'url':clean(e['request']['url']),'type':e.get('type'),'start':e['timestamp'],'initiator':scrub(e.get('initiator',{}))}
    def responded(e):
     if e['requestId']in requests:
      r=e['response'];h={k.lower():v for k,v in r.get('headers',{}).items()};requests[e['requestId']].update(status=r['status'],mime=r['mimeType'],response=e['timestamp'],protocol=r.get('protocol'),headers={k:h[k]for k in ['content-encoding','content-length','cache-control']if k in h},timing=r.get('timing'))
    def finished(e):
     if e['requestId']in requests:requests[e['requestId']].update(end=e['timestamp'],encodedBytes=e['encodedDataLength'])
    def failed(e):
     if e['requestId']in requests:requests[e['requestId']].update(failure=e.get('errorText'))
    d.on('Network.requestWillBeSent',requested);d.on('Network.responseReceived',responded);d.on('Network.loadingFinished',finished);d.on('Network.loadingFailed',failed);d.on('Tracing.dataCollected',lambda e:trace.extend(e['value']));d.on('Tracing.tracingComplete',lambda e:complete.append(True))
    row={'profile':profile,'run':run,'browser':browser.version,'traceEnabled':True,'fieldData':False,'physicalDevice':False,'deliveryStubbed':False,'ownErrors':errors}
    try:
     d.send('Tracing.start',{'categories':'devtools.timeline,loading,blink.user_timing','transferMode':'ReportEvents'});begin=time.monotonic();response=page.goto('https://soyuz.hair/',wait_until='commit',timeout=45000);assert response.status==200
     page.wait_for_timeout(max(0,10000-(time.monotonic()-begin)*1000));page.wait_for_function('performance.now()>=10000',timeout=2000)
     state=page.evaluate("""()=>({now:performance.now(),timeOrigin:performance.timeOrigin,probe:loadProbe,paints:performance.getEntriesByType('paint').map(e=>({name:e.name,time:e.startTime})),navigation:performance.getEntriesByType('navigation').map(e=>({ttfb:e.responseStart,responseEnd:e.responseEnd,dcl:e.domContentLoadedEventEnd,load:e.loadEventEnd,transfer:e.transferSize,encoded:e.encodedBodySize,decoded:e.decodedBodySize})),styles:[...document.querySelectorAll('link[rel=stylesheet]')].map(e=>({url:e.href,media:e.media})),fonts:document.fonts.status,news:document.querySelector('.hero-scene')?.dataset.newsState,cookie:document.documentElement.dataset.cookiePrompt,builds:[...new Set([...document.scripts].map(s=>s.src.match(/Soyuz\\/releases\\/([a-f0-9]{20})/)).filter(Boolean).map(m=>m[1]))],resources:performance.getEntriesByType('resource').map(e=>({url:e.name,start:e.startTime,responseStart:e.responseStart,end:e.responseEnd,transfer:e.transferSize,encoded:e.encodedBodySize,decoded:e.decodedBodySize,type:e.initiatorType}))})""")
     assert state['builds']==[BUILD],state['builds'];lcp=[e for e in state['probe']['lcp']if e['time']<=10000];row.update(state=scrub(state),lcpMs=lcp[-1]['time']if lcp else None,cls=cls([e for e in state['probe']['shifts']if e['time']<=10000]),measurementWindowEndMs=10000)
     assert row['lcpMs']is not None and any(e['name']=='first-contentful-paint'and e['time']<=10000 for e in state['paints']),'No FCP/LCP in the fixed 10s window; sample is incomplete'
     if run==1:page.screenshot(path=str(OUT/(profile['name']+'.png')))
    except Exception as e:row['failure']=str(e)
    finally:
     try:
      d.send('Tracing.end');deadline=time.monotonic()+15
      while not complete and time.monotonic()<deadline:page.wait_for_timeout(100)
      assert complete,'Trace incomplete'
     except Exception as e:row['traceFailure']=str(e)
     row['network']=list(requests.values());row['traceEvents']=len(trace)
     trace_file=OUT/(profile['name']+'-'+str(run)+'.trace.json.gz');trace_file.write_bytes(gzip.compress(json.dumps({'traceEvents':scrub(trace),'metadata':{'browser':browser.version,'build':BUILD,'profile':profile,'queryValuesRemoved':True}},ensure_ascii=False).encode(),mtime=0));row['traceFile']=trace_file.name;row['traceSha256']=hashlib.sha256(trace_file.read_bytes()).hexdigest();rows.append(row);c.close()
     (OUT/'results.json').write_text(json.dumps({'build':BUILD,'rows':rows,'conditions':'Actual HTTPS, native gzip, fresh contexts, cache disabled, fixed light/DPR1, all9 same trace categories, no network fixtures. PhoneCPU4/150ms/200000Bps. Firstvisit vs denied returning explicit. No forms or account access.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'profile':profile['name'],'run':run,'lcpMs':row.get('lcpMs'),'cls':row.get('cls'),'failure':row.get('failure'),'errors':len(errors),'traceEvents':len(trace)}),flush=True)
 finally:browser.close()
assert len(rows)==9 and not any(r.get('failure')or r.get('traceFailure')or r['ownErrors']for r in rows)
print('PASS9 public load profiles; browserclosed END')
