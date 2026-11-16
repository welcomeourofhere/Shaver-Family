"""24 bounded paired lab samples. No field CWV/INP/FPS or physical-phone claims."""
import argparse
import hashlib
import json
import re
import statistics
import subprocess
import time
import tinycss2
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--baseline',default='http://127.0.0.1:4381/')
parser.add_argument('--candidate',default='http://127.0.0.1:4382/')
parser.add_argument('--baseline-folder',type=Path,default=ROOT/'tmp/planning/iteration66/baseline-E/site')
parser.add_argument('--candidate-folder',type=Path,default=ROOT/'tmp/planning/iteration66/ci-native/site')
parser.add_argument('--label',required=True)
parser.add_argument('--prepare-only',action='store_true')
parser.add_argument('--map-run',type=int,choices=[1,2,3],help='Replace one explicitly contaminated complete map pair; never an automatic retry')
parser.add_argument('--merge-replacement',nargs=2,type=Path,metavar=('ORIGINAL','REPLACEMENT'),help='Write a new accepted summary, preserving both raw reports; launches no browser')
parser.add_argument('--floating-ab',action='store_true',help='Six diagnostic map samples; OFF changes only the compiled adaptive-floating branch guard in a response fixture')
parser.add_argument('--static-from',type=Path,help='Analyse existing accepted resources/CSS/manifest only; launches no browser or compression')
args=parser.parse_args()
assert re.fullmatch(r'[\w-]+',args.label)
URLS={'E':args.baseline,'66':args.candidate}
FOLDERS={'E':args.baseline_folder.resolve(),'66':args.candidate_folder.resolve()}
for url in URLS.values():assert urlsplit(url).scheme=='http' and urlsplit(url).hostname in ['127.0.0.1','localhost'] and not urlsplit(url).query
OUT=ROOT/'tmp/planning/iteration66/benchmark'/args.label
OUT.mkdir(parents=True,exist_ok=False)
PROFILES=[{'name':'desktop','width':1440,'height':900,'phone':False,'cpu':1,'slow':False},
          {'name':'phone','width':390,'height':844,'phone':True,'cpu':1,'slow':False},
          {'name':'slowphone','width':390,'height':844,'phone':True,'cpu':4,'slow':True}]
MAP_PROFILE={'name':'map-desktop-cpu4','width':1440,'height':900,'phone':False,'cpu':4,'slow':True}
FLOATING_VARIANT='on'
FLOATING_FIXTURE=None

def floating_fixture():
    files=list((FOLDERS['66']/'_astro').glob('SiteSettings.*.js'));assert len(files)==1,files
    path=files[0];source=path.read_text(encoding='utf-8')
    code="""const fs=require('fs'),ts=require('typescript'),s=fs.readFileSync(process.argv[1],'utf8'),f=ts.createSourceFile('fixture.js',s,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS),m=f.statements.filter(n=>ts.isIfStatement(n)&&['elementsFromPoint','--golden-ratio','floatingTone'].every(x=>n.getText(f).includes(x)));if(m.length!==1)throw Error('Adaptive branch match count '+m.length);const n=m[0];process.stdout.write(JSON.stringify({start:n.expression.getStart(f),end:n.expression.end,statementStart:n.getStart(f),statementEnd:n.end,condition:n.expression.getText(f)}));"""
    located=subprocess.run(['node','-e',code,str(path)],cwd=ROOT,check=True,capture_output=True,text=True)
    info=json.loads(located.stdout);patched=source[:info['start']]+'false'+source[info['end']:]
    return {**info,'path':str(path),'urlPath':'/_astro/'+path.name,'source':source,'patched':patched,
            'sourceSha256':hashlib.sha256(source.encode()).hexdigest(),'offSha256':hashlib.sha256(patched.encode()).hexdigest()}

