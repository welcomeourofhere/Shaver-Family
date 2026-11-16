"""Paired desktop-drag samples; count actual style reads and preserve the held poses."""
import importlib.util
import json
from pathlib import Path
import statistics
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('regression',ROOT/'tests/device-regression.py')
regression=importlib.util.module_from_spec(spec);spec.loader.exec_module(regression)
folders={'baseline':ROOT/'tmp/baseline61-offers/dist','candidate':ROOT/'dist'}
before={key:regression.digest(folder)for key,folder in folders.items()}
servers={key:regression.serve(folder)for key,folder in folders.items()};rows=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='chrome')
  for run in range(3):
   for label in (['baseline','candidate']if run%2==0 else ['candidate','baseline']):
    context=browser.new_context(viewport={'width':1440,'height':1000})
    url=servers[label][1];context.route('**/*',lambda route:route.continue_()if route.request.url.startswith(url)or route.request.url.startswith('data:')else route.abort())
    context.add_init_script('window.rootReads=0;const original=window.getComputedStyle;window.getComputedStyle=function(e,...args){if(e===document.documentElement)rootReads++;return original.call(this,e,...args)}')
    page=context.new_page();page.goto(url);page.evaluate('document.fonts.ready');rail=page.locator('[data-of-rail]');rail.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");page.wait_for_timeout(700)
    cdp=context.new_cdp_session(page);cdp.send('Performance.enable');cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
    box=rail.bounding_box();x=min(1300,box['x']+box['width']-70);y=max(150,min(700,box['y']+210));page.mouse.move(x,y);page.mouse.down();page.evaluate('rootReads=0')
    first={m['name']:m['value']for m in cdp.send('Performance.getMetrics')['metrics']}
    for i in range(1,51):page.mouse.move(x-i*4,y)
    last={m['name']:m['value']for m in cdp.send('Performance.getMetrics')['metrics']}
    row={'label':label,'run':run+1,'rootReads':page.evaluate('rootReads'),'selected':page.locator('[data-offers]').get_attribute('data-offer-index'),'held':rail.evaluate("e=>e.classList.contains('is-dragging')"),'metrics':{key:last[key]-first[key]for key in ['ScriptDuration','RecalcStyleDuration','RecalcStyleCount','LayoutDuration','TaskDuration']},'poses':rail.locator('[data-offer-id]').evaluate_all("es=>es.map(e=>{const s=getComputedStyle(e),m=new DOMMatrix(s.transform);return{id:e.dataset.offerId,visible:s.visibility,pose:[m.m41,m.m42,m.m11,+s.opacity].map(n=>+n.toFixed(4))}})")}
    page.mouse.up();assert row['held'] and row['selected']=='0',row;rows.append(row);context.close();print(label,run+1,'rootReads',row['rootReads'],'styleSeconds',row['metrics']['RecalcStyleDuration'],flush=True)
  browser.close()
finally:
 for server,_ in servers.values():server.shutdown();server.server_close()
 after={key:regression.digest(folder)for key,folder in folders.items()}
 summary={label:{'rootReadsMedian':statistics.median(row['rootReads']for row in rows if row['label']==label),'metricMedians':{key:statistics.median(row['metrics'][key]for row in rows if row['label']==label)for key in ['ScriptDuration','RecalcStyleDuration','RecalcStyleCount','LayoutDuration','TaskDuration']}}for label in folders}if len(rows)==6 else{}
 out=ROOT/'artifacts/iteration61/offer-performance.json';out.write_text(json.dumps({'rows':rows,'summary':summary,'hashes':before,'unchanged':before==after,'conditions':'Chrome 1440x1000, CPU x4, 50 real mouse moves held over 200px; alternating paired runs, no parallel browser jobs','physicalDevice':False,'fieldData':False,'published':False},indent=2),encoding='utf-8')
assert before==after and len(rows)==6
for run in range(1,4):
 baseline=next(row for row in rows if row['label']=='baseline'and row['run']==run);candidate=next(row for row in rows if row['label']=='candidate'and row['run']==run)
 assert baseline['poses']==candidate['poses'],'the approved held artwork must stay identical'
 assert baseline['rootReads']>1000 and candidate['rootReads']<20
print('PASS paired held poses unchanged; root style reads reduced',summary)
