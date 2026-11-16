"""Equivalent cold-load lab samples against preserved and current static builds.

No production/field Core Web Vitals or physical GPU/battery claims.
python -X utf8 tests/device-performance.py --runs 3
"""
import argparse, functools, hashlib, http.server, json, socketserver, statistics, threading, time
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
    def copyfile(self,source,output):
        try: super().copyfile(source,output)
        except (ConnectionResetError,ConnectionAbortedError,BrokenPipeError): pass
class Server(socketserver.ThreadingMixIn,http.server.HTTPServer): daemon_threads=True
def serve(folder):
    server=Server(('127.0.0.1',0),functools.partial(Quiet,directory=str(folder)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server,f'http://127.0.0.1:{server.server_port}/'
def digest(folder):
    h=hashlib.sha256()
    for path in sorted(folder.rglob('*'),key=lambda p:tuple(part.lower()for part in p.relative_to(folder).parts)):
        if path.is_file():h.update(path.relative_to(folder).as_posix().encode());h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()
INIT="""window.lab={lcp:[],shift:[],long:[],events:[]};
for(const [type,key]of [['largest-contentful-paint','lcp'],['layout-shift','shift'],['longtask','long'],['event','events']])
if(PerformanceObserver.supportedEntryTypes.includes(type))new PerformanceObserver(list=>lab[key].push(...list.getEntries().map(e=>({time:e.startTime,duration:e.duration,value:e.value,input:e.hadRecentInput,name:e.name,interaction:e.interactionId,element:e.element?.className})))).observe({type,buffered:true,durationThreshold:16});"""

def sample(browser,url,phone,slow):
    context=browser.new_context(viewport={'width':390 if phone else 1440,'height':844 if phone else 900},is_mobile=phone,has_touch=phone)
    context.route('**/*',lambda route:route.continue_()if route.request.url.startswith(url)or route.request.url.startswith('data:')else route.abort())
    context.add_init_script(INIT);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    cdp=context.new_cdp_session(page);cdp.send('Network.enable');cdp.send('Network.setCacheDisabled',{'cacheDisabled':True});cdp.send('Performance.enable')
    traffic={}
    def response(event):
        traffic[event['requestId']]={'path':urlparse(event['response']['url']).path,'bytes':0,'complete':False}
    def data(event):
        if event['requestId']in traffic:traffic[event['requestId']]['bytes']+=event.get('encodedDataLength')or event.get('dataLength',0)
    def finished(event):
        if event['requestId']in traffic:traffic[event['requestId']].update(bytes=event['encodedDataLength'],complete=True)
    cdp.on('Network.responseReceived',response);cdp.on('Network.dataReceived',data);cdp.on('Network.loadingFinished',finished)
    if slow:
        cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
        cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':200000,'uploadThroughput':93750,'connectionType':'cellular4g'})
    start=time.monotonic();page.goto(url,wait_until='domcontentloaded');page.wait_for_timeout(max(0,8000-(time.monotonic()-start)*1000))
    initial=page.evaluate("""()=>({lab,paint:performance.getEntriesByType('paint').map(e=>({name:e.name,time:e.startTime})),fonts:document.fonts.status,ready:document.readyState,video:[...document.querySelectorAll('video')].map(v=>({src:v.getAttribute('src'),poster:v.getAttribute('poster'),paused:v.paused,ready:v.readyState,time:v.currentTime})),resources:performance.getEntriesByType('resource').map(e=>({path:new URL(e.name).pathname,bytes:e.encodedBodySize,type:e.initiatorType}))})""")
    initial_traffic=[dict(v)for v in traffic.values()]
    metrics={row['name']:row['value']for row in cdp.send('Performance.getMetrics')['metrics']}
    assert initial['fonts']=='loaded'and initial['ready']=='complete',initial
    if phone and 'efficient'in(initial['video'][0]['src']or''):
        assert not any(r['path'].startswith('/media/news/')for r in initial_traffic),initial_traffic
        assert not any(r['poster']for r in initial['video'][1:]),initial['video']
    page.locator('#faq').evaluate("e=>e.scrollIntoView({block:'start',behavior:'instant'})");page.wait_for_timeout(700)
    before={row['name']:row['value']for row in cdp.send('Performance.getMetrics')['metrics']}
    page.wait_for_timeout(1500)
    after={row['name']:row['value']for row in cdp.send('Performance.getMetrics')['metrics']}
    offscreen=page.locator('.hero-video').evaluate('v=>v.paused');assert offscreen
    if phone:
        page.locator('[data-open-menu]').click();page.wait_for_timeout(300);page.keyboard.press('Escape');page.wait_for_timeout(250)
    assert not errors,errors
    events=page.evaluate('lab.events');context.close()
    return {'phone':phone,'slow':slow,'initial':initial,'initialTraffic':initial_traffic,'initialBodyBytes':sum(row['bytes']for row in initial_traffic),'metrics':metrics,'offscreenHeroPaused':offscreen,'idleScriptSeconds':after['ScriptDuration']-before['ScriptDuration'],'idleTaskSeconds':after['TaskDuration']-before['TaskDuration'],'maxInteractionEventMs':max([e['duration']for e in events if e.get('interaction')]+[0]),'scriptErrors':errors}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runs',type=int,default=3);parser.add_argument('--phase',type=int,default=56);parser.add_argument('--delivery',choices=['source','native'],default='source');args=parser.parse_args()
    folders={'baseline':ROOT/f'tmp/baseline{args.phase}{"-native"if args.delivery=="native"else""}/dist','candidate':ROOT/f'tmp/candidate{args.phase}-native/dist'if args.delivery=='native'else ROOT/'dist'};before={k:digest(v)for k,v in folders.items()}
    servers={key:serve(folder)for key,folder in folders.items()};rows=[]
    try:
        with sync_playwright()as pw:
            browser=pw.chromium.launch(channel='chrome')
            try:
                for phone,slow in [(True,False),(True,True),(False,False)]:
                    for iteration in range(args.runs):
                        for label in ['baseline','candidate']:
                            row=sample(browser,servers[label][1],phone,slow);row.update(label=label,run=iteration+1,browser=browser.version)
                            rows.append(row);print(json.dumps({'label':label,'phone':phone,'slow':slow,'run':iteration+1,'bytes':row['initialBodyBytes'],'lcpMs':row['initial']['lab']['lcp'][-1]['time']if row['initial']['lab']['lcp']else None,'longTasks':len(row['initial']['lab']['long']),'idleScriptSeconds':row['idleScriptSeconds']},ensure_ascii=False),flush=True)
            finally:browser.close()
    finally:
        for server,_ in servers.values():server.shutdown();server.server_close()
        after={k:digest(v)for k,v in folders.items()}
        out=ROOT/f'tmp/planning/iteration{args.phase}';out.mkdir(parents=True,exist_ok=True)
        report={'rows':rows,'buildHashes':before,'unchanged':before==after,'conditions':'Chrome cold context, 8s load window, static HTTP without compression; slow = 4x CPU, 150ms RTT, 1.6Mbps down; external requests blocked','fieldData':False,'physicalDevice':False,'published':False}
        name='native-performance'if args.delivery=='native'else'performance'
        (out/(name+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        summary=[]
        for phone,slow in [(True,False),(True,True),(False,False)]:
            for label in folders:
                samples=[row for row in rows if row['phone']==phone and row['slow']==slow and row['label']==label]
                if not samples:continue
                summary.append({'label':label,'phone':phone,'slow':slow,'samples':len(samples),
                    'completedNonVideoBytes':statistics.median(sum(r['bytes']for r in row['initialTraffic']if r['complete']and not r['path'].endswith('.mp4'))for row in samples),
                    'lcpMs':statistics.median(row['initial']['lab']['lcp'][-1]['time']for row in samples if row['initial']['lab']['lcp']),
                    'idleScriptMs':statistics.median(row['idleScriptSeconds']*1000 for row in samples),
                    'maxObservedInteractionEventMs':max(row['maxInteractionEventMs']for row in samples)})
        (out/(name+'-summary.json')).write_text(json.dumps({'summary':summary,'buildHashes':before,'unchanged':before==after,'fieldData':False,'note':'Local small samples. Streaming MP4 bytes excluded; event duration is not field INP.','published':False},ensure_ascii=False,indent=2),encoding='utf-8')
    assert before==after and len(rows)==args.runs*6
if __name__=='__main__':main()