def profile_summary(profile,diagnostics,frame_id):
    nodes={n['id']:n for n in profile['nodes']};parents={child:n['id'] for n in profile['nodes'] for child in n.get('children',[])}
    scripts=diagnostics['scripts'];contexts=diagnostics['contexts'];totals={};adaptive=0;main_self=0
    for sample,delta in zip(profile.get('samples',[]),profile.get('timeDeltas',[])):
        ms=delta/1000;seen=set();adaptive_here=False;node_id=sample
        while node_id in nodes:
            call=nodes[node_id]['callFrame'];meta=scripts.get(call['scriptId'],{});context=contexts.get(meta.get('context'),{})
            url=call.get('url') or meta.get('url','')
            if context.get('frameId')==frame_id and url and url not in seen:
                totals[url]=totals.get(url,0)+ms;seen.add(url)
                if node_id==sample:main_self+=ms
            if context.get('frameId')==frame_id and url.endswith(FLOATING_FIXTURE['urlPath']) and call.get('lineNumber')==0 and FLOATING_FIXTURE['statementStart']<=call.get('columnNumber',-1)<=FLOATING_FIXTURE['statementEnd']:
                adaptive_here=True
            if node_id not in parents:break
            node_id=parents[node_id]
        if adaptive_here:adaptive+=ms
    return {'mainFrameId':frame_id,'profileSampleCount':len(profile.get('samples',[])),'sampledWallMs':sum(profile.get('timeDeltas',[]))/1000,
            'mainFrameScriptLeafSelfMs':main_self,'adaptiveInclusiveSampleMs':adaptive,
            'mainFrameScriptInclusiveMs':sorted([{'url':url,'sampleMs':ms} for url,ms in totals.items()],key=lambda row:-row['sampleMs'])}

def sha(data):return hashlib.sha256(data).hexdigest()
def digest(folder):
    value=hashlib.sha256()
    for path in sorted(folder.rglob('*'),key=lambda p:p.relative_to(folder).as_posix().casefold()):
        if path.is_file():value.update(path.relative_to(folder).as_posix().encode());value.update(hashlib.sha256(path.read_bytes()).digest())
    return value.hexdigest()
def safe_url(value):
    url=urlsplit(value)
    return {'url':f'{url.scheme}://{url.netloc}{url.path}','queryKeys':sorted({v.split('=')[0] for v in url.query.split('&') if v})}
def own_category(value,own_host):
    url=urlsplit(value)
    if url.netloc==own_host:return 'own'
    if url.hostname=='raw.githubusercontent.com':return 'news-endpoint-blocked-for-local-snapshot'
    if url.hostname and ('google-analytics' in url.hostname or 'googletagmanager' in url.hostname or url.hostname.startswith('mc.yandex.')):return 'analytics-denied'
    return 'provider'
def cls_score(entries):
    best=score=0;start=previous=-1
    for row in sorted((x for x in entries if not x['input']),key=lambda x:x['time']):
        if start<0 or row['time']-previous>1000 or row['time']-start>5000:start=row['time'];score=0
        score+=row['value'];previous=row['time'];best=max(best,score)
    return best
def long_summary(entries):return {'count':len(entries),'totalMs':sum(x['duration'] for x in entries),'maxMs':max([x['duration'] for x in entries]+[0]),'excessOver50Ms':sum(max(0,x['duration']-50) for x in entries)}
def median(values):return statistics.median(v for v in values if v is not None) if any(v is not None for v in values) else None

INIT="""(() => {
 if(window.top!==window)return;
 localStorage.setItem('soyuz_theme','light');localStorage.setItem('soyuz.analytics.v1','denied');
 localStorage.removeItem('soyuz.analytics.v2');
 window.lab={lcp:[],shifts:[],long:[],events:[],gaps:[],recordFrames:false};
 for(const [type,key] of [['largest-contentful-paint','lcp'],['layout-shift','shifts'],['longtask','long'],['event','events']])
  if(PerformanceObserver.supportedEntryTypes.includes(type))new PerformanceObserver(list=>{
   for(const e of list.getEntries())lab[key].push({time:e.startTime,duration:e.duration,value:e.value,input:e.hadRecentInput,
    name:e.name,interaction:e.interactionId,processingStart:e.processingStart,processingEnd:e.processingEnd,
    url:e.url,element:e.element?.className,attribution:e.attribution?.map(a=>({name:a.name,type:a.containerType,src:a.containerSrc}))});
  }).observe({type,buffered:true,durationThreshold:16});
 let previous=0;const frame=t=>{if(lab.recordFrames&&previous)lab.gaps.push(t-previous);previous=t;requestAnimationFrame(frame)};requestAnimationFrame(frame);
})()"""

