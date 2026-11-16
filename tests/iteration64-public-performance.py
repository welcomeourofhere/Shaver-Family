"""Cold public delivery and real analytics transport, without submitting bookings."""
import importlib.util,json,statistics
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tmp/planning/iteration64'
spec=importlib.util.spec_from_file_location('performance',ROOT/'tests/device-performance.py');perf=importlib.util.module_from_spec(spec);spec.loader.exec_module(perf)
rows=[];receipts=[]
with sync_playwright()as p:
 browser=p.chromium.launch(channel='chrome')
 for phone,slow in [(True,False),(True,True),(False,False)]:
  for run in range(3):
   context=browser.new_context(viewport={'width':390 if phone else 1440,'height':844 if phone else 900},is_mobile=phone,has_touch=phone);context.add_init_script(perf.INIT);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   cdp=context.new_cdp_session(page);cdp.send('Network.enable');cdp.send('Network.setCacheDisabled',{'cacheDisabled':True})
   if slow:
    cdp.send('Emulation.setCPUThrottlingRate',{'rate':4});cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':200000,'uploadThroughput':93750,'connectionType':'cellular4g'})
   if slow and run==0:cdp.send('Tracing.start',{'categories':'devtools.timeline,blink.user_timing','transferMode':'ReturnAsStream'})
   response=page.goto('https://soyuz.hair/',wait_until='domcontentloaded');page.wait_for_timeout(8000)
   row=page.evaluate("()=>({lab,resources:performance.getEntriesByType('resource').map(e=>({path:new URL(e.name).pathname,host:new URL(e.name).hostname,start:e.startTime,end:e.responseEnd,bytes:e.encodedBodySize})),navigation:performance.getEntriesByType('navigation').map(e=>({ttfb:e.responseStart,dom:e.domContentLoadedEventEnd,bytes:e.encodedBodySize})),fonts:document.fonts.status})")
   row.update(phone=phone,slow=slow,run=run+1,status=response.status,scriptErrors=errors);assert response.status==200 and not errors
   if slow and run==0:
    complete=[];cdp.on('Tracing.tracingComplete',lambda e:complete.append(e));cdp.send('Tracing.end');page.wait_for_timeout(100)
    while not complete:page.wait_for_timeout(50)
    chunks=[]
    while True:
     chunk=cdp.send('IO.read',{'handle':complete[0]['stream']});chunks.append(chunk['data'])
     if chunk['eof']:break
    cdp.send('IO.close',{'handle':complete[0]['stream']});(OUT/'public-slow-trace.json').write_text(''.join(chunks),encoding='utf-8')
   rows.append(row);print('PUBLIC',phone,slow,run+1,'LCP',row['lab']['lcp'][-1]['time']if row['lab']['lcp']else None,'CLS',sum(v['value']for v in row['lab']['shift']if not v['input']),flush=True);context.close()
 # New anonymous QA context. Only transport status/event names are retained.
 context=browser.new_context(viewport={'width':1440,'height':900});context.route('https://*.yclients.ru/**',lambda route:route.abort());page=context.new_page()
 def received(response):
  u=urlsplit(response.url);q=parse_qs(u.query)
  if 'google-analytics.com'in u.hostname and'/collect'in u.path:receipts.append({'vendor':'ga4','status':response.status,'event':q.get('en',[''])[0],'measurement':q.get('tid',[''])[0]})
  elif u.hostname and u.hostname.startswith('mc.yandex.')and'/watch/114263185'in u.path:receipts.append({'vendor':'metrika','status':response.status,'goal':q.get('page-url',[''])[0].split('/')[-1]if q.get('page-url',[''])[0].startswith('goal:')else'pageview'})
 page.on('response',received);page.goto('https://soyuz.hair/',wait_until='domcontentloaded');page.locator('[data-analytics-choice=granted]').click();page.wait_for_timeout(3500);page.locator('.header-book').click();page.wait_for_timeout(1500);page.keyboard.press('Escape');page.wait_for_timeout(500)
 with context.expect_page()as popup:page.locator('.certificate-buy').click()
 popup.value.close();page.wait_for_timeout(5000)
 scripts=page.evaluate("()=>[...document.scripts].filter(x=>x.id==='soyuz-ga4'||x.id==='soyuz-metrika').map(x=>x.id)");assert len(scripts)==2
 context.close();browser.close()
summary=[{'phone':phone,'slow':slow,'samples':3,'lcpMedianMs':statistics.median(r['lab']['lcp'][-1]['time']for r in rows if r['phone']==phone and r['slow']==slow),'clsMax':max(sum(v['value']for v in r['lab']['shift']if not v['input'])for r in rows if r['phone']==phone and r['slow']==slow)}for phone,slow in [(True,False),(True,True),(False,False)]]
(OUT/'public-performance.json').write_text(json.dumps({'rows':rows,'summary':summary,'analyticsReceipts':receipts,'fieldData':False,'physicalDevice':False,'bookingSubmitted':False,'purchaseSubmitted':False},indent=2),encoding='utf-8');print(json.dumps({'summary':summary,'analyticsReceipts':receipts}),flush=True)