def resource_report(records,cutoff=None):
    rows=[]
    cutoff=time.time()*1000 if cutoff is None else cutoff
    snapshot=[(request,dict(data)) for request,data in list(records.items()) if data['atEpochMs']<=cutoff]
    for request,data in snapshot:
        row={**data}
        row['finished']=bool(row.get('finished') and row.get('finishedAtEpochMs',float('inf'))<=cutoff)
        row['timing']=request.timing
        if row.get('finished'):
            try:row['sizes']=request.sizes()
            except Exception as error:row['sizesError']=str(error)
        rows.append(row)
    nonvideo=[r for r in rows if r.get('finished') and not (r.get('mime','').startswith('video/') or re.search(r'\.(mp4|webm)$',urlsplit(r['url']).path))]
    return {'resources':rows,'completedNonVideoBodyBytes':sum(r.get('sizes',{}).get('responseBodySize',0) for r in nonvideo),
            'completedNonVideoWireBytes':sum(r.get('sizes',{}).get('responseBodySize',0)+r.get('sizes',{}).get('responseHeadersSize',0) for r in nonvideo),
            'inFlight':sum(not r.get('finished') and not r.get('failure') for r in rows),
            'ownFailures':[r for r in rows if r['category']=='own' and (r.get('failure') or r.get('status',200)>=400)],
            'providerFailures':[r for r in rows if r['category']=='provider' and (r.get('failure') or r.get('status',200)>=400)]}

def setup(browser,label,profile):
    context=browser.new_context(viewport={'width':profile['width'],'height':profile['height']},is_mobile=profile['phone'],has_touch=profile['phone'],device_scale_factor=1,color_scheme='light',reduced_motion='no-preference',service_workers='block')
    context.add_init_script(INIT)
    fixture_hits=[]
    if args.floating_ab:
        body=FLOATING_FIXTURE['source'] if FLOATING_VARIANT=='on' else FLOATING_FIXTURE['patched']
        def fixture_response(route):
            fixture_hits.append(route.request.url)
            route.fulfill(status=200,body=body,content_type='text/javascript',headers={'Cache-Control':'no-store'})
        context.route('**'+FLOATING_FIXTURE['urlPath'],fixture_response)
    # Freeze each build's own local fallback; no content rewrite or image/network stubs.
    context.route('https://raw.githubusercontent.com/**',lambda route:route.abort())
    for pattern in ['https://www.googletagmanager.com/**','https://*.google-analytics.com/**','https://mc.yandex.ru/**','https://mc.yandex.com/**']:
        context.route(pattern,lambda route:route.abort())
    page=context.new_page();records={};errors=[];host=urlsplit(URLS[label]).netloc
    def page_error(error):
        stack=error.stack or '';category='own' if host in stack else 'provider' if re.search(r'https?://',stack) else 'unknown'
        errors.append({'message':str(error),'stack':stack,'category':category})
    page.on('pageerror',page_error)
    def requested(request):records[request]={**safe_url(request.url),'category':own_category(request.url,host),'type':request.resource_type,'atEpochMs':time.time()*1000,'finished':False}
    def responded(response):
        if response.request in records:records[response.request].update(status=response.status,mime=response.headers.get('content-type',''))
    def finished(request):
        if request in records:records[request].update(finished=True,finishedAtEpochMs=time.time()*1000)
    def failed(request):
        if request in records:records[request]['failure']=request.failure
    page.on('request',requested);page.on('response',responded);page.on('requestfinished',finished);page.on('requestfailed',failed)
    cdp=context.new_cdp_session(page);cdp.send('Network.enable');cdp.send('Network.setCacheDisabled',{'cacheDisabled':True});cdp.send('Network.clearBrowserCache');cdp.send('Performance.enable')
    cdp.send('Emulation.setCPUThrottlingRate',{'rate':profile['cpu']})
    cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':150 if profile['slow'] else 0,'downloadThroughput':200000 if profile['slow'] else -1,'uploadThroughput':93750 if profile['slow'] else -1,'connectionType':'cellular4g' if profile['slow'] else 'ethernet'})
    diagnostics={'contexts':{},'scripts':{},'fixtureHits':fixture_hits}
    if args.floating_ab:
        cdp.on('Runtime.executionContextCreated',lambda event:diagnostics['contexts'].update({event['context']['id']:event['context'].get('auxData',{})}))
        cdp.on('Debugger.scriptParsed',lambda event:diagnostics['scripts'].update({event['scriptId']:{'url':event.get('url',''),'context':event.get('executionContextId')}}))
        cdp.send('Runtime.enable');cdp.send('Debugger.enable');cdp.send('Profiler.enable');cdp.send('Profiler.setSamplingInterval',{'interval':1000})
    return context,page,cdp,records,errors,diagnostics

def metrics(cdp):return {v['name']:v['value'] for v in cdp.send('Performance.getMetrics')['metrics']}
def metric_delta(before,after):return {name:(after.get(name,0)-before.get(name,0))*1000 for name in ['ScriptDuration','LayoutDuration','RecalcStyleDuration','TaskDuration']}
def wait_window(page,start,ms):page.wait_for_timeout(max(0,ms-(time.monotonic()-start)*1000))
def safe_actions(page,cdp,phone):
    start=page.evaluate('performance.now()');before=metrics(cdp)
    if phone:
        button=page.locator('[data-mobile-nav] [data-open-menu]');rect=button.bounding_box()
        assert rect and rect['width']>=44 and rect['height']>=44,rect
        p={'x':rect['x']+rect['width']/2,'y':rect['y']+rect['height']/2,'id':1}
        cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[p]});cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        page.wait_for_function("document.querySelector('#mobile-menu').open",timeout=10000);page.wait_for_timeout(340)
        page.keyboard.press('Escape');page.wait_for_function("!document.querySelector('#mobile-menu').open",timeout=10000)
    else:
        rail=page.locator('.hero-rail');rail.focus();page.keyboard.press('ArrowRight');page.wait_for_timeout(180);page.keyboard.press('ArrowLeft')
    page.wait_for_timeout(350);end=page.evaluate('performance.now()');after=metrics(cdp)
    data=page.evaluate('({events:lab.events,long:lab.long})')
    events=[e for e in data['events'] if e.get('interaction') and start<=e['time']<=end]
    return {'startMs':start,'endMs':end,'events':events,'maxObservedEventDurationMs':max([e['duration'] for e in events]+[0]),
            'maxObservedInputDelayMs':max([e['processingStart']-e['time'] for e in events]+[0]),'cpuMs':metric_delta(before,after),
            'longTasks':long_summary([e for e in data['long'] if start<=e['time']<=end]),'meaning':'single-session EventTiming, not field INP'}

def cold(browser,label,profile,run):
    context,page,cdp,records,errors,_=setup(browser,label,profile)
    row={'kind':'cold','candidate':label,'profile':profile,'run':run}
    try:
        begin=time.monotonic();page.goto(URLS[label],wait_until='domcontentloaded',timeout=30000);wait_window(page,begin,8000)
        data=page.evaluate("""() => ({now:performance.now(),timeOrigin:performance.timeOrigin,lab,ready:document.readyState,fonts:document.fonts.status,
          paints:performance.getEntriesByType('paint').map(e=>({name:e.name,time:e.startTime})),
          navigation:performance.getEntriesByType('navigation').map(e=>({responseStart:e.responseStart,domContentLoaded:e.domContentLoadedEventEnd,load:e.loadEventEnd})),
          video:[...document.querySelectorAll('video')].filter(v=>v.getAttribute('src')).map(v=>({src:v.currentSrc,ready:v.readyState,time:v.currentTime,paused:v.paused})),
          newsState:document.querySelector('.hero-scene').dataset.newsState,newsId:document.querySelector('.hero-slide[data-hero-active=true]')?.dataset.newsId,
          domElements:document.getElementsByTagName('*').length,reviewCards:document.querySelectorAll('.review-card').length,consent:localStorage.getItem('soyuz.analytics.v2')})""")
        cutoff=min(data['now'],8000);lcp=[x for x in data['lab']['lcp'] if x['time']<=cutoff];early=[x for x in lcp if x['time']<6000]
        row.update(windowMs=cutoff,ready=data['ready'],fonts=data['fonts'],paint=data['paints'],navigation=data['navigation'],
                   lcpMs=lcp[-1]['time'] if lcp else None,lcpBefore6sMs=early[-1]['time'] if early else None,lcpCandidates=lcp,
                   cls=cls_score([x for x in data['lab']['shifts'] if x['time']<=cutoff]),layoutShifts=data['lab']['shifts'],
                   longTasks=long_summary([x for x in data['lab']['long'] if x['time']<=cutoff]),cpu=metrics(cdp),
                   newsState=data['newsState'],newsId=data['newsId'],domElements=data['domElements'],reviewCards=data['reviewCards'],video=data['video'],consent=data['consent'],sampledAtMs=data['now'],**resource_report(records,data['timeOrigin']+cutoff))
        try:row['interaction']=safe_actions(page,cdp,profile['phone'])
        except Exception as error:row['interactionFailure']=str(error)
    except Exception as error:row['failure']=str(error);row.update(resource_report(records))
    finally:row['pageErrors']=errors;row['ownPageErrors']=[e for e in errors if e['category']=='own'];context.close()
    return row

def map_sample(browser,label,run):
    profile=MAP_PROFILE;context,page,cdp,records,errors,diagnostics=setup(browser,label,profile)
    row={'kind':'map','candidate':label,'profile':profile,'run':run}
    try:
        page.goto(URLS[label],wait_until='domcontentloaded',timeout=30000);page.evaluate('document.fonts.ready');page.wait_for_timeout(400)
        if args.floating_ab:assert len(diagnostics['fixtureHits'])==1,diagnostics['fixtureHits']
        geometry=page.locator('.contact-map').evaluate('e=>{const r=e.getBoundingClientRect();return{top:r.top+scrollY,width:r.width,height:r.height}}')
        page.locator('#about').evaluate("e=>e.scrollIntoView({block:'start',behavior:'instant'})");page.wait_for_timeout(200)
        start_y=page.evaluate('scrollY');distance=max(0,geometry['top']-start_y-250)
        frame_id=cdp.send('Page.getFrameTree')['frameTree']['frame']['id'] if args.floating_ab else None
        if args.floating_ab:cdp.send('Profiler.start')
        before=metrics(cdp);begin=time.monotonic();mark=page.evaluate('lab.gaps=[];lab.recordFrames=true;performance.now()');time_origin=page.evaluate('performance.timeOrigin')
        steps=[];goal=geometry['top']-250
        for _ in range(60):
            y=page.evaluate('scrollY');remaining=goal-y
            if remaining<=50:break
            delta=min(160,max(30,remaining/3));steps.append({'y':y,'deltaY':delta})
            page.mouse.wheel(0,delta);page.wait_for_timeout(40)
        wait_window(page,begin,12000);end=page.evaluate('lab.recordFrames=false;performance.now()');after=metrics(cdp)
        if args.floating_ab:
            profile_data=cdp.send('Profiler.stop')['profile']
            (OUT/f'profile-{FLOATING_VARIANT}-{run}.json').write_text(json.dumps({'profile':profile_data,'contexts':diagnostics['contexts'],'scripts':diagnostics['scripts'],'mainFrameId':frame_id}),encoding='utf-8')
            row['mainFrameProfile']=profile_summary(profile_data,diagnostics,frame_id)
            row['mainFrameProfile']['fixtureHits']=diagnostics['fixtureHits']
            row['floatingVariant']=FLOATING_VARIANT
        state=page.evaluate("""() => ({long:lab.long,gaps:lab.gaps,y:scrollY,
          mapSrc:document.querySelector('.contact-map iframe').src,busy:document.querySelector('.contact-map').getAttribute('aria-busy'),
          contactTransform:getComputedStyle(document.querySelector('.contact-layout')).transform})""")
        final=page.locator('.contact-map').evaluate('e=>{const r=e.getBoundingClientRect();return{top:r.top+scrollY,width:r.width,height:r.height}}')
        frames=[f for f in page.frames if 'yandex.' in f.url and '/map-widget/' in f.url]
        provider=None
        if frames:
            try:provider=frames[0].evaluate("({ready:document.readyState,title:document.title,bodyChildren:document.body?.children.length,errorLike:/captcha|robot|ошибка|error/i.test(document.title)})")
            except Exception as error:provider={'inspectionFailure':str(error)}
        gaps=sorted(state['gaps']);traffic=resource_report(records,time_origin+end)
        window_resources=[r for r in traffic['resources'] if r['atEpochMs']>=time_origin+mark]
        row.update(startMs=mark,endMs=end,startY=start_y,endY=state['y'],wheelDistance=distance,wheelSteps=steps,
                   geometryBefore=geometry,geometryAfter=final,geometryStable=all(abs(geometry[k]-final[k])<1 for k in geometry),
                   mapSrc=state['mapSrc'],mapBusy=state['busy'],providerState=provider,contactTransform=state['contactTransform'],
                   mainLongTasks=long_summary([x for x in state['long'] if mark<=x['time']<=end]),mainCpuMs=metric_delta(before,after),
                   callbackGapP95Ms=gaps[int((len(gaps)-1)*.95)] if gaps else None,callbackGapMaxMs=max(gaps,default=0),callbackGapsOver50=sum(v>50 for v in gaps),
                   callbackCount=len(gaps),windowResourceBodyBytes=sum(r.get('sizes',{}).get('responseBodySize',0) for r in window_resources),
                   providerBodyBytes=sum(r.get('sizes',{}).get('responseBodySize',0) for r in window_resources if r['category']=='provider'),
                   providerDocumentLoaded=bool(provider and provider.get('ready')=='complete' and provider.get('bodyChildren',0)>0 and not provider.get('errorLike')),
                   **traffic)
        screenshot_name=f'map-{FLOATING_VARIANT if args.floating_ab else label}-{run}.png'
        page.screenshot(path=str(OUT/screenshot_name))
        row['screenshot']=screenshot_name
    except Exception as error:row['failure']=str(error);row.update(resource_report(records))
    finally:row['pageErrors']=errors;row['ownPageErrors']=[e for e in errors if e['category']=='own'];context.close()
    return row

def summary(rows):
    if any('floatingVariant' in row for row in rows):
        result=[]
        for variant in ['off','on']:
            selected=[r for r in rows if r.get('floatingVariant')==variant]
            result.append({'variant':variant,'samples':len(selected),
                'medianMainScriptMs':median([r.get('mainCpuMs',{}).get('ScriptDuration') for r in selected]),
                'medianCallbackGapP95Ms':median([r.get('callbackGapP95Ms') for r in selected]),
                'medianAdaptiveInclusiveSampleMs':median([r.get('mainFrameProfile',{}).get('adaptiveInclusiveSampleMs') for r in selected]),
                'ownFailures':sum(bool(r.get('ownFailures') or r.get('ownPageErrors') or r.get('failure')) for r in selected)})
        return result
    groups=[]
    for kind,names in [('cold',[p['name'] for p in PROFILES]),('map',[MAP_PROFILE['name']])]:
        for name in names:
            pair={}
            for label in URLS:
                selected=[r for r in rows if r['kind']==kind and r['profile']['name']==name and r['candidate']==label]
                valid=[r for r in selected if not r.get('failure') and not r.get('ownFailures') and not r.get('ownPageErrors')]
                fields=['lcpMs','lcpBefore6sMs','cls','completedNonVideoBodyBytes'] if kind=='cold' else ['callbackGapP95Ms','callbackGapsOver50','completedNonVideoBodyBytes']
                pair[label]={'sampleCount':len(selected),'validOwnSamples':len(valid),'medians':{field:median([r.get(field) for r in valid]) for field in fields},
                             'providerFailures':sum(bool(r.get('providerFailures')) for r in selected)}
                if kind=='map':pair[label]['providerDocumentLoadedSamples']=sum(bool(r.get('providerDocumentLoaded')) for r in selected)
                if kind=='cold':
                    interactions=[r['interaction'] for r in valid if 'interaction' in r]
                    pair[label]['validInteractions']=len(interactions)
                    pair[label]['interactionFailures']=[r['interactionFailure'] for r in selected if r.get('interactionFailure')]
                    pair[label]['maxObservedEventDurationMs']=max([r['maxObservedEventDurationMs'] for r in interactions]) if interactions else None
            deltas={key:(pair['66']['medians'][key]-pair['E']['medians'][key]) if pair['66']['medians'][key] is not None and pair['E']['medians'][key] is not None else None for key in pair['E']['medians']}
            groups.append({'kind':kind,'profile':name,'candidates':pair,'medianDelta66MinusE':deltas})
    return groups

if args.static_from:
    measured=json.loads(args.static_from.read_text(encoding='utf-8'))
    candidate_folder=Path(measured['folders']['66']);manifest=json.loads((ROOT/measured['sources']['66']['manifest']).read_text(encoding='utf-8'))
    representative=next(row for row in measured['rows'] if row['kind']=='cold' and row['profile']['name']=='slowphone' and row['candidate']=='66' and row['run']==2)
    style_paths=sorted({urlsplit(row['url']).path.lstrip('/') for row in representative['resources'] if row['category']=='own' and row['type']=='stylesheet'})
    guard=':not(#soyuz-export-style-a#soyuz-export-style-b)';rules_by_key={};styles=[]
    def visit_rules(rules,context,filename):
        for rule in rules:
            if rule.type=='qualified-rule':
                selector=tinycss2.serialize(rule.prelude).strip();body=tinycss2.serialize(rule.content).strip();key=(context,selector,body)
                rules_by_key.setdefault(key,[]).append(filename)
            elif rule.type=='at-rule' and rule.lower_at_keyword in ['media','supports','container','layer','scope'] and rule.content is not None:
                visit_rules(tinycss2.parse_rule_list(rule.content),context+(f'@{rule.lower_at_keyword} '+tinycss2.serialize(rule.prelude).strip(),),filename)
    for path in style_paths:
        body=(candidate_folder/path).read_bytes();text=body.decode('utf-8');entry=next(row for row in manifest['files'] if row['sourcePath']==path)
        payload=(ROOT/entry['file']).read_bytes();assert len(payload)==entry['bytes'] and sha(payload)==entry['sha256']
        styles.append({'path':path,'fixtureRawBytes':len(body),'guardCount':text.count(guard),'guardRawBytes':text.count(guard)*len(guard.encode()),
                       'cloudContentBytes':entry['contentBytes'],'cloudEncodedBytes':entry['bytes'],'contentEncoding':entry['contentEncoding'],'cloudPayloadSha256':entry['sha256']})
        visit_rules(tinycss2.parse_stylesheet(text),(),path)
    cross=[{'context':list(key[0]),'selector':key[1],'declarations':key[2],'files':sorted(set(files))} for key,files in rules_by_key.items() if len(set(files))>1]
    critical=[]
    for candidate in ['E','66']:
        row=next(row for row in measured['rows'] if row['kind']=='cold' and row['profile']['name']=='slowphone' and row['candidate']==candidate and row['run']==2)
        own=[r for r in row['resources'] if r['category']=='own'];doc=next(r for r in own if r['type']=='document');start=doc['timing']['startTime']
        waterfall=[{**{k:r[k] for k in ['url','type']},'bodyBytes':r.get('sizes',{}).get('responseBodySize'),
                    'startMs':r['timing']['startTime']-start,'finishMs':r['timing']['startTime']-start+r['timing']['responseEnd']} for r in own]
        preceding=sorted([r for r in waterfall if 0<r['finishMs']<=row['lcpMs']],key=lambda r:r['finishMs'])[-20:]
        critical.append({'candidate':candidate,'run':2,'lcpMs':row['lcpMs'],'lcp':row['lcpCandidates'][-1],'paint':row['paint'],
                         'documentBytes':doc.get('sizes',{}).get('responseBodySize'),'documentResponseEndMs':doc['timing']['responseEnd'],
                         'last20FinishingBeforeLCP':preceding,'allResourceWaterfall':sorted(waterfall,key=lambda r:r['startMs'])})
    result={'sourceReport':str(args.static_from),'build':manifest['build'],'styles':styles,
            'totalFixtureRawBytes':sum(s['fixtureRawBytes'] for s in styles),'totalCloudContentBytes':sum(s['cloudContentBytes'] for s in styles),
            'totalCloudEncodedBytes':sum(s['cloudEncodedBytes'] for s in styles),'totalGuardRawBytes':sum(s['guardRawBytes'] for s in styles),
            'exactCrossFileDuplicateRules':cross,'distinctContextualRuleCount':len(rules_by_key),'criticalPathWaterfalls':critical,
            'note':'Existing manifest gzip payload sizes/hashes only; no recompression. Last20 is a waterfall view, not a dependency/field trace. Guards are an export-isolation contract.'}
    (OUT/'static.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({key:result[key] for key in ['totalFixtureRawBytes','totalCloudContentBytes','totalCloudEncodedBytes','totalGuardRawBytes','distinctContextualRuleCount']},ensure_ascii=False))
    print('cross-file duplicate rules',len(cross),'report',OUT/'static.json')
    raise SystemExit(0)

if args.merge_replacement:
    paths=[path.resolve() for path in args.merge_replacement]
    assert all(path.is_relative_to((ROOT/'tmp').resolve()) for path in paths)
    original,replacement=[json.loads(path.read_text(encoding='utf-8')) for path in paths]
    assert original['complete'] and replacement['complete'] and original['unchanged'] and replacement['unchanged']
    assert original['hashesBefore']==original['hashesAfter']==replacement['hashesBefore']==replacement['hashesAfter']
    assert len(original['rows'])==24 and len(replacement['rows'])==2
    key=lambda row:(row['kind'],row['profile']['name'],row['run'],row['candidate'])
    keys={key(row) for row in replacement['rows']}
    assert {row['candidate'] for row in replacement['rows']}=={'E','66'}
    assert len({(row['kind'],row['profile']['name'],row['run']) for row in replacement['rows']})==1
    assert all(row['kind']=='map' for row in replacement['rows'])
    excluded=[row for row in original['rows'] if key(row) in keys]
    assert len(excluded)==2
    rows=[row for row in original['rows'] if key(row) not in keys]+replacement['rows']
    rows.sort(key=lambda row:(row['kind'],row['profile']['name'],row['run'],row['candidate']))
    event_path=paths[0].parent/'INTERFERENCE.json'
    result={**original,'rows':rows,'summary':summary(rows),'acceptedSamples':24,
            'originalReport':{'path':str(paths[0]),'sha256':sha(paths[0].read_bytes())},
            'replacementReport':{'path':str(paths[1]),'sha256':sha(paths[1].read_bytes())},
            'excludedOriginalPair':[{'key':list(key(row)),'reason':'Paired replacement after reported ±5s HMR interference window'} for row in excluded],
            'interference':json.loads(event_path.read_text(encoding='utf-8-sig')) if event_path.exists() else None}
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'acceptedSamples':24,'replacedSamples':2,'summary':result['summary'],'results':str(OUT/'results.json')},ensure_ascii=False))
    raise SystemExit(0)

if args.floating_ab:FLOATING_FIXTURE=floating_fixture()
hashes={label:digest(folder) for label,folder in FOLDERS.items()}
feeds={label:json.loads((folder/'data/news.json').read_text(encoding='utf-8')) for label,folder in FOLDERS.items()}
news_slots={label:[{'id':item['id'],'text':item['text'],'image':item['image']} for item in feed['items'][:2]] for label,feed in feeds.items()}
plan={'profiles':PROFILES,'mapProfile':MAP_PROFILE,'samples':6 if args.floating_ab else 2 if args.map_run else 24,'replacementMapRun':args.map_run,'floatingAB':args.floating_ab,
      'floatingFixture':{k:v for k,v in FLOATING_FIXTURE.items() if k not in ['source','patched']} if FLOATING_FIXTURE else None,
      'urls':URLS,'folders':{k:str(v) for k,v in FOLDERS.items()},'hashesBefore':hashes,
      'sources':{k:json.loads((v.parent/'source.json').read_text(encoding='utf-8')) for k,v in FOLDERS.items()},
      'newsIds':{k:[x['id'] for x in v['items']] for k,v in feeds.items()},'firstTwoNewsPayloadsEqual':news_slots['E']==news_slots['66'],
      'conditions':'Cold Chrome contexts, light, DPR1, normal motion, cache disabled. Slow only: CPU4,150ms protocol latency,200000B/s down,93750B/s up. 8s cold + safe actions;12s actual about-to-map. Analytics refused; GitHub endpoint blocked equally to select own frozen local snapshot. Static local transport; no production TLS/compression equivalence.',
      'fieldData':False,'physicalDevice':False,'published':False}
(OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
if args.prepare_only:
    print(json.dumps({'prepared':str(OUT/'plan.json'),'samples':plan['samples'],'firstTwoNewsPayloadsEqual':plan['firstTwoNewsPayloadsEqual']},ensure_ascii=False))
    raise SystemExit(0)
rows=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--mute-audio'])
        try:
            plan['browser']=browser.version
            for profile in ([] if args.map_run or args.floating_ab else PROFILES):
                for run in range(1,4):
                    for label in (['E','66'] if run%2 else ['66','E']):
                        row=cold(browser,label,profile,run);rows.append(row)
                        (OUT/'results.json').write_text(json.dumps({**plan,'rows':rows,'summary':summary(rows)},ensure_ascii=False,indent=2),encoding='utf-8')
                        print(json.dumps({'kind':'cold','candidate':label,'profile':profile['name'],'run':run,'lcpMs':row.get('lcpMs'),'cls':row.get('cls'),'bodyBytes':row.get('completedNonVideoBodyBytes'),'failure':row.get('failure'),'ownFailures':len(row.get('ownFailures',[]))},ensure_ascii=False),flush=True)
            for run in ([args.map_run] if args.map_run else range(1,4)):
                for label in ((['off','on'] if run%2 else ['on','off']) if args.floating_ab else ['E','66'] if run%2 else ['66','E']):
                    if args.floating_ab:FLOATING_VARIANT=label
                    candidate='66' if args.floating_ab else label
                    row=map_sample(browser,candidate,run);rows.append(row)
                    (OUT/'results.json').write_text(json.dumps({**plan,'rows':rows,'summary':summary(rows)},ensure_ascii=False,indent=2),encoding='utf-8')
                    print(json.dumps({'kind':'map','candidate':label,'run':run,'callbackGapP95Ms':row.get('callbackGapP95Ms'),'provider':row.get('providerState'),'failure':row.get('failure'),'providerFailures':len(row.get('providerFailures',[]))},ensure_ascii=False),flush=True)
        finally:browser.close()
finally:
    after={label:digest(folder) for label,folder in FOLDERS.items()}
    final={**plan,'rows':rows,'summary':summary(rows),'hashesAfter':after,'unchanged':hashes==after,'complete':len(rows)==plan['samples']}
    (OUT/'results.json').write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
assert hashes==after,'Frozen input changed during measurement'
assert len(rows)==plan['samples'],len(rows)
print(json.dumps({'samples':len(rows),'unchanged':True,'summary':final['summary'],'results':str(OUT/'results.json')},ensure_ascii=False))
